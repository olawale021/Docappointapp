
# Initialization of Flask app, configuration of MongoDB, and setup of Flask-Login
from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_cors import CORS
from flask_bootstrap import Bootstrap


app = Flask(__name__, template_folder='templates')
app.config.from_object('app.config.Config')
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

mongo = PyMongo(app)
bootstrap = Bootstrap(app)


@login_manager.user_loader
def load_user(username):
    from app.models import Patient, Doctor, Admin  # Import here to avoid circular import
    # Assuming you have a User model with a method like User.get
    return Patient.get(username) or Doctor.get(username) or Admin.get(username)


from app import routes

