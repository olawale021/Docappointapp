from flask import render_template, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, mongo, login_manager
from flask import send_from_directory, Flask, request, jsonify
from pymongo.errors import PyMongoError
from app.models import Admin, Patient, Doctor
from app.utils import (get_all_doctors, is_doctor_available, validate_appointment_date,
                       get_busy_dates_by_doctor, get_patient_full_name, get_fixed_appointments_for_doctor,
                       get_appointment_requests_for_doctor, get_pending_patients,
                       get_total_appointments_count, get_all_appointments, get_approved_patients, AppointmentForm)
from app.models import Appointment
from flask import jsonify
from bson.objectid import ObjectId, InvalidId
from flask_wtf.csrf import generate_csrf
import logging
import cloudinary.uploader
from PIL import Image
import io


@app.route('/')
def home():
    doctors_collection = mongo.db.doctors
    approved_doctors = doctors_collection.find({"registration_status": "approved"})
    return render_template('homepage.html', doctors=approved_doctors)


@app.route('/patient_registration', methods=['GET', 'POST'])
def patient_registration():

    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
                logging.info('Received JSON data: %s', data)

            else:
                data = request.form.to_dict()
                logging.info('Received form data: error', data)

            username = data['username']
            first_name = data['first_name']
            last_name = data['last_name']
            date_of_birth = data['date_of_birth']
            gender = data['gender']
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
                'gender': gender,
                'phone_number': phone_number,
                'password': hashed_password,
                'address': address,
                'registration_status': 'pending'
            })

            flash("Patient registration successful", "success", )
            return render_template('/patient/registration_pending.html', csrf_token=generate_csrf())

        except KeyError as e:
            return jsonify({"error": f"Missing key: {str(e)}"}), 400

    return render_template('patient/patient_registration.html', csrf_token=generate_csrf())


@app.route('/doctor_registration', methods=['GET', 'POST'])
def register_doctor():
    try:
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict(flat=True)  # Convert ImmutableMultiDict to regular dict

            username = data['username']
            first_name = data['first_name']
            last_name = data['last_name']
            date_of_birth = data['date_of_birth']
            gender = data['gender']
            phone_number = data['phone_number']
            password = data['password']
            # Handle address as an object
            address = {
                "street": data.get('address_street'),
                "city": data.get('address_city'),
                "country": data.get('address_country'),
                "postcode": data.get('address_postcode'),
            }
            hospital = data['hospital']
            specialty = data['specialty']
            image_url = data.get('image_url')  # Optional
            biography = data.get('biography')

            education = [{
                "degree": data.get('degree'),
                "college_institute": data.get('college_institute'),
                "year_of_completion": data.get('year_of_completion')
            }]

            experience = [{
                "hospital_name": data.get('hospital'),
                "from_date": data.get('from_date'),
                "to_date": data.get('to_date'),
                "role": data.get('role')
            }]

            registration = [{
                "registration_name": data.get('registration_name'),
                "year": data.get('year'),
            }]

            # Hash the password before storing it
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            # Insert the doctor data into MongoDB
            mongo.db.doctors.insert_one({
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': date_of_birth,
                'gender': gender,
                'phone_number': phone_number,
                'password': hashed_password,
                'address': address,  # Store address as an object
                'hospital': hospital,
                'specialty': specialty,
                'registration_status': 'pending',
                'image_url': image_url,
                'biography': biography,
                'education': education,
                'experience': experience,
                'registration': registration
            })

            flash("Doctor registration successful", "success")
            return render_template('/patient/registration_pending.html', csrf_token=generate_csrf())

        return render_template('/doctor/doctor_registration.html', csrf_token=generate_csrf())

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

        return render_template('/admin/admin_registration.html', )

    except KeyError as e:
        return jsonify({"error": f"Missing key: {str(e)}"}), 400


from flask import jsonify
from bson import ObjectId


@app.route('/approve_registration/<patient_id>', methods=['POST'])
def approve_registration(patient_id):
    try:
        # Convert the string ID to a MongoDB ObjectId
        object_id = ObjectId(patient_id)

        # Update registration status to 'approved' for the specified patient ID
        result = mongo.db.patients.update_one({'_id': object_id}, {'$set': {'registration_status': 'approved'}})

        # Check if the update was successful
        if result.matched_count > 0:
            message = f"Registration for patient with ID {patient_id} approved"
            status = "success"
        else:
            message = "Patient not found."
            status = "error"

        return jsonify({"message": message, "status": status})

    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}", "status": "error"})


