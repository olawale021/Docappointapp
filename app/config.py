# config.py

# Configuration file for Flask app
import os

import cloudinary
# Import the cloudinary.api for managing assets
import cloudinary.api
# Import the cloudinary.uploader for uploading assets
import cloudinary.uploader

cloudinary.config(
    cloud_name="dtvclnkeo",
    api_key="741531362294953",
    api_secret="YikgdsrjzgeeoGCc_t88sBSMQ70",
    secure=True,
)


class Config:
    SECRET_KEY = 'asdflkjhg'
    MONGO_URI = 'mongodb://localhost:27017/AppointmentDB'



