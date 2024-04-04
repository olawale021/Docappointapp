import unittest
from unittest.mock import patch, MagicMock
from app import app
from bson.objectid import ObjectId
from datetime import datetime, timedelta


class CreateAppointmentTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        app.config['SERVER_NAME'] = 'localhost.localdomain'
        app.config['WTF_CSRF_ENABLED'] = False
        self.patient_id = str(ObjectId('660d31266a03fcb618df8081'))
        self.doctor_id = str(ObjectId('66003d1f0cfcff3c4b8a0356'))
        self.future_date = '2024-04-27'
        self.time = '09:00 - 09:30'

    @patch('app.mongo.db.appointments.insert_one')
    @patch('app.utils.is_doctor_available', return_value=True)
    @patch('app.utils.validate_appointment_date', return_value=True)
    def test_create_appointment_success(self, mock_validate, mock_available, mock_insert):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['patient_id'] = self.patient_id
            response = c.post('/create_appointment', data={
                'doctor_id': self.doctor_id,
                'date': self.future_date,
                'time': self.time
            }, follow_redirects=True)
            self.assertIn(b'Your Appointment Booked Successfully', response.data)
