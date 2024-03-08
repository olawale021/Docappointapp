from flask import render_template, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, mongo, login_manager
from flask import send_from_directory, Flask, request, jsonify
from pymongo.errors import PyMongoError
from app.models import Admin, Patient, Doctor
from app.utils import (get_all_doctors, is_doctor_available, validate_appointment_date,
                       get_busy_dates_by_doctor, get_patient_full_name, get_fixed_appointments_for_doctor,
                       get_appointment_requests_for_doctor, get_pending_patients,
                       get_total_appointments_count, get_all_appointments, get_approved_patients)
from app.models import Appointment
from flask import jsonify
from bson.objectid import ObjectId, InvalidId


@app.route('/')
def home():
    return send_from_directory('templates', 'homepage.html')


@app.route('/patient_registration', methods=['GET', 'POST'])
def patient_registration():
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            username = data['username']
            first_name = data['first_name']
            last_name = data['last_name']
            date_of_birth = data['date_of_birth']
            phone_number = data['phone_number']
            password = data['password']
            address = data['address']

            # Hash the password before storing it
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            # Insert the patient data into MongoDB
            mongo.db.patients.insert_one({
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': date_of_birth,
                'phone_number': phone_number,
                'password': hashed_password,
                'address': address,
                'registration_status': 'pending'
            })

            flash("Patient registration successful", "success")
            return redirect(url_for('registration_pending'))

        except KeyError as e:
            return jsonify({"error": f"Missing key: {str(e)}"}), 400

    return send_from_directory('templates', 'patient/patient_registration.html')


@app.route('/doctor_registration', methods=['GET', 'POST'])
def register_doctor():
    try:
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            username = data['username']
            first_name = data['first_name']
            last_name = data['last_name']
            date_of_birth = data['date_of_birth']
            phone_number = data['phone_number']
            password = data['password']
            address = data['address']
            hospital = data['hospital']
            specialty = data['specialty']

            # Hash the password before storing it
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            # Insert the doctor data into MongoDB
            mongo.db.doctors.insert_one({
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': date_of_birth,
                'phone_number': phone_number,
                'password': hashed_password,
                'address': address,
                'hospital': hospital,
                'specialty': specialty
            })

            flash("Doctor registration successful", "success")
            return redirect(url_for('home'))

        return send_from_directory('templates', 'doctor/doctor_registration.html')

    except KeyError as e:
        return jsonify({"error": f"Missing key: {str(e)}"}), 400


@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    try:
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            username = data['username']
            password = data['password']

            # Hash the password before storing it
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            # Insert the admin data into MongoDB
            mongo.db.admins.insert_one({
                'username': username,
                'password': hashed_password,
            })

            flash("Admin registration successful", "success")

        return render_template('/admin/admin_registration.html')

    except KeyError as e:
        return jsonify({"error": f"Missing key: {str(e)}"}), 400


@app.route('/approve_registration/<username>', methods=['POST'])
def approve_registration(username):
    # Update registration status to 'approved' for the specified username
    mongo.db.patients.update_one({'username': username}, {'$set': {'registration_status': 'approved'}})
    mongo.db.doctors.update_one({'username': username}, {'$set': {'registration_status': 'approved'}})

    return jsonify({"message": f"Registration for {username} approved"})


