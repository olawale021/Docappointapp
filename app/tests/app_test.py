import unittest
from unittest.mock import patch, MagicMock
from flask import template_rendered
from app import app  # Adjust this to your application's structure
from bson.objectid import ObjectId
import cloudinary.uploader


class DoctorProfileSettingsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        app.config['WTF_CSRF_ENABLED'] = False

    @patch('app.mongo.db.doctors.find_one')
    def test_doctor_profile_settings_get_not_logged_in(self, mock_find_one):
        # Mock the session to not contain a doctor_id
        with self.app as client:
            response = client.get('/doctor_profile_settings')
            self.assertEqual(response.status_code, 302)
            self.assertTrue('/doctor_login' in response.headers['Location'])

    @patch('app.mongo.db.doctors.find_one')
    def test_doctor_profile_settings_get_success(self, mock_find_one):
        # Setup the mock return value
        mock_find_one.return_value = {'_id': ObjectId('66003d720cfcff3c4b8a0357')}
        with self.app as client:
            with client.session_transaction() as sess:
                sess['doctor_id'] = str(ObjectId('66003d720cfcff3c4b8a0357'))
            response = client.get('/doctor_profile_settings')
            self.assertEqual(response.status_code, 200)

    @patch('cloudinary.uploader.upload')
    @patch('app.mongo.db.doctors.update_one')
    @patch('app.mongo.db.doctors.find_one')
    def test_doctor_profile_settings_post_success(self, mock_find_one, mock_update_one, mock_cloudinary_upload):
        # Mock database find_one return value and cloudinary upload
        mock_find_one.return_value = {'_id': ObjectId('66003d720cfcff3c4b8a0357')}
        mock_update_one.return_value = None  # Assuming successful update
        mock_cloudinary_upload.return_value = {'secure_url': 'https://example.com/test.jpg'}

        with self.app as client:
            with client.session_transaction() as sess:
                sess['doctor_id'] = str(ObjectId('66003d720cfcff3c4b8a0357'))
            data = {
                'first_name': 'John',
                'last_name': 'Doe',
                # Add other form fields as necessary
            }
            response = client.post('/doctor_profile_settings', data=data, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 302)
            self.assertTrue('/doctor_dashboard' in response.headers['Location'])
