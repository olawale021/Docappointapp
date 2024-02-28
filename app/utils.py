from app import mongo
from datetime import datetime


def get_available_doctors():
    doctors = mongo.db.doctors.find({'registration_status': 'approved'})
    return [doctor['username'] for doctor in doctors]


def is_doctor_available(doctor_username, appointment_date):
    appointments_count = mongo.db.appointments.count_documents({
        'doctor_username': doctor_username,
        'date': appointment_date
    })
    return appointments_count == 0


def get_all_doctors():
    return mongo.db.doctors.find()


def get_busy_dates_by_doctor():
    busy_dates_by_doctor = {}
    appointments = mongo.db.appointments.find()
    for appointment in appointments:
        doctor_username = appointment['doctor_username']
        date = appointment['date']
        if doctor_username not in busy_dates_by_doctor:
            busy_dates_by_doctor[doctor_username] = [date]
        else:
            busy_dates_by_doctor[doctor_username].append(date)
    return busy_dates_by_doctor


def validate_appointment_date(date):
    today = datetime.now().date()
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    return selected_date >= today


def get_patient_full_name(patient):
    """
    Get the full name of a patient by concatenating their first name and last name.
    Args:
        patient (dict): Patient information dictionary containing 'first_name' and 'last_name' keys.
    Returns:
        str: Full name of the patient.
    """
    if 'first_name' in patient and 'last_name' in patient:
        return f"{patient['first_name']} {patient['last_name']}"
    else:
        return None


def get_fixed_appointments_for_doctor(doctor_username):
    # Query the database for fixed appointments for the specific doctor
    fixed_appointments = mongo.db.appointments.find({'doctor_username': doctor_username, 'status': 'approved'})
    return list(fixed_appointments)


def get_appointment_requests_for_doctor(doctor_username):
    # Query the database for appointment requests for the specific doctor
    appointment_requests = mongo.db.appointments.find({'doctor_username': doctor_username, 'status': 'requested'})
    return list(appointment_requests)
