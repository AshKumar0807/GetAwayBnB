import os
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Property, PropertyImage, Booking, Payment , HostExperience, ExperienceBooking
from sqlalchemy import and_
from datetime import datetime, timedelta


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Password check
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('signup'))

        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "danger")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        new_user = User(name=name, email=email, phone=phone,password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        #Fetch user from database
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            # Use Flask-Login to log in the user
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    properties = Property.query.all()
    return render_template('dash.html', properties=properties)

@app.route('/explore', methods=['GET'])
def explore_properties():
    #Get filters from the request
    city = request.args.get('city', '')
    state = request.args.get('state', '')
    min_price = request.args.get('min_price', None, type=float)
    max_price = request.args.get('max_price', None, type=float)
    max_guests = request.args.get('max_guests', None, type=int)

    query = Property.query.filter_by(isAvailable=True)  #
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if state:
        query = query.filter(Property.state.ilike(f"%{state}%"))
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if max_guests is not None:
        query = query.filter(Property.maxGuests >= max_guests)

    # Fetch the properties
    properties = query.all()

    return render_template('explore_properties.html', properties=properties)

@app.route('/property/<int:property_id>', methods=['GET', 'POST'])
def property_details(property_id):
    # Fetch the property by ID
    property_data = Property.query.get_or_404(property_id)
    images = PropertyImage.query.filter_by(propertyID=property_id).all()

    if request.method == 'POST':
        # Booking form submission
        checkin_date_str = request.form.get('checkinDate')
        checkout_date_str = request.form.get('checkoutDate')
        total_guests = int(request.form.get('totalGuests', 1))

        #string dates to Python date objects
        try:
            checkin_date = datetime.strptime(checkin_date_str, '%Y-%m-%d').date()
            checkout_date = datetime.strptime(checkout_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Please select valid check-in and check-out dates.", "danger")
            return redirect(url_for('property_details', property_id=property_id))

        # Validate dates
        if checkout_date <= checkin_date:
            flash("Checkout date must be after check-in date.", "danger")
            return redirect(url_for('property_details', property_id=property_id))

        # Check availability
        existing_bookings = Booking.query.filter(
            Booking.propertyID == property_id,
            Booking.status == 'confirmed',
            Booking.checkoutDate > checkin_date,
            Booking.checkinDate < checkout_date
        ).all()

        if existing_bookings:
            flash("The property is not available for the selected dates.", "danger")
            return redirect(url_for('property_details', property_id=property_id))

        #Calculate total price
        num_nights = (checkout_date - checkin_date).days
        total_price = num_nights * float(property_data.price)

        #new booking with 'pending' status
        new_booking = Booking(
            propertyID=property_id,
            guestID=current_user.userID,
            checkinDate=checkin_date,  #Python date object
            checkoutDate=checkout_date,  # Python date object
            totalPrice=total_price,
            status='pending'
        )
        db.session.add(new_booking)
        db.session.commit()

        flash("Booking request submitted! Please proceed to payment.", "success")
        return redirect(url_for('payment', booking_id=new_booking.bookingID))

    # Pass data to the template
    return render_template(
        'property_details.html',
        property=property_data,
        images=images
    )


@app.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def payment(booking_id):
    # Fetch booking details
    booking = Booking.query.get_or_404(booking_id)

    # Check if the booking is still valid
    if booking.status == 'canceled' or booking.isBooked:
        flash("This booking is no longer valid.", "danger")
        return redirect(url_for('explore_properties'))

    if request.method == 'POST':
        # Get payment details
        payment_method = request.form.get('paymentMethod')

        # Create payment record
        new_payment = Payment(
            bookingID=booking_id,
            amount=booking.totalPrice,
            status='completed',
            paymentMethod=payment_method
        )
        db.session.add(new_payment)

        # Update booking and property status
        booking.status = 'confirmed'
        booking.isBooked = True
        property = Property.query.get(booking.propertyID)
        property.isBooked = True  # Mark property as booked
        db.session.commit()

        flash("Payment successful! Your booking is confirmed.", "success")
        return redirect(url_for('explore_properties'))

    return render_template('payment.html', booking=booking)

@app.route('/become_host', methods=['GET', 'POST'])
@login_required
def become_host():
    if request.method == 'POST':
        # Check if the user is already a host
        if current_user.isHost:
            flash("You are already a host!", "info")
            return redirect(url_for('view_property'))

        # Update the isHost flag for the current user
        current_user.isHost = True
        db.session.commit()

        flash("Congratulations! You are now a host. Start listing your properties.", "success")
        return redirect(url_for('upload_property'))

    return render_template('host.html')


@app.route('/upload_property', methods=['GET', 'POST'])
@login_required
def upload_property():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        price = request.form['price']
        maxGuests = request.form['maxGuests']
        images = request.files.getlist('images')

        if len(images) < 2:
            flash("Please upload at least 2 images for your property.", "warning")
            return redirect(request.url)

        new_property = Property(
            hostID=current_user.userID,  #current_user.id after authentication
            title=title,
            description=description,
            address=address,
            city=city,
            state=state,
            country=country,
            price=price,
            maxGuests=maxGuests
        )

        db.session.add(new_property)
        db.session.commit()

        # Save images
        for image in images:
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                upload_folder = os.path.join(current_app.root_path, 'static/uploads')
                os.makedirs(upload_folder, exist_ok=True)  # Ensure the folder exists
                filepath = os.path.join(upload_folder, filename)
                image.save(filepath)

                image_record = PropertyImage(
                    propertyID=new_property.propertyID,
                    imageUrl=f'/static/uploads/{filename}'
                )
                db.session.add(image_record)

        db.session.commit()

        flash("Property and images uploaded successfully!", "success")
        return redirect(url_for('upload_property'))

    return render_template('upload_property.html')

@app.route('/view_property')
def view_property():
    properties = Property.query.all()
    return render_template('view_properties.html', properties=properties)

@app.route('/host_experience', methods=['GET', 'POST'])
@login_required
def host_experience():
    # Ensure the user has host privileges
    if not current_user.isHost:
        current_user.isHost = True
        db.session.commit()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        location = request.form['location']
        max_participants = request.form['maxParticipants']

        # Create a new HostExperience
        new_experience = HostExperience(
            hostID=current_user.userID,
            title=title,
            description=description,
            price=price,
            location=location,
            maxParticipants=max_participants
        )
        db.session.add(new_experience)
        db.session.commit()

        flash("Experience hosted successfully!", "success")
        return redirect(url_for('view_host_experiences'))

    return render_template('host_experience.html')


@app.route('/explore_experiences', methods=['GET'])
def explore_experiences():
    # Fetch all experiences
    experiences = HostExperience.query.all()
    return render_template('explore_experiences.html', experiences=experiences)


@app.route('/book_experience/<int:experience_id>', methods=['GET', 'POST'])
@login_required
def book_experience(experience_id):
    # Fetch the experience by ID
    experience = HostExperience.query.get_or_404(experience_id)

    if request.method == 'POST':
        date_str = request.form['date']

        # Convert string date to Python date object
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Please select a valid date.", "danger")
            return redirect(url_for('book_experience', experience_id=experience_id))

        # Check if the user has already booked on the same date
        existing_booking = ExperienceBooking.query.filter_by(
            experienceID=experience_id,
            guestID=current_user.userID,
            date=date
        ).first()

        if existing_booking:
            flash("You have already booked this experience on the selected date.", "info")
            return redirect(url_for('explore_experiences'))

        # Create a new booking
        new_booking = ExperienceBooking(
            experienceID=experience_id,
            guestID=current_user.userID,
            date=date,
            status='pending'
        )
        db.session.add(new_booking)
        db.session.commit()

        flash("Experience booking request submitted successfully!", "success")
        return redirect(url_for('explore_experiences'))

    return render_template('book_experience.html', experience=experience)


@app.route('/view_host_experiences', methods=['GET'])
@login_required
def view_host_experiences():
    
    if not current_user.isHost:
        current_user.isHost = True
        db.session.commit()

    # Fetch the experiences hosted by the current user
    experiences = HostExperience.query.filter_by(hostID=current_user.userID).all()
    return render_template('view_host_experiences.html', experiences=experiences)

@app.route('/edit_experience/<int:experience_id>', methods=['GET', 'POST'])
@login_required
def edit_experience(experience_id):
    #for the primary key field 'experienceID'
    experience = HostExperience.query.filter_by(experienceID=experience_id).first_or_404()

    #Ensure the current user is the host
    if experience.hostID != current_user.userID:
        flash("You don't have permission to edit this experience.", "danger")
        return redirect(url_for('view_host_experiences'))

    if request.method == 'POST':
        # Update the experience details from the form data
        experience.title = request.form['title']
        experience.description = request.form['description']
        experience.location = request.form['location']
        experience.price = request.form['price']
        experience.maxParticipants = request.form['maxParticipants']

        # Commit the changes to the database
        db.session.commit()
        flash("Experience updated successfully!", "success")
        return redirect(url_for('view_host_experiences'))

    return render_template('edit_experience.html', experience=experience)

# @app.route('/property/<int:property_id>', methods=['GET'])
# def property_details(property_id):
#     #Fetch the property by ID
#     property_data = Property.query.get_or_404(property_id)
#     images = PropertyImage.query.filter_by(propertyID=property_id).all()

#     # pass value in the next template
#     return render_template(
#         'property_details.html',
#         property=property_data,
#         images=images
#     )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Azure sets this
    app.run(host='0.0.0.0', port=port)