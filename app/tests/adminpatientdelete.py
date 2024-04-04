import unittest
from app import app  # Make sure this correctly imports your Flask application
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId


class DeletePatientTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

        self.patient_id = ObjectId('660e7dfe51ae3b370ec6a09a')

    @patch('app.mongo.db.patients.delete_one')
    def test_delete_patient_success(self, mock_delete):
        # Configure the mock to simulate a successful deletion
        mock_delete.return_value.deleted_count = 1

        # Make a POST request to the delete patient endpoint
        response = self.client.post(f'/admin/patients/delete/{self.patient_id}')

        # Check that the response contains the expected success message
        self.assertIn(b'Your operation was completed successfully.', response.data)
        self.assertEqual(response.status_code, 200)