@app.route('/approve_doctor/<doctor_id>', methods=['POST'])
def approve_doctor(doctor_id):
    try:
        # Convert the string ID to a MongoDB ObjectId
        object_id = ObjectId(doctor_id)

        # Update approval status to 'approved' for the specified doctor ID
        result = mongo.db.doctors.update_one({'_id': object_id}, {'$set': {'approval_status': 'approved'}})

        # Check if the update was successful
        if result.matched_count > 0:
            message = f"Approval for doctor with ID {doctor_id} granted."
            status = "success"
        else:
            message = "Doctor not found."
            status = "error"

        return jsonify({"message": message, "status": status})

    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}", "status": "error"})


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
        print("Before find_one call")
        admin_data = mongo.db.admins.find_one({'username': admin_username})
        print("After find_one call", admin_data)

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

    return render_template('/admin/admin_login.html', csrf_token=generate_csrf())


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
    # print("smple", all_appointments)

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

    return render_template('/patient/patient_login.html', csrf_token=generate_csrf())


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
            return redirect(url_for('some_error_handling_route'))

        try:
            doctor_info = mongo.db.doctors.find_one({'_id': doctor_oid})
        except PyMongoError as e:
            flash('Database error occurred.', 'error')
            return redirect(url_for('some_error_handling_route'))

        if not doctor_info:
            flash('Doctor not found.', 'error')
            return redirect(url_for('some_error_handling_route'))

    return render_template('/patient/booking_success.html',
                           doctor_info=doctor_info,
                           appointment_date=appointment_date,
                           appointment_time=appointment_time)


@app.route('/registration_pending')
def registration_pending():
    return render_template('/patient/registration_pending.html', csrf_token=generate_csrf())


@app.route('/patient_dashboard', methods=['GET'])
def patient_dashboard():
    if 'patient_id' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('patient_login'))

    patient_id = session['patient_id']
    try:
        patient_oid = ObjectId(patient_id)
        patient_data = mongo.db.patients.find_one({'_id': patient_oid})
        app.logger.debug('Patient IDs: %s', patient_data)
    except:
        flash('An error occurred.', 'error')
        return redirect(url_for('patient_login'))

    if not patient_data:
        flash('Patient data not found.', 'error')
        return redirect(url_for('patient_login'))

    appointments = mongo.db.appointments.find({'patient_id': patient_oid})
    appointments_list = list(appointments)

    for appointment in appointments_list:
        doctor_oid = appointment['doctor_id']
        doctor_info = mongo.db.doctors.find_one({'_id': doctor_oid})
        appointment['doctor_info'] = doctor_info

    registration_status = patient_data.get('registration_status', 'pending')
    patient_full_name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}".strip()

    # Assuming get_all_doctors() and get_busy_dates_by_doctor() are defined elsewhere and applicable
    doctors = get_all_doctors()
    busy_dates_by_doctor = get_busy_dates_by_doctor()

    if registration_status == 'pending':
        return render_template('/patient/registration_pending.html')
    elif registration_status == 'approved':
        return render_template('/patient/patient_dashboard.html', patient_full_name=patient_full_name,
                               doctors=doctors, busy_dates_by_doctor=busy_dates_by_doctor, patient_id=patient_id,
                               patient_info=patient_data, appointments=appointments_list)
    else:
        flash('Unexpected registration status.', 'error')
        return redirect(url_for('home'))


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

    return render_template('doctor/doctor_login.html', csrf_token=generate_csrf())


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
                           appointment_requests=appointment_requests, fixed_appointments=fixed_appointments, csrf_token=generate_csrf())


@app.route('/approve_appointment/<appointment_id>', methods=['GET', 'POST'])
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
    address_city = request.args.get('address_city')
    name = request.args.get('name')
    gender = request.args.get('gender')

    query = {}
    if address_city:
        query["address.city"] = address_city
    if name:
        # If your database is set up to support text search on the 'name' field
        query["$text"] = {"$search": name}
    if gender:
        # Assuming gender is stored directly and doesn't need text search
        query["gender"] = gender

    doctors_collection = mongo.db.doctors

    # Apply the query filters when fetching doctors from the database
    doctors = doctors_collection.find(query)

    # Convert doctors to a list if necessary (depending on your template rendering needs)
    doctors_list = list(doctors)

    current_gender = request.args.get('gender', '')

    return render_template('/doctor/search_doctor.html', doctors=doctors_list, current_gender=current_gender)


