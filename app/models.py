from flask_login import UserMixin
from app import mongo


class Patient(UserMixin):
    def __init__(self, username, first_name,
                 last_name, date_of_birth,
                 phone_number, password,
                 address, registration_status='pending'):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.phone_number = phone_number
        self.password = password  # Make sure to hash the password before storing it
        self.address = address
        self.registration_status = registration_status

    def get_id(self):
        return self.username

    @staticmethod
    def get(username):
        patient_data = mongo.db.patients.find_one({'username': username})
        if patient_data:
            return Patient(
                username=patient_data['username'],
                first_name=patient_data['first_name'],
                last_name=patient_data['last_name'],
                date_of_birth=patient_data['date_of_birth'],
                phone_number=patient_data['phone_number'],
                password=patient_data['password'],  # Make sure to hash the password before storing it
                address=patient_data['address']
            )
        return None


class Doctor(UserMixin):
    def __init__(self, username, first_name,
                 last_name, date_of_birth,
                 phone_number, password,
                 address, doctor_id,
                 specialty, registration_status='pending'):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.phone_number = phone_number
        self.password = password  # Make sure to hash the password before storing it
        self.address = address
        self.doctor_id = doctor_id
        self.specialty = specialty
        self.registration_status = registration_status

    def get_id(self):
        return self.username

    @staticmethod
    def get(username):
        doctor_data = mongo.db.doctors.find_one({'username': username})
        if doctor_data:
            return Doctor(
                username=doctor_data['username'],
                first_name=doctor_data['first_name'],
                last_name=doctor_data['last_name'],
                date_of_birth=doctor_data['date_of_birth'],
                phone_number=doctor_data['phone_number'],
                password=doctor_data['password'],  # Make sure to hash the password before storing it
                address=doctor_data['address'],
                doctor_id=doctor_data['doctor_id'],
                specialty=doctor_data['specialty']
            )
        return None


class Admin(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username

    @staticmethod
    def get(username):
        # Fetch admin data from MongoDB and create an Admin instance
        admin_data = mongo.db.admins.find_one({'username': username})
        if admin_data:
            return Admin(username=admin_data['username'])
        return None


class Appointment:
    def __init__(self, patient_fullname, doctor_username, date, status='requested'):
        self.patient_fullname = patient_fullname
        self.doctor_username = doctor_username
        self.date = date
        self.status = status

    @staticmethod
    def from_dict(appointment_data):
        return Appointment(
            patient_fullname=appointment_data['patient_fullname'],
            doctor_username=appointment_data['doctor_username'],
            date=appointment_data['date'],
            status=appointment_data.get('status', 'requested')
        )

    def to_dict(self):
        return {
            'patient_fullname': self.patient_fullname,
            'doctor_username': self.doctor_username,
            'date': self.date,
            'status': self.status
        }

