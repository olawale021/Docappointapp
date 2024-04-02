from flask_login import UserMixin

from app import mongo


class Patient(UserMixin):
    def __init__(self, username, first_name, last_name, date_of_birth, gender,
                 phone_number, password, address, image_url=None, blood_group=None, email=None,
                 registration_status='pending'):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.phone_number = phone_number
        self.password = password  # Make sure to hash the password before storing it
        self.address = address
        self.image_url = image_url  # New field for the patient's image URL
        self.blood_group = blood_group  # New field for the patient's blood group
        self.email = email
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
                gender=patient_data['gender'],
                phone_number=patient_data['phone_number'],
                password=patient_data['password'],  # Assuming this is already hashed
                address=patient_data['address'],
                image_url=patient_data.get('image_url'),  # Use .get for optional fields
                blood_group=patient_data.get('blood_group'),
                email=patient_data.get('email')
            )
        return None


class Doctor(UserMixin):
    def __init__(self, username, first_name, last_name, date_of_birth, gender,
                 phone_number, password, address, hospital, specialty,
                 registration_status='pending', image_url=None, biography=None,
                 education=None, experience=None, registration=None):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.phone_number = phone_number
        self.password = password
        self.address = address
        self.hospital = hospital
        self.specialty = specialty
        self.registration_status = registration_status
        self.image_url = image_url
        self.biography = biography
        self.education = education or []  # List of education records
        self.experience = experience or []  # List of experience records
        self.registration = registration or []  # List of registration records

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
                gender=doctor_data['gender'],
                phone_number=doctor_data['phone_number'],
                password=doctor_data['password'],  # Make sure to hash the password before storing it
                address=doctor_data['address'],
                hospital=doctor_data['hospital'],
                specialty=doctor_data['specialty'],
                registration_status=doctor_data.get('registration_status', 'pending'),
                image_url=doctor_data.get('image_url'),
                biography=doctor_data.get('biography'),
                education=doctor_data.get('education', []),
                experience=doctor_data.get('experience', []),
                registration=doctor_data.get('registration', [])
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
    def __init__(self, patient_id, doctor_id, date, time, status='requested'):
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.date = date
        self.time = time
        self.status = status

    @staticmethod
    def from_dict(appointment_data):
        return Appointment(
            patient_id=appointment_data['patient_id'],
            doctor_id=appointment_data['doctor_id'],
            date=appointment_data['date'],
            time=appointment_data['time'],
            status=appointment_data.get('status', 'requested')
        )

    def to_dict(self):
        return {
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'date': self.date,
            'time': self.time,
            'status': self.status
        }


