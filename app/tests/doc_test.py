import unittest
from unittest.mock import patch

from bson import ObjectId
from werkzeug.security import generate_password_hash

from app import app  # Ensure this correctly imports your Flask app
from flask import url_for, json


class DoctorRegistrationTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        app.config['WTF_CSRF_ENABLED'] = False  # add assertion here

    def test_register_doctor_missing_fields(self):
        with self.client:
            response = self.client.post('/doctor_registration', data=json.dumps({}), content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertIn("Missing or empty required fields", response.json['error'])

    def test_register_doctor_invalid_phone_number(self):
        doctor_data = {
            'username': 'jdoe', 'first_name': 'John', 'last_name': 'Doe', 'date_of_birth': '1980-01-01',
            'gender': 'male', 'phone_number': '123', 'password': 'password123',
            'hospital': 'General Hospital', 'specialty': 'Cardiology'
        }
        with self.client:
            response = self.client.post('/doctor_registration', data=json.dumps(doctor_data), content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertIn("Phone number must be exactly 11 digits", response.json['error'])

    def test_doctor_registration_invalid_phone_number_length(self):
        data = {
            'username': 'johndoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1980-01-01',
            'gender': 'Male',
            'phone_number': '123456789',  # Intentionally incorrect length
            'password': 'strongpassword',
            'hospital': 'General Hospital',
            'specialty': 'Cardiology'
        }
        response = self.client.post('/doctor_registration', json=data)
        assert response.status_code == 400
        assert b"Phone number must be exactly 11 digits" in response.data

    @patch('app.mongo.db.doctors.find_one')
    def test_doctor_login_success(self, mock_find_one):
        mock_find_one.return_value = {
            '_id': ObjectId('65fd6c5a0d6fbf0263c56072'),
            'phone_number': '0798765563',
            'password': generate_password_hash('validpassword')
        }

        response = self.client.post('/doctor_login', data={
            'phone_number': '0798765563',
            'password': 'validpassword'
        }, follow_redirects=True)

        # Check for redirect to doctor_dashboard
        self.assertEqual(response.status_code, 200)

    @patch('app.mongo.db.doctors.find_one')
    @patch('app.utils.get_appointment_requests_for_doctor')
    @patch('app.utils.get_fixed_appointments_for_doctor')
    def test_doctor_dashboard_access(self, mock_get_fixed_appointments, mock_get_appointment_requests, mock_find_one):
        # Setup mock data for doctor and appointments
        doctor_id = '66003d720cfcff3c4b8a0357'
        mock_doctor = {
            '_id': ObjectId(doctor_id),
            'phone_number': '0798765563',
            'password': generate_password_hash('validpassword'),
        }
        mock_appointment_requests = [{
            'date': '2024-04-20',
            'patient_info': {'first_name': 'John', 'last_name': 'Smith'}
        }]
        mock_fixed_appointments = [{
            'date': '2024-04-06',
            'patient_info': {'first_name': 'Alex', 'last_name': 'Brett'}
        }]

        # Mock database responses
        mock_find_one.return_value = mock_doctor
        mock_get_appointment_requests.return_value = mock_appointment_requests
        mock_get_fixed_appointments.return_value = mock_fixed_appointments

        with self.client.session_transaction() as sess:
            sess['doctor_id'] = doctor_id

        response = self.client.get('/doctor_dashboard')

        assert response.status_code == 200

