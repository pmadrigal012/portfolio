"""Local storage for maintenance requests and service providers."""
import os
import sqlite3
from pathlib import Path

STATUSES = ['Find a provider', 'Awaiting response', 'Schedule a visit', 'Repair in progress', 'Verify repair', 'Closed']

def connect():
    path = Path(os.environ.get('RENTAL_DB_PATH', 'data/rentals.db'))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db

def initialize():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS providers (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, specialty TEXT NOT NULL,
          zone TEXT NOT NULL, phone TEXT NOT NULL, notes TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS incidents (
          id INTEGER PRIMARY KEY, property TEXT NOT NULL, rental_type TEXT NOT NULL,
          description TEXT NOT NULL, specialty TEXT NOT NULL, priority TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'Find a provider', provider_id INTEGER,
          visit TEXT NOT NULL DEFAULT '', cost REAL);
        CREATE TABLE IF NOT EXISTS updates (
          id INTEGER PRIMARY KEY, incident_id INTEGER NOT NULL,
          note TEXT NOT NULL, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        ''')
        columns = {row['name'] for row in db.execute('PRAGMA table_info(incidents)')}
        if 'last_activity' not in columns:
            db.execute('ALTER TABLE incidents ADD COLUMN last_activity TEXT')
            # Recover known history dates without inventing dates for older requests.
            db.execute('UPDATE incidents SET last_activity=(SELECT MAX(created) FROM updates WHERE incident_id=incidents.id)')
        # Idempotently migrate structured labels from the original Spanish prototype.
        legacy_labels = {'Fontanería / goteras': 'Plumbing / leaks', 'Electricidad': 'Electrical', 'Techos y canoas': 'Roofing and gutters', 'Limpieza': 'Cleaning', 'Cerrajería': 'Locksmith', 'General / por definir': 'General / to be determined', 'Buscar proveedor': 'Find a provider', 'Esperar respuesta': 'Awaiting response', 'Coordinar visita': 'Schedule a visit', 'Reparación en curso': 'Repair in progress', 'Verificar reparación': 'Verify repair', 'Cerrado': 'Closed', 'Corta estancia': 'Short-term', 'Larga estancia': 'Long-term', 'Alta': 'High', 'Urgente': 'Urgent'}
        for old, new in legacy_labels.items():
            for column in ('status', 'specialty', 'rental_type', 'priority'):
                db.execute(f'UPDATE incidents SET {column}=? WHERE {column}=?', (new, old))
            db.execute('UPDATE providers SET specialty=? WHERE specialty=?', (new, old))

def rows(sql, args=()):
    with connect() as db:
        return [dict(row) for row in db.execute(sql, args).fetchall()]

def add_provider(name, specialty, zone, phone, notes):
    with connect() as db:
        db.execute('INSERT INTO providers (name,specialty,zone,phone,notes) VALUES (?,?,?,?,?)', (name,specialty,zone,phone,notes))

def add_incident(property_name, rental_type, description, specialty, priority):
    with connect() as db:
        db.execute('INSERT INTO incidents (property,rental_type,description,specialty,priority,last_activity) VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)', (property_name,rental_type,description,specialty,priority))

def save_incident(id, status, provider_id, visit, cost, note):
    if status not in STATUSES or (cost is not None and cost < 0):
        raise ValueError('Invalid status or cost')
    with connect() as db:
        # Read and write under one transaction so the history matches the saved change.
        db.execute('BEGIN IMMEDIATE')
        previous = db.execute('SELECT status,provider_id,visit,cost FROM incidents WHERE id=?', (id,)).fetchone()
        if previous is None:
            raise ValueError('Maintenance request not found')
        events = []
        if previous['status'] != status:
            events.append(f"Status changed from {previous['status']} to {status}.")
        if previous['provider_id'] != provider_id:
            def provider_name(provider):
                if provider is None:
                    return 'Unassigned'
                row = db.execute('SELECT name FROM providers WHERE id=?', (provider,)).fetchone()
                if row is None:
                    raise ValueError('Service provider not found')
                return f"{row['name']} (#{provider})"
            events.append(f"Provider changed from {provider_name(previous['provider_id'])} to {provider_name(provider_id)}.")
        db.execute('UPDATE incidents SET status=?,provider_id=?,visit=?,cost=? WHERE id=?', (status,provider_id,visit,cost,id))
        if note.strip() or any(previous[field] != value for field, value in (
            ('status', status), ('provider_id', provider_id), ('visit', visit), ('cost', cost)
        )):
            db.execute('UPDATE incidents SET last_activity=CURRENT_TIMESTAMP WHERE id=?', (id,))
        for event in events:
            db.execute('INSERT INTO updates (incident_id,note) VALUES (?,?)', (id,event))
        if note.strip():
            db.execute('INSERT INTO updates (incident_id,note) VALUES (?,?)', (id,note.strip()))
