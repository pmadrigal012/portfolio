import unittest
from unittest.mock import patch, Mock
from streamlit.testing.v1 import AppTest
import access


class User(dict):
    is_logged_in = True


class AccessTest(unittest.TestCase):
    def test_requires_verified_allowlisted_identity(self):
        user = User(email='Owner@example.com', email_verified=True)
        self.assertTrue(access.is_allowed(user, ['owner@example.com']))
        self.assertFalse(access.is_allowed(user, ['someone@example.com']))
        user['email_verified'] = False
        self.assertFalse(access.is_allowed(user, ['owner@example.com']))
        user['email_verified'] = 'true'
        self.assertFalse(access.is_allowed(user, ['owner@example.com']))
        user['email_verified'] = True
        user.is_logged_in = False
        self.assertFalse(access.is_allowed(user, ['owner@example.com']))

    def test_missing_configuration_blocks_database_access(self):
        with patch('storage.initialize') as initialize, patch('storage.rows') as rows:
            app = AppTest.from_file('app.py').run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn('Private access is not configured', app.warning[0].value)
            initialize.assert_not_called()
            rows.assert_not_called()

    def test_gate_handles_anonymous_denied_and_approved_users(self):
        config = {'allowed_emails': ['owner@example.com'], 'auth': {
            'redirect_uri': 'https://example.com/oauth2callback', 'cookie_secret': 'test-only',
            'client_id': 'test-only', 'client_secret': 'test-only',
            'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration'}}
        class Stopped(Exception):
            pass
        for logged_in, email, approved in [(False, '', False), (True, 'other@example.com', False), (True, 'owner@example.com', True)]:
            with self.subTest(logged_in=logged_in, email=email):
                fake = Mock()
                fake.secrets = config
                fake.user = User(email=email, email_verified=True)
                fake.user.is_logged_in = logged_in
                fake.button.return_value = False
                fake.sidebar.button.return_value = False
                fake.stop.side_effect = Stopped
                with patch.object(access, 'st', fake):
                    if approved:
                        access.require_access()
                        fake.stop.assert_not_called()
                    else:
                        with self.assertRaises(Stopped):
                            access.require_access()