@app.route('/book_appointment')
def book_appointment():
    form = AppointmentForm()
    doctor_id = request.args.get('doctor_id')

    if not doctor_id:
        flash('Doctor ID not provided.', 'error')
        return redirect(url_for('some_route'))

    try:
        doctor_oid = ObjectId(doctor_id)
    except InvalidId:
        flash('Invalid doctor ID provided.', 'error')
        return redirect(url_for('some_route'))

    try:
        doctor_info = mongo.db.doctors.find_one({'_id': doctor_oid})
        if not doctor_info:
            flash('Doctor not found.', 'error')
            return redirect(url_for('some_route'))
    except PyMongoError:
        flash('Database error occurred.', 'error')
        return redirect(url_for('some_route'))

    # patient ID is stored in session upon login
    patient_id = session.get('patient_id')
    if not patient_id:
        flash('You need to be logged in to book an appointment.', 'error')
        return redirect(url_for('patient_login'))  # Adjust with your login route
    print("pid", patient_id)
    print("did", doctor_id)
    return render_template('/patient/book_appointment.html', doctor_id=doctor_id,
                           doctor_info=doctor_info, patient_id=patient_id, form=form)


@app.route('/admin_appointments')
def admin_appointments():
    try:
        appointments = mongo.db.appointments.find()
        # Optionally, enrich appointments with patient and doctor info
        appointments_list = []
        for appointment in appointments:
            try:
                appointment['patient_info'] = mongo.db.patients.find_one({'_id': appointment['patient_id']})
                appointment['doctor_info'] = mongo.db.doctors.find_one({'_id': appointment['doctor_id']})
            except KeyError:
                # Handle missing patient_id or doctor_id
                continue
            appointments_list.append(appointment)
        return render_template('/admin/admin_appointments.html', appointments=appointments_list,
                               csrf_token=generate_csrf())
    except PyMongoError as e:
        flash(f"Database error: {e}", 'error')
        return redirect(url_for('admin_dashboard', csrf_token=generate_csrf()))


# Route to update appointment status
@app.route('/admin/appointments/update_status', methods=['POST'])
def update_appointment_status():
    data = request.json
    appointment_id = data.get('appointment_id')
    new_status = data.get('new_status')

    # Server-side logging
    print(f"Attempting to update appointment {appointment_id} to status {new_status}")
    print(data)
    try:
        result = mongo.db.appointments.update_one(
            {'_id': ObjectId(appointment_id)},
            {'$set': {'status': new_status}}
        )

        if result.modified_count > 0:
            print(f"Successfully updated appointment {appointment_id} to status {new_status}")
            flash('Appointment status updated successfully.', 'success')
            return jsonify({'message': 'Success'})
        else:
            print(f"No changes made for appointment {appointment_id}")
            flash('No changes made to appointment status.', 'info')
            return jsonify({'message': 'No changes made'}), 200
    except Exception as e:
        print(f"Failed to update appointment status: {str(e)}")
        flash(f"Failed to update appointment status: {str(e)}", 'error')
        return jsonify({'message': 'Failed to update status'}), 500


# Route to delete appointment
@app.route('/admin/appointments/delete/<appointment_id>', methods=['POST'])
def admin_delete_appointment(appointment_id):
    try:
        mongo.db.appointments.delete_one({'_id': ObjectId(appointment_id)})
        flash('Appointment deleted successfully.', 'success')
    except PyMongoError as e:
        flash(f"Failed to delete appointment: {e}", 'error')
    return redirect(url_for('admin_appointments'))


@app.route('/admin/patients')
def admin_patients():
    patients = mongo.db.patients.find()
    patients_list = list(patients)
    return render_template('/admin/admin_patients.html', patients=patients_list, csrf_token=generate_csrf())


