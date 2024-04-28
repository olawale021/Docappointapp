import unittest
from app import app
from flask import url_for, session
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId
from flask_wtf.csrf import generate_csrf


class TestAppointment(unittest.TestCase):
    def setUp(self):
        # Configure the Flask test client
        self.client = app.test_client()
        self.client.testing = True
        app.config['SERVER_NAME'] = 'localhost.localdomain'
        app.config['WTF_CSRF_ENABLED'] = False

        # Use actual ObjectId values or mocks as necessary
        self.appointment_id = ObjectId('660d37e76a03fcb618df8084')  # Replace with a suitable test id
        self.doctor_id = ObjectId('66003d1f0cfcff3c4b8a0356')      # Replace with a suitable test id

    @patch('app.mongo.db.appointments.update_one')
    @patch('app.mongo.db.doctors.find_one')
    def test_accept_appointment_no_login(self, mock_find_one, mock_update_one):
        # Setup the mock for find_one to simulate doctor not being found
        mock_find_one.return_value = None

        # Ensure that session manipulation and request are done within the application context
        with app.app_context():
            with self.client.session_transaction() as sess:
                # Ensure the session does not have a logged-in doctor
                sess.pop('doctor_id', None)

            # Now that we're within the application context, perform the POST request
            response = self.client.post(url_for('accept_appointment', appointment_id=str(self.appointment_id)))

            # Check the response for the expected redirect
            self.assertEqual(response.status_code, 302)
            # Ensure that the response redirects to the doctor login page
            self.assertIn('/doctor_login', response.headers['Location'])

    @patch('app.mongo.db.appointments.update_one')
    @patch('app.mongo.db.doctors.find_one')
    def test_accept_appointment_success(self, mock_find_one, mock_update_one):
        # Start the application context
        with app.app_context():
            # Simulate a logged-in doctor within the session
            with self.client.session_transaction() as sess:
                sess['doctor_id'] = str(self.doctor_id)

            # Setup the mock database responses
            mock_find_one.return_value = {'_id': self.doctor_id}
            mock_update_one.return_value = MagicMock(acknowledged=True)

            # Perform the POST request within the same application context
            response = self.client.post(url_for('accept_appointment', appointment_id=str(self.appointment_id)))

            # Verify the response
            self.assertEqual(response.status_code, 302)  # Expecting a redirect
            self.assertTrue('/doctor_dashboard' in response.headers['Location'])

