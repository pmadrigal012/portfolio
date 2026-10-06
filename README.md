# RentalOps

A maintenance coordination assistant for short-term and long-term rental properties, inspired by a property owner's workflow in Costa Rica: receive a tenant's report, find an available service provider, coordinate access, and verify the repair.

## Business problem

Maintenance coordination is scattered across WhatsApp conversations. Owners need to know which repairs are unresolved, who has been contacted, and whose confirmation is pending. RentalOps brings that follow-up into one place and builds a reusable provider directory.

## Run locally

Requires Python 3.12. From this repository's directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

Open the address Streamlit prints on your computer. Press Ctrl+C to stop the app.

## Try the workflow

1. In **Service providers**, add a fictional contact with the **Roofing and gutters** specialty.
2. In **Maintenance requests**, report a leak at a demo property.
3. In **Details and follow-up**, record the contacts you approached and their replies in follow-up notes.
4. Assign a provider and record a visit time confirmed with the tenant.
5. Record the cost and repair verification, then change the status to **Closed**.

The WhatsApp button opens a draft for you to review and send manually. It does not confirm delivery or receive replies. Use your own or fictional numbers when testing.

## Code structure

- `app.py`: Streamlit screens, forms, and WhatsApp links.
- `storage.py`: parameterized SQL queries and SQLite transactions.
- `data/rentals.db`: local records, excluded from Git. Set `RENTAL_DB_PATH` to use another location.
- `tests/test_workflow.py`: persistence, validation, and interface workflow tests.

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Records survive restarts if the SQLite file is retained. Note timestamps use UTC; visit times are free-form text agreed by the people involved. Existing Spanish category and status labels are migrated automatically; user-written descriptions and notes are preserved.

## Current scope

The prototype records requests, contacts, notes, visits, and costs. It does not store videos, interpret reports with AI, receive WhatsApp messages, or automate notifications. Dashboard counters reflect recorded state rather than automated monitoring.

This local prototype has no authentication. Use fictional data for demonstrations. Hosting real records requires access control, persistent storage, data protection, and backups. Temporary hosting disks can lose the database. Public deployment and operational monitoring are not implemented yet.

## Roadmap

1. Validate an end-to-end maintenance case with the property owner.
2. Deploy a demonstration using fictional data.
3. Add operational metrics and alerts.
4. Integrate the official WhatsApp API.
5. Evaluate AI-assisted extraction of structured maintenance requests.

The portfolio will document the problem, implementation decisions, deployment, and measured outcomes as those stages are completed.