@app.route('/admin/patients/update_status/<patient_id>', methods=['POST'])
def update_patients_status(patient_id):
    new_status = request.form.get('status')
    try:
        object_id = ObjectId(patient_id)
        result = mongo.db.patients.update_one({'_id': object_id}, {'$set': {'registration_status': new_status}})

        if result.matched_count == 0:
            flash('Patient not found.', 'error')
        else:
            flash('Patient status updated successfully.', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')

    return redirect(url_for('admin_patients'))


@app.route('/admin/patients/delete/<patient_id>', methods=['POST'])
def delete_patient(patient_id):
    try:
        # Convert the string ID to a MongoDB ObjectId
        object_id = ObjectId(patient_id)

        result = mongo.db.patients.delete_one({'_id': object_id})

        if result.deleted_count == 0:
            return render_template('admin/error_message.html', message="Patient not found")

        return render_template('admin/success_message.html')

    except Exception as e:
        return render_template('admin/error_message.html', message=f"An error occurred: {str(e)}")


@app.route('/admin/doctors')
def admin_doctors():
    doctors = mongo.db.doctors.find()
    doctors_list = list(doctors)
    return render_template('/admin/admin_doctors.html', doctors=doctors_list, csrf_token=generate_csrf())


@app.route('/admin/doctors/update_status/<doctor_id>', methods=['POST'])
def update_doctor_status(doctor_id):
    new_status = request.form.get('status')
    try:
        object_id = ObjectId(doctor_id)
        result = mongo.db.doctors.update_one({'_id': object_id}, {'$set': {'registration_status': new_status}})

        if result.matched_count == 0:
            flash('Doctor not found.', 'error')
        else:
            flash('Doctor status updated successfully.', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')

    return redirect(url_for('admin_doctors'))


@app.route('/admin/doctors/delete/<doctor_id>', methods=['POST'])
def delete_doctor(doctor_id):
    try:
        # Convert the string ID to a MongoDB ObjectId
        object_id = ObjectId(doctor_id)

        result = mongo.db.doctors.delete_one({'_id': object_id})

        if result.deleted_count == 0:
            return render_template('admin/error_message.html', message="Doctor not found")

        return render_template('admin/success_message.html')

    except Exception as e:
        return render_template('admin/error_message.html', message=f"An error occurred: {str(e)}")


@app.route('/doctor_logout')
def doctor_logout():
    logout_user()
    session.clear()
    return redirect(url_for('home'))


@app.route('/patient_logout')
def patient_logout():
    logout_user()
    session.clear()
    return redirect(url_for('home'))


@app.route('/admin_logout')
@login_required
def admin_logout():
    if current_user.is_authenticated:
        logout_user()
        session.clear()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


@app.route('/doctor_profile_settings', methods=['GET', 'POST'])
def doctor_profile_settings():
    doctor_id = session.get('doctor_id')
    if not doctor_id:
        flash('Please login first.', 'error')
        return redirect(url_for('doctor_login'))

    # Convert string doctor_id back to ObjectId for database query
    doctor_oid = ObjectId(doctor_id)

    doctor = mongo.db.doctors.find_one({'_id': doctor_oid})

    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('doctor_login'))

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        # Handle image upload to Cloudinary if a file is provided
        if 'image' in request.files:
            image_to_upload = request.files['image']

            if image_to_upload:
                # Open the image file using its stream
                img = Image.open(image_to_upload.stream)  # Adjusted here

                # Resize the image
                img = img.resize((369, 445))  # Specify desired size

                # Save the resized image to a bytes buffer
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')  # Ensure format is explicitly set if original format is unknown

                # Seek to the start of the bytes buffer
                img_byte_arr.seek(0)

                # Upload the image from the bytes buffer
                result = cloudinary.uploader.upload(img_byte_arr, resource_type='image')
                image_url = result.get('secure_url')

                # Update image_url in the data dictionary to be stored
                data['image_url'] = image_url

        # Prepare the update dictionary
        update_data = {
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'date_of_birth': data.get('date_of_birth'),
            'gender': data.get('gender'),
            'phone_number': data.get('phone_number'),
            'address': {
                "street": data.get('address_street'),
                "city": data.get('address_city'),
                "country": data.get('address_country'),
                "postcode": data.get('address_postcode'),
            },
            'hospital': data.get('hospital'),
            'specialty': data.get('specialty'),
            'image_url': data.get('image_url'),
            'biography': data.get('biography'),
            'education': [{
                "degree": data.get('degree'),
                "college_institute": data.get('college_institute'),
                "year_of_completion": data.get('year_of_completion')
            }],
            'registration': [{
                "registration_name": data.get('registration_name'),
                "year": data.get('year')
            }]
        }

        # Only include fields that are not None
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # Update the doctor's profile in MongoDB
        mongo.db.doctors.update_one({'_id': doctor_oid}, {'$set': update_data})

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('doctor_dashboard', csrf_token=generate_csrf()))

    # GET request: Load the update form with the current user's data
    doctor_data = mongo.db.doctors.find_one({'_id': doctor_oid})
    if doctor_data:
        return render_template('doctor/doctor_profile_settings.html', doctor=doctor_data, csrf_token=generate_csrf())

    else:
        flash('Doctor profile not found.', 'error')
        print("data", doctor_data)
        return redirect(url_for('doctor_dashboard', csrf_token=generate_csrf()))


