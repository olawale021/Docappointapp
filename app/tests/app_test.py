from unittest.mock import patch
import pytest
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF tokens for the tests
    # Any other configuration for testing can be set here

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


