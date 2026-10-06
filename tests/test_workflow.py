import os
import tempfile
import unittest
from unittest.mock import patch
import storage

class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'RENTAL_DB_PATH':self.temp.name+'/test.db'})
        self.env.start()
        storage.initialize()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_repair_persists(self):
        storage.add_provider('Ana','Roofing and gutters','San José','50612345678','Test')
        storage.add_incident('Demo property','Long-term','Leak','Roofing and gutters','High')
        p = storage.rows('SELECT * FROM providers')[0]
        i = storage.rows('SELECT * FROM incidents')[0]
        storage.save_incident(i['id'],'Schedule a visit',p['id'],'Tuesday 9:00 AM',None,'Accepted')
        storage.save_incident(i['id'],'Closed',p['id'],'Tuesday 9:00 AM',25000,'Repair verified')
        storage.initialize()
        saved = storage.rows('SELECT * FROM incidents')[0]
        self.assertEqual(saved['status'],'Closed')
        self.assertEqual(saved['provider_id'],p['id'])
        self.assertEqual(saved['cost'],25000)
        self.assertEqual(len(storage.rows('SELECT * FROM updates')),2)

    def test_invalid_updates(self):
        with self.assertRaises(ValueError):
            storage.save_incident(1,'Invalid',None,'',None,'')
        with self.assertRaises(ValueError):
            storage.save_incident(1,'Closed',None,'',-1,'')

    def test_existing_labels_migrate_without_changing_user_content(self):
        storage.add_provider('Ana', 'Techos y canoas', 'San José', '50612345678', 'Contacto habitual')
        storage.add_incident('Mi casa', 'Larga estancia', 'Gotera en el cuarto', 'Techos y canoas', 'Alta')
        with storage.connect() as db:
            db.execute("UPDATE incidents SET status='Coordinar visita'")
        storage.initialize()
        storage.initialize()
        item = storage.rows('SELECT * FROM incidents')[0]
        self.assertEqual(item['status'], 'Schedule a visit')
        self.assertEqual(item['rental_type'], 'Long-term')
        self.assertEqual(item['specialty'], 'Roofing and gutters')
        self.assertEqual(item['priority'], 'High')
        self.assertEqual(item['description'], 'Gotera en el cuarto')
        self.assertEqual(storage.rows('SELECT * FROM providers')[0]['notes'], 'Contacto habitual')

    def test_interface_flow(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file('app.py').run()
        self.assertEqual(len(app.exception),0)
        app.text_input[0].set_value('Demo property')
        app.text_area[0].set_value('Leak in the bedroom')
        app.button[0].click().run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,'1')
        app.sidebar.radio[0].set_value('Service providers').run()
        app.text_input[0].set_value('Ana')
        app.text_input[1].set_value('San José')
        app.text_input[2].set_value('50612345678')
        app.button[0].click().run()
        self.assertEqual(len(app.exception),0)
        app.sidebar.radio[0].set_value('Details and follow-up').run()
        self.assertEqual(len(app.exception),0)
        app.selectbox[1].set_value('Closed')
        app.text_area[0].set_value('Repair verified')
        app.button[0].click().run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(storage.rows('SELECT * FROM incidents')[0]['status'],'Closed')

    def test_close_button_saves_form_and_updates_dashboard(self):
        from streamlit.testing.v1 import AppTest
        storage.add_incident('Demo property', 'Long-term', 'Leak', 'Roofing and gutters', 'High')
        app = AppTest.from_file('app.py').run()
        app.sidebar.radio[0].set_value('Details and follow-up').run()
        app.text_area[0].set_value('Tenant confirmed the leak is fixed.')
        app.checkbox[0].check()
        app.number_input[0].set_value(25000)
        next(b for b in app.button if b.label == 'Close repair').click().run()
        self.assertEqual(len(app.exception), 0)
        saved = storage.rows('SELECT * FROM incidents')[0]
        self.assertEqual(saved['status'], 'Closed')
        self.assertEqual(saved['cost'], 25000)
        self.assertIn('Tenant confirmed', storage.rows('SELECT * FROM updates')[0]['note'])
        self.assertTrue(next(b for b in app.button if b.label == 'Close repair').disabled)
        self.assertEqual(app.success[0].value, 'This repair is closed.')
        app.sidebar.radio[0].set_value('Maintenance requests').run()
        self.assertEqual(app.metric[0].value, '0')

if __name__ == '__main__':
    unittest.main()
