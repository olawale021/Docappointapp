from flask import render_template, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, mongo, login_manager
from flask import send_from_directory, Flask, request, jsonify
from app.models import Admin, Patient, Doctor
from app.utils import (get_all_doctors, is_doctor_available, validate_appointment_date,
                       get_busy_dates_by_doctor, get_patient_full_name, get_fixed_appointments_for_doctor,
                       get_appointment_requests_for_doctor)
from app.models import Appointment
from flask import jsonify
from bson import ObjectId


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
            return redirect(url_for('home'))

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
            doctor_id = data['doctor_id']
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
                'doctor_id': doctor_id,
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
    pending_patients = mongo.db.patients.find({'registration_status': 'pending'})
    pending_doctors = mongo.db.doctors.find({'registration_status': 'pending'})
    return render_template('admin/admin_dashboard.html',
                           pending_patients=pending_patients, pending_doctors=pending_doctors)


@app.route('/create_appointment', methods=['POST'])
def create_appointment():
    # Get form data
    patient_fullname = request.form['patient_fullname']
    doctor_username = request.form['doctor']
    date = request.form['date']

    # Check if date is valid
    if not validate_appointment_date(date):
        flash('You cannot book appointments on past dates.', 'error')
        return redirect(url_for('patient_dashboard'))

    # Check doctor's availability
    if not is_doctor_available(doctor_username, date):
        flash('The selected doctor is not available at the chosen date and time.', 'error')
        return redirect(url_for('patient_dashboard'))

    # Create Appointment instance
    appointment = Appointment(patient_fullname, doctor_username, date)

    # Save appointment to database
    mongo.db.appointments.insert_one(appointment.to_dict())

    flash('Appointment request has been submitted successfully.', 'success')
    return redirect(url_for('patient_dashboard'))


@app.route('/patient_login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        # Get form data
        phone_number = request.form['phone_number']
        password = request.form['password']

        # Query the database to check if username exists
        patient_data = mongo.db.patients.find_one({'phone_number': phone_number})

        if patient_data:
            # Check if the password is correct
            if check_password_hash(patient_data['password'], password):
                # Set session variables
                session['phone_number'] = phone_number
                session['registration_status'] = patient_data.get('registration_status', 'pending')

                # Redirect to patient dashboard
                return redirect(url_for('patient_dashboard'))
            else:
                flash('Invalid username or password.', 'error')
        else:
            flash('Invalid username or password.', 'error')

    return render_template('/patient/patient_login.html')


@app.route('/patient_dashboard', methods=['GET', 'POST'])
def patient_dashboard():
    doctors = get_all_doctors()
    busy_dates_by_doctor = get_busy_dates_by_doctor()

    # Check if user is logged in
    if 'phone_number' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('patient_login'))  # Assuming the login route is named 'login'

    # Get the phone number from the session
    phone_number = session['phone_number']

    # Retrieve patient data from the database
    patient_data = mongo.db.patients.find_one({'phone_number': phone_number})

    # Check if patient data exists and get registration status
    if patient_data:
        registration_status = patient_data.get('registration_status', 'pending')
        patient_full_name = get_patient_full_name(patient_data)
    else:
        flash('Patient data not found.', 'error')
        return redirect(url_for('patient_login'))  # Redirect to home or login page

    # Render appropriate template based on registration status
    if registration_status == 'pending':
        return render_template('patient/registration_pending.html')
    elif registration_status == 'approved':
        return render_template('patient/patient_dashboard.html', patient_full_name=patient_full_name,
                               doctors=doctors, busy_dates_by_doctor=busy_dates_by_doctor)


@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        password = request.form['password']

        # Check if doctor exists in the database
        doctor = mongo.db.doctors.find_one({'phone_number': phone_number})

        if doctor and check_password_hash(doctor['password'], password):
            # Doctor exists and password is correct
            session['doctor_username'] = doctor['username']
            flash('Login successful', 'success')
            return redirect(url_for('doctor_dashboard', username=doctor['username']))
        else:
            # Invalid credentials
            flash('Invalid phone number or password', 'error')

    return render_template('doctor/doctor_login.html')


@app.route('/doctor_dashboard/<username>')
def doctor_dashboard(username):

    doctor = mongo.db.doctors.find_one({'username': username})
    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('login'))  # Redirect to login page if doctor not found

    doctor_username = session.get('doctor_username')

    # Retrieve appointment requests for the specific doctor
    appointment_requests = get_appointment_requests_for_doctor(doctor_username)

    # Retrieve fixed appointments for the specific doctor
    fixed_appointments = get_fixed_appointments_for_doctor(doctor_username)
    print("Fixed Appointments:", fixed_appointments)

    return render_template('doctor/doctor_dashboard.html', doctor_username=username,
                           appointment_requests=appointment_requests, fixed_appointments=fixed_appointments)


@app.route('/approve_appointment/<appointment_id>', methods=['POST'])
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



