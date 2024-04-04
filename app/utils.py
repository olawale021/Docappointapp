from app import mongo
from datetime import datetime
from bson import ObjectId


from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class AppointmentForm(FlaskForm):
    # Define form fields here
    patient_id = StringField('Patient ID', validators=[DataRequired()])
    doctor_id = StringField('Doctor ID', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    time = StringField('Time', validators=[DataRequired()])
    submit = SubmitField('Book Appointment')


def get_available_doctors():
    doctors = mongo.db.doctors.find({'registration_status': 'approved'})
    return [doctor['username'] for doctor in doctors]


def is_doctor_available(doctor_id, date, time):

    doctor_oid = ObjectId(doctor_id)

    # Count appointments for the given doctor, date, and time
    appointments_count = mongo.db.appointments.count_documents({
        'doctor_id': doctor_oid,
        'date': date,
        'time': time
    })

    # If there are no appointments for this doctor at the given date and time, they are available
    return appointments_count == 0


def get_all_doctors():
    return mongo.db.doctors.find()


from bson import ObjectId


def get_busy_dates_by_doctor():
    busy_dates_by_doctor = {}
    appointments = mongo.db.appointments.find()
    for appointment in appointments:
        # Check if 'doctor_id' key exists in the document
        if 'doctor_id' in appointment:
            # Ensure doctor_id is a string for consistent dictionary keys
            doctor_id_str = str(appointment['doctor_id'])
            date = appointment['date']
            if doctor_id_str not in busy_dates_by_doctor:
                busy_dates_by_doctor[doctor_id_str] = [date]
            else:
                if date not in busy_dates_by_doctor[doctor_id_str]:
                    busy_dates_by_doctor[doctor_id_str].append(date)
        else:
            # Handle case where 'doctor_id' is not present, e.g., log a warning
            print(f"Warning: Appointment {appointment['_id']} missing 'doctor_id'")

    return busy_dates_by_doctor


def validate_appointment_date(date, time):
    # Split the time string to get only the start time if it's a range
    start_time = time.split(' - ')[0]  # Assumes time is in the format "09:00 - 12:30"

    # Combine date and start_time into a single datetime object
    appointment_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")

    # Get the current datetime
    now = datetime.now()

    # Check if the appointment datetime is in the past
    return appointment_datetime >= now


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


def get_appointment_requests_for_doctor(doctor_id):
    appointments = mongo.db.appointments.find({'doctor_id': ObjectId(doctor_id), 'status': 'requested'})
    appointments_list = list(appointments)

    for appointment in appointments_list:
        patient_id = appointment.get('patient_id')
        if patient_id:
            # Fetch the patient information for each appointment
            patient_info = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})
            # Add the patient information to the appointment document
            appointment['patient_info'] = patient_info
        else:
            appointment['patient_info'] = None

    return appointments_list


from bson.objectid import ObjectId


def get_fixed_appointments_for_doctor(doctor_id):
    """
    Retrieve fixed (confirmed) appointments for a specific doctor and include patient information.
    :param doctor_id: The ObjectId of the doctor.
    :return: A list of fixed appointments with patient information.
    """
    try:
        # Convert string doctor_id to ObjectId
        doctor_oid = ObjectId(doctor_id)
        # Query for confirmed appointments
        fixed_appointments = list(mongo.db.appointments.find({'doctor_id': doctor_oid, 'status': 'approved'}))

        # Enhance each appointment with patient information
        for appointment in fixed_appointments:
            patient_id = appointment.get('patient_id')
            if patient_id:
                # Fetch the patient information for each appointment
                patient_info = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})
                # Add the patient information to the appointment document
                appointment['patient_info'] = patient_info
            else:
                appointment['patient_info'] = None

        return fixed_appointments
    except Exception as e:
        print(f"Error retrieving fixed appointments: {e}")
        return []


def get_available_doctors_count():
    return mongo.db.doctors.count_documents({'registration_status': 'approved'})


def get_total_doctors_count():
    return mongo.db.doctors.count_documents({})


def get_total_appointments_count():
    return mongo.db.appointments.count_documents({})


def get_all_appointments():
    appointments = mongo.db.appointments.find()
    appointments_with_details = []

    for appointment in appointments:
        # Use the .get() method for safe access
        patient_id = appointment.get('patient_id')
        doctor_id = appointment.get('doctor_id')

        # Initialize as None to handle missing information
        patient_info = None
        doctor_info = None

        # Fetch patient information if patient_id exists
        if patient_id:
            patient_info = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})

        # Fetch doctor information if doctor_id exists
        if doctor_id:
            doctor_info = mongo.db.doctors.find_one({'_id': ObjectId(doctor_id)})

        # Update appointment details
        appointment_details = dict(appointment)
        appointment_details['patient_info'] = patient_info
        appointment_details['doctor_info'] = doctor_info

        appointments_with_details.append(appointment_details)

    return appointments_with_details


def get_all_patients():
    return list(mongo.db.patients.find())


def get_patients_by_registration_status(status):
    """
    Get patients based on their registration status.
    Args:
        status (str): Registration status, e.g., 'pending', 'approved'.
    Returns:
        list: List of patients with the specified registration status.
    """
    return mongo.db.patients.find({'registration_status': status})


def get_pending_patients():
    """
    Get patients with registration status 'pending'.
    Returns:
        list: List of patients with registration status 'pending'.
    """
    return get_patients_by_registration_status('pending')


def get_approved_patients():
    """
    Get patients with registration status 'approved'.
    Returns:
        list: List of patients with registration status 'approved'.
    """
    return get_patients_by_registration_status('approved')


# def get_doctor_info(doctor_id):
#     """
#     Retrieve doctor information by doctor ID.
#
#     Args:
#         doctor_id (str): The ID of the doctor to retrieve.
#
#     Returns:
#         dict: Doctor information if found, None otherwise.
#     """
#     return mongo.db.doctors.find_one({'_id': ObjectId(doctor_id)})