@app.route('/reject_registration/<username>', methods=['POST'])
def reject_registration(username):
    # Update registration status to 'rejected' for the specified username
    mongo.db.patients.update_one({'username': username}, {'$set': {'registration_status': 'rejected'}})
    mongo.db.doctors.update_one({'username': username}, {'$set': {'registration_status': 'rejected'}})

    return jsonify({"message": f"Registration for {username} rejected"})


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_username = request.form.get('username')
        admin_password = request.form.get('password')

        admin_data = mongo.db.admins.find_one({'username': admin_username})

        if admin_data and check_password_hash(admin_data['password'], admin_password):
            # Successful login
            user = Admin(admin_data['username'])
            login_user(user)

            # Store the user identifier (username) in the session
            session['user_id'] = user.get_id()

            # Redirect to the admin dashboard or the originally requested page (if 'next' exists)
            return redirect(request.args.get('next') or url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')

    return render_template('/admin/admin_login.html')


@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    # Only authenticated users can access this route
    # Show the admin dashboard
    patients_cursor = mongo.db.patients.find()
    doctor_cursor = mongo.db.doctors.find()
    # No need to fetch pending doctors

    # Convert cursors to lists for counting and passing to template
    all_patients = list(patients_cursor)
    all_doctors = list(doctor_cursor)  # Use the function to get total doctors count
    total_appointments_count = get_total_appointments_count()

    # Fetch all appointments and patients
    all_appointments = get_all_appointments()
    all_patients = len(all_patients)
    all_doctors = len(all_doctors)
    doctors = get_all_doctors()
    pending_patients = get_pending_patients()
    approved_patients = get_approved_patients()
    sample_appointment = all_appointments[0] if all_appointments else None
    print(sample_appointment)

    return render_template('admin/admin_dashboard.html',
                           all_patients=all_patients,
                           all_doctors=all_doctors,
                           doctors=doctors,
                           total_appointments_count=total_appointments_count,
                           all_appointments=all_appointments, pending_patients=pending_patients,
                           approved_patients=approved_patients)


@app.route('/patient_login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        # Get form data
        phone_number = request.form['phone_number']
        password = request.form['password']

        # Query the database to check if the phone number exists
        patient_data = mongo.db.patients.find_one({'phone_number': phone_number})

        if patient_data and check_password_hash(patient_data['password'], password):
            # Password is correct, set session variables
            session['patient_id'] = str(patient_data['_id'])  # Store patient_id in session

            registration_status = patient_data.get('registration_status', 'pending')

            if registration_status == 'pending':
                # Redirect to registration pending page
                return redirect(url_for('registration_pending'))
            elif registration_status == 'approved':
                # Redirect to patient dashboard
                return redirect(url_for('patient_dashboard'))
        else:
            # Invalid login attempt
            flash('Invalid phone number or password.', 'error')

    return render_template('/patient/patient_login.html')


@app.route('/create_appointment', methods=['POST'])
def create_appointment():
    # 'patient_id' is stored in session upon login
    patient_id = session.get('patient_id')
    doctor_id = request.form.get('doctor_id')
    date = request.form.get('date')
    time = request.form.get('time')

    # Convert IDs from string to ObjectId
    patient_oid = ObjectId(patient_id)
    doctor_oid = ObjectId(doctor_id)

    # Check if date and time are valid
    if not validate_appointment_date(date, time):
        flash('You cannot book appointments on past dates or times.', 'error')
        return redirect(url_for('book_appointment'))

    # Check doctor's availability
    if not is_doctor_available(doctor_id, date, time):
        flash('The selected doctor is not available at the chosen date and time.', 'error')
        return redirect(url_for('book_appointment'))

    # Create Appointment instance
    appointment = Appointment(patient_oid, doctor_oid, date, time)

    # Save appointment to database
    mongo.db.appointments.insert_one(appointment.to_dict())

    flash('Appointment request has been submitted successfully.', 'success')
    return redirect(url_for('booking_success', doctor_id=doctor_id, date=date, time=time))


@app.route('/booking_success')
def booking_success():
    doctor_id = request.args.get('doctor_id', None)
    appointment_date = request.args.get('date', None)
    appointment_time = request.args.get('time', None)

    doctor_info = None
    if doctor_id:
        try:
            doctor_oid = ObjectId(doctor_id)
        except InvalidId:
            flash('Invalid doctor ID provided.', 'error')
            return redirect(url_for('some_error_handling_route'))  # Adjust this to your actual error handling route

        try:
            doctor_info = mongo.db.doctors.find_one({'_id': doctor_oid})
        except PyMongoError as e:
            flash('Database error occurred.', 'error')
            return redirect(url_for('some_error_handling_route'))  # Adjust this to your actual error handling route

        if not doctor_info:
            flash('Doctor not found.', 'error')
            return redirect(url_for('some_error_handling_route'))  # Adjust this to your actual error handling route

    return render_template('/patient/booking_success.html',
                           doctor_info=doctor_info,
                           appointment_date=appointment_date,
                           appointment_time=appointment_time)


@app.route('/registration_pending')
def registration_pending():
    return render_template('/patient/registration_pending.html')


@app.route('/patient_dashboard', methods=['GET', 'POST'])
def patient_dashboard():
    if 'patient_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('patient_login'))

    patient_id = session['patient_id']
    try:
        patient_oid = ObjectId(patient_id)
    except InvalidId:
        flash('Invalid patient ID.', 'error')
        return redirect(url_for('patient_login'))

    patient_data = mongo.db.patients.find_one({'_id': patient_oid})

    if not patient_data:
        flash('Patient data not found.', 'error')
        return redirect(url_for('patient_login'))

    # Fetch appointments for the logged-in patient
    appointments = mongo.db.appointments.find({'patient_id': patient_oid})

    # Optional: Convert appointments cursor to a list if you plan to iterate over it multiple times
    appointments_list = list(appointments)

    # Attach doctor's information to each appointment
    for appointment in appointments_list:
        doctor_oid = appointment['doctor_id']
        doctor_info = mongo.db.doctors.find_one({'_id': doctor_oid})
        appointment['doctor_info'] = doctor_info

    registration_status = patient_data.get('registration_status', 'pending')
    patient_full_name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}".strip()
    doctors = get_all_doctors()
    busy_dates_by_doctor = get_busy_dates_by_doctor()

    if registration_status == 'pending':
        return render_template('patient/registration_pending.html')
    elif registration_status == 'approved':
        return render_template('patient/patient_dashboard.html', patient_full_name=patient_full_name,
                               doctors=doctors, busy_dates_by_doctor=busy_dates_by_doctor, patient_id=patient_id,
                               patient_info=patient_data, appointments=appointments_list)


@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        password = request.form['password']

        # Check if doctor exists in the database
        doctor = mongo.db.doctors.find_one({'phone_number': phone_number})

        if doctor and check_password_hash(doctor['password'], password):
            # Doctor exists and password is correct
            session['doctor_id'] = str(doctor['_id'])  # Store doctor_id in session
            flash('Login successful', 'success')
            return redirect(url_for('doctor_dashboard'))
        else:
            # Invalid credentials
            flash('Invalid phone number or password', 'error')

    return render_template('doctor/doctor_login.html')


@app.route('/doctor_dashboard')
def doctor_dashboard():
    doctor_id = session.get('doctor_id')
    if not doctor_id:
        flash('Please login first.', 'error')
        return redirect(url_for('doctor_login'))

    # Convert string doctor_id back to ObjectId for database query
    doctor_oid = ObjectId(doctor_id)

    doctor = mongo.db.doctors.find_one({'_id': doctor_oid})
    print("doctor", doctor)
    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('doctor_login'))

    # Retrieve appointment requests for the specific doctor
    appointment_requests = get_appointment_requests_for_doctor(doctor_id)

    # Retrieve fixed appointments for the specific doctor
    fixed_appointments = get_fixed_appointments_for_doctor(doctor_id)

    return render_template('doctor/doctor_dashboard.html', doctor=doctor,
                           appointment_requests=appointment_requests, fixed_appointments=fixed_appointments)


