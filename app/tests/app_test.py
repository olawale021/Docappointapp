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




















