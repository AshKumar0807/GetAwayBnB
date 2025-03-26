from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    userID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return str(self.userID)

class Property(db.Model):
    propertyID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hostID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    maxGuests = db.Column(db.Integer, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class Booking(db.Model):
    bookingID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    propertyID = db.Column(db.Integer, db.ForeignKey('property.propertyID'), nullable=False)
    guestID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    checkinDate = db.Column(db.Date, nullable=False)
    checkoutDate = db.Column(db.Date, nullable=False)
    totalPrice = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    paymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bookingID = db.Column(db.Integer, db.ForeignKey('booking.bookingID'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    paymentMethod = db.Column(db.String(50), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    reviewID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    propertyID = db.Column(db.Integer, db.ForeignKey('property.propertyID'), nullable=False)
    guestID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    messageID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    senderID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    receiverID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sentAt = db.Column(db.DateTime, default=datetime.utcnow)

class Wishlist(db.Model):
    wishlistID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    guestID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class WishlistProperty(db.Model):
    wishlistID = db.Column(db.Integer, db.ForeignKey('wishlist.wishlistID'), primary_key=True)
    propertyID = db.Column(db.Integer, db.ForeignKey('property.propertyID'), primary_key=True)

class HostExperience(db.Model):
    experienceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hostID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    maxParticipants = db.Column(db.Integer, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class ExperienceBooking(db.Model):
    bookingID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    experienceID = db.Column(db.Integer, db.ForeignKey('host_experience.experienceID'), nullable=False)
    guestID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)

class DamageReport(db.Model):
    reportID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bookingID = db.Column(db.Integer, db.ForeignKey('booking.bookingID'), nullable=False)
    reportedBy = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class HostLoyalty(db.Model):
    hostID = db.Column(db.Integer, db.ForeignKey('user.userID'), primary_key=True)
    points = db.Column(db.Integer, default=0)
    level = db.Column(db.String(20))
    badges = db.Column(db.Text)
    lastUpdated = db.Column(db.DateTime, default=datetime.utcnow)
