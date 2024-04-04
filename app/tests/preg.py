import pytest
from flask import url_for, template_rendered
from contextlib import contextmanager
from app import app as flask_app

from unittest.mock import patch
from unittest.mock import patch, ANY
from werkzeug.security import generate_password_hash
from app.models import Admin
from app.routes import admin_login  # Adjust import based on your project structure
from flask import request


@pytest.fixture
def client():
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key",
        "WTF_CSRF_ENABLED": False,
    })
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client


# Use this context manager to simulate login_user behavior if needed
from contextlib import contextmanager
from flask_login import current_user


@contextmanager
def user_logged_in(user):
    def is_authenticated():
        return True
    original_is_authenticated = user.is_authenticated
    user.is_authenticated = is_authenticated
    current_user._get_current_object = lambda: user
    yield
    user.is_authenticated = original_is_authenticated





@patch('app.routes.mongo.db.admins.find_one')
def test_admin_login_find_one_called(mock_find_one, client):
    # Setup test data
    test_username = 'admin0121'
    test_password = 'Ray@1122'
    print("Sending POST request with:", test_username, test_password)
    mock_find_one.return_value = {
        'username': 'admin0121',
        'password': generate_password_hash(test_password)
    }
    # Make test request
    response = client.post('/admin_login', data={'username': test_username, 'password': test_password},
                           follow_redirects=True)
    print('testPass', test_password)
    print("Calls made to find_one:", mock_find_one.call_args_list)
    # Assertions
    assert response.status_code == 200
    mock_find_one.assert_called_once_with({'username': test_username})



