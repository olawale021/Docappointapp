from unittest.mock import patch
import pytest
from bson import ObjectId
from flask import url_for

from app import app as flask_app
from werkzeug.security import generate_password_hash
from flask import session


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF tokens for the tests

    with flask_app.test_client() as client:
        yield client  # This provides a client for your test functions to use

def test_home_route(client):
  # Mock the doctors collection to avoid interacting with a real database
  with patch('app.mongo.db.doctors.find') as mock_find:
    mock_find.return_value = [
      {"username": "Dr. Linda HayWood", "registration_status": "approved"},
      {"username": "Dr. Charles Washington", "registration_status": "approved"},
    ]

    # Make a GET request to the home route
    response = client.get('/')
    # print(response.data)

    # Assert the response status code
    assert response.status_code == 200

    # Assert the template is rendered with the correct context
    assert b'Dr. Linda HayWood' in response.data
    assert b'Dr. Charles Washington' in response.data


def test_admin_login_missing_username(client):
    """Test /admin_login endpoint with missing username."""
    response = client.post('/admin_login', data={'password': 'testPassword'}, follow_redirects=True)
    assert b'Username is required.' in response.data


def test_patient_registration_missing_fields(client):
    """Ensure that missing fields are correctly identified."""
    response = client.post('/patient_registration', json={
        # Omitting required fields to trigger validation
        'username': 'testuser'
    })
    assert response.status_code == 400
    print(response.data)
    assert b"Missing fields" in response.data


def test_patient_registration_username_too_short(client):
    """Ensure that short usernames are rejected."""
    response = client.post('/patient_registration', json={
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


def test_doctor_registration_missing_field(client):
    """Ensure the endpoint correctly handles missing required fields."""
    data = {
        # Omitting 'username' to simulate missing required field
        'first_name': 'John',
        'last_name': 'Doe',
        'date_of_birth': '1980-01-01',
        'gender': 'Male',
        'phone_number': '12345678901',
        'password': 'strongpassword',
        'hospital': 'General Hospital',
        'specialty': 'Cardiology'
    }
    response = client.post('/doctor_registration', json=data)
    assert response.status_code == 400
    assert b"Missing or empty required fields" in response.data


def test_doctor_registration_invalid_phone_number_length(client):
    """Ensure the endpoint validates the phone number length correctly."""
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
    response = client.post('/doctor_registration', json=data)
    assert response.status_code == 400
    assert b"Phone number must be exactly 11 digits" in response.data


def test_patient_login_approved(client):
    with patch('app.mongo.db.patients.find_one') as mock_find_one:
        # Mock the database response for an approved patient
        mock_find_one.return_value = {
            '_id': ObjectId('65fd6c5a0d6fbf0263c56072'),
            'phone_number': '0798765563',
            'password': generate_password_hash('correct_password'),
            'registration_status': 'approved'
        }

        response = client.post('/patient_login', data={
            'phone_number': '0798765563',
            'password': 'correct_password'
        }, follow_redirects=True)

        # Assert the redirection to the patient dashboard
        assert response.request.path == url_for('patient_login')
        print(response.data)


@patch('app.mongo.db.doctors.find_one')
def test_doctor_login_success(mock_find_one, client):
    mock_find_one.return_value = {
        '_id': ObjectId('66003d720cfcff3c4b8a0357'),
        'phone_number': '07476537524',
        'password': generate_password_hash('validpassword')
    }

    response = client.post('/doctor_login', data={
        'phone_number': '07476537524',
        'password': 'validpassword'
    }, follow_redirects=True)

    # Check for redirect to doctor_dashboard
    assert response.request.path == url_for('doctor_login')


@patch('app.mongo.db.doctors.find_one')
@patch('app.get_appointment_requests_for_doctor')
@patch('app.get_fixed_appointments_for_doctor')
def test_doctor_dashboard_access(mock_get_fixed_appointments, mock_get_appointment_requests, mock_find_one, client):
    # Setup mock data for doctor and appointments
    doctor_id = '66003d720cfcff3c4b8a0357'
    mock_doctor = {
        '_id': ObjectId(doctor_id),
        'phone_number': '07476537524',
        'password': generate_password_hash('validpassword'),
    }
    mock_appointment_requests = [{
        'date': '2023-10-01',
        'patient_info': {'first_name': 'John', 'last_name': 'Smith'}
    }]
    mock_fixed_appointments = [{
        'date': '2023-10-02',
        'patient_info': {'first_name': 'Jane', 'last_name': 'Doe'}
    }]

    # Mock database responses
    mock_find_one.return_value = mock_doctor
    mock_get_appointment_requests.return_value = mock_appointment_requests
    mock_get_fixed_appointments.return_value = mock_fixed_appointments

    with client.session_transaction() as sess:
        sess['doctor_id'] = doctor_id

    response = client.get('/doctor_dashboard')

    assert response.status_code == 200
    assert b'Dr. Jane Doe' in response.data
    assert b'John Smith' in response.data
    assert b'Jane Doe' in response.data
    assert b'01 October 2023' in response.data
    assert b'02 October 2023' in response.data












