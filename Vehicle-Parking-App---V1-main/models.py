# we are not woking with a sql queries to directly inteereact with daatabase we are using orms to create a databasen
#  it is better to make everything more pytghonic and use python classes to represent the database tables
from app import app
from flask_sqlalchemy import SQLAlchemy
db=SQLAlchemy(app)
#importing security stuff
from werkzeug.security import generate_password_hash
#creating user model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    passhash = db.Column(db.String(256), nullable=False)
    full_name=db.Column(db.String(100),nullable=True)
    date_of_birth=db.Column(db.DateTime,nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    bookings = db.relationship('Booking', backref='user',cascade='all,delete-orphan')
    transaction = db.relationship('Transaction', backref='user',cascade='all,delete-orphan')
    vehicles = db.relationship('Vehicle', backref='user', cascade='all, delete-orphan')
    spots = db.relationship('Parking_spot', backref='user', cascade='all, delete-orphan')
    
# creating parking_lot model
class Parking_lot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(50), unique=True)
    price = db.Column(db.Float, nullable=False)
    address=db.Column(db.String(200), unique=True)
    pincode=db.Column(db.Integer, nullable=False)
    maximum_number_of_spots=db.Column(db.Integer,nullable=False)
    # It sets up a link so you can easily get all spots in a parking_lot, and from a spot, you can find its parking_lot.
    parking_spots = db.relationship('Parking_spot',backref='parking_lot',cascade="all, delete-orphan")

#create parking_spots model
class Parking_spot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id=db.Column(db.Integer,db.ForeignKey('parking_lot.id'),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=True)
    status=db.Column(db.String(1),nullable=False)
    parking_timestamp=db.Column(db.DateTime, nullable=True)
    leaving_timestamp=db.Column(db.DateTime, nullable=True)  
    
    
# creating transaction model 
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spot_id=db.Column(db.Integer,db.ForeignKey('parking_spot.id'),nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    total_cost = db.Column(db.Integer,nullable=False)

# creating vehicle model
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_number = db.Column(db.String(20),nullable=False,unique=True)
    vehicle_type = db.Column(db.String(20), nullable=False)
    bookings=db.relationship('Booking',backref='vehicle')
    
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    parkin_time=db.Column(db.DateTime,nullable=True)
    parkout_time=db.Column(db.DateTime,nullable=True)
    status=db.Column(db.String(1),nullable=False)


with app.app_context():
    #  creates all the database tables defined by your models (if they don’t already exist)
    db.create_all()
    #create admin ceredentialals
    admin=User.query.filter_by(is_admin=True).first()
    if not admin:
        password='admin@123'
        password_hash=generate_password_hash(password)
        admin=User(username='Admin',passhash=password_hash,is_admin=True)
        db.session.add(admin)
        db.session.commit()
