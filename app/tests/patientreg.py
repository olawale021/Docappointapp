import unittest
from unittest.mock import patch

from bson import ObjectId
from werkzeug.security import generate_password_hash

from app import app
from flask import url_for, json


class DoctorRegistrationTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        app.config['WTF_CSRF_ENABLED'] = False

    def test_patient_login_approved(self):
        with patch('app.mongo.db.patients.find_one') as mock_find_one:
            # Mock the database response for an approved patient
            mock_find_one.return_value = {
                '_id': ObjectId('65fd6c5a0d6fbf0263c56072'),
                'phone_number': '0798765563',
                'password': generate_password_hash('correct_password'),
                'registration_status': 'approved'
            }

            response = self.client.post('/patient_login', data={
                'phone_number': '0798765563',
                'password': 'correct_password'
            }, follow_redirects=True)

            # Assert the redirection to the patient dashboard
            self.assertEqual(response.status_code, 200)

    def test_patient_registration_username_too_short(self):
        """Ensure that short usernames are rejected."""
        response = self.client.post('/patient_registration', json={
            # Include all required fields but make username too short
            'username': 'user',  # Intentionally too short
            'first_name': 'Test',
            'last_name': 'User',
            'date_of_birth': '1990-01-01',
            'gender': 'Other',
            'phone_number': '1234567890',
            'password': 'securePassword123!',
            'address': '123 Test St.'
        })
        assert response.status_code == 400
        assert b"Username must be at least 5 characters long" in response.data

    def test_patient_registration_missing_fields(self):
        """Ensure that missing fields are correctly identified."""
        response = self.client.post('/patient_registration', json={
            # Omitting required fields to trigger validation
            'username': 'testuser'
        })
        assert response.status_code == 400
        assert b"Missing fields" in response.data

    def test_patient_registration_get(self):
        # Test the GET request to the patient registration route
        response = self.client.get('/patient_registration')
        assert response.status_code == 200
        # Adjust this assertion based on the actual content of your registration form
        assert b'Patient Register' in response.data

    def test_patient_login_wrong_password(self):
        with patch('app.mongo.db.patients.find_one') as mock_find_one:
            # Mock the database response for a patient with a specific password hash
            mock_find_one.return_value = {
                '_id': ObjectId('65fd6c5a0d6fbf0263c56072'),
                'phone_number': '0798765563',
                'password': generate_password_hash('correct_password'),
                'registration_status': 'approved'
            }

            # Attempt to login with the wrong password
            response = self.client.post('/patient_login', data={
                'phone_number': '0798765563',
                'password': 'wrong_password'
            })

            # Assert that login fails due to incorrect password
            self.assertIn(b'Invalid phone number or password.', response.data)