@app.route('/approve_appointment/<appointment_id>', methods=['GET','POST'])
def approve_appointment(appointment_id):
    # Convert appointment_id to ObjectId
    appointment_id = ObjectId(appointment_id)
    # print("Appointment ID:", appointment_id)  # Debug print
    appointment = mongo.db.appointments.find_one({'_id': appointment_id})
    # print("Appointment:", appointment)  # Debug print

    # Check if the appointment exists
    if not appointment:
        return jsonify({"message": "Appointment not found"}), 404

    # Update appointment status to approved
    mongo.db.appointments.update_one({'_id': appointment_id}, {'$set': {'status': 'approved'}})

    return jsonify({"message": "Appointment approved"}), 200


@app.route('/delete_appointment/<appointment_id>', methods=['POST'])
def delete_appointment(appointment_id):
    # Convert appointment_id to ObjectId
    appointment_id = ObjectId(appointment_id)
    # Find the appointment by its ID
    appointment = mongo.db.appointments.find_one({'_id': appointment_id})

    # Check if the appointment exists
    if not appointment:
        return jsonify({"message": "Appointment not found"}), 404

    # Delete the appointment
    mongo.db.appointments.delete_one({'_id': appointment_id})

    return jsonify({"message": "Appointment deleted"}), 200


@app.route('/search_doctor')
def search_doctor():
    doctors_collection = mongo.db.doctors

    # Fetch all doctors from the database
    doctors = doctors_collection.find()

    return render_template('/doctor/search_doctor.html', doctors=doctors)


@app.route('/book_appointment')
def book_appointment():
    doctor_id = request.args.get('doctor_id')

    if not doctor_id:
        flash('Doctor ID not provided.', 'error')
        return redirect(url_for('some_route'))  # Adjust with your actual route

    try:
        doctor_oid = ObjectId(doctor_id)
    except InvalidId:
        flash('Invalid doctor ID provided.', 'error')
        return redirect(url_for('some_route'))  # Adjust with your actual route

    try:
        doctor_info = mongo.db.doctors.find_one({'_id': doctor_oid})
        if not doctor_info:
            flash('Doctor not found.', 'error')
            return redirect(url_for('some_route'))  # Adjust with your actual route
    except PyMongoError:
        flash('Database error occurred.', 'error')
        return redirect(url_for('some_route'))  # Adjust with your actual route

    # patient ID is stored in session upon login
    patient_id = session.get('patient_id')
    if not patient_id:
        flash('You need to be logged in to book an appointment.', 'error')
        return redirect(url_for('login_route'))  # Adjust with your login route
    print("pid", patient_id)
    print("did", doctor_id)
    return render_template('/patient/book_appointment.html', doctor_id=doctor_id,
                           doctor_info=doctor_info, patient_id=patient_id)


