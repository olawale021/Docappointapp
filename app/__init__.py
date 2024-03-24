
# Initialization of Flask app, configuration of MongoDB, and setup of Flask-Login
from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_cors import CORS
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
import logging


app = Flask(__name__, template_folder='templates')
app.config.from_object('app.config.Config')

login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
csrf = CSRFProtect(app)
mongo = PyMongo(app)
logging.basicConfig(level=logging.INFO)
bootstrap = Bootstrap(app)


@login_manager.user_loader
def load_user(_id):
    from app.models import Patient, Doctor, Admin  # Import here to avoid circular import
    # Assuming you have a User model with a method like User.get
    return Patient.get(_id) or Doctor.get(_id) or Admin.get(_id)


from app import routes