@app.route('/doctor_appointment')
def doctor_appointment():
    doctor_id = session.get('doctor_id')
    if not doctor_id:
        flash('Please login first.', 'error')
        return redirect(url_for('doctor_login'))

    doctor_oid = ObjectId(doctor_id)
    doctor = mongo.db.doctors.find_one({'_id': doctor_oid})

    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('doctor_login'))

    appointments_cursor = mongo.db.appointments.find({'doctor_id': doctor_oid})

    # Convert cursor to list and enrich with patient info
    appointments_list = []
    for appointment in appointments_cursor:
        patient = mongo.db.patients.find_one({'_id': appointment['patient_id']})
        if patient:
            appointment['patient_name'] = patient.get('name')
            appointment['patient_address'] = patient.get('address')
            appointment['patient_phone'] = patient.get('phone_number')
            appointment['patient_image_url'] = patient.get('image_url', 'assets/img/patients/default.jpg')
        appointments_list.append(appointment)

    return render_template('/doctor/doctor_appointment.html', appointments=appointments_list, doctor=doctor)


@app.route('/appointment/<appointment_id>/accept', methods=['POST'])
def accept_appointment(appointment_id):
    doctor_id = session.get('doctor_id')
    if not doctor_id:
        flash('Please login first.', 'error')
        return redirect(url_for('doctor_login'))

    doctor_oid = ObjectId(doctor_id)
    doctor = mongo.db.doctors.find_one({'_id': doctor_oid})

    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('doctor_login'))
    try:
        mongo.db.appointments.update_one({'_id': ObjectId(appointment_id)}, {'$set': {'status': 'approved'}})
        flash('Appointment accepted successfully.', 'success')
    except Exception as e:
        flash(f'Error accepting appointment: {str(e)}', 'error')
    return redirect(url_for('doctor_dashboard', doctor=doctor, csrf_token=generate_csrf()))


@app.route('/appointment/<appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    try:
        mongo.db.appointments.update_one({'_id': ObjectId(appointment_id)}, {'$set': {'status': 'cancelled'}})
        flash('Appointment cancelled successfully.', 'success')
    except Exception as e:
        flash(f'Error cancelling appointment: {str(e)}', 'error')
    return redirect(url_for('doctor_appointment'))


@app.route('/patient_profile_settings', methods=['GET', 'POST'])
def patient_profile_settings():
    patient_id = session.get('patient_id')
    if not patient_id:
        flash('Please login first.', 'error')
        return redirect(url_for('patient_login'))

    patient_oid = ObjectId(patient_id)
    patient = mongo.db.patients.find_one({'_id': patient_oid})

    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('patient_login'))

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        # Handle image upload similarly as done for doctors, adjust the fields accordingly
        image_url = None
        if 'image' in request.files and request.files['image']:
            image_to_upload = request.files['image']
            result = cloudinary.uploader.upload(image_to_upload, resource_type='image')
            image_url = result.get('secure_url')

        # Prepare the update data, ensure to capture all form inputs correctly
        update_data = {
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'date_of_birth': data.get('date_of_birth'),
            'gender': data.get('gender'),
            'blood_group': data.get('blood_group'),
            'email': data.get('email'),
            'phone_number': data.get('phone'),  # Ensure consistency in your naming convention
            'address': {
                "street": data.get('address_street'),
                "city": data.get('address_city'),
                "country": data.get('address_country'),
                "postcode": data.get('address_postcode'),
            },
            'image_url': image_url  # Ensure this is only updated if a new image is uploaded
        }

        # Only include 'image_url' in the update if a new image was uploaded
        if image_url:
            update_data['image_url'] = image_url
        else:
            # Remove the 'image_url' key if no new image was uploaded
            update_data.pop('image_url', None)

        # Update patient profile in MongoDB
        mongo.db.patients.update_one({'_id': patient_oid}, {'$set': update_data})
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('patient_dashboard'))

    return render_template('patient/patient_profile_settings.html', patient=patient, csrf_token=generate_csrf())

