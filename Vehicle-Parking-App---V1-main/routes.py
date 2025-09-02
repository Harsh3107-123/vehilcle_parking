#import app from app.py
from app import app
#import render_template from flask to render HTML templates and other necessary stuf
from flask import render_template,request,flash,redirect,url_for,session
#importing models to use database models we are going to use all models
from models import *
#importing some security stuff
from werkzeug.security import generate_password_hash, check_password_hash

from functools import wraps
#to perform scalar operation
from sqlalchemy import func

from datetime import datetime



#adding thing called decorator such that it will add additional functionality in our code so that we does not need to authenticate many times 
def login_required(f):
    @wraps(f)
    #  *args — Positional Arguments
    #  **kwargs — Keyword Arguments
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login',methods=['POST'])
def login_post():
    name= request.form.get('username')
    password= request.form.get('password')
    # check if the user exist or not
    user=User.query.filter_by(username=name).first()
    if not user:
        flash("User does not exist,Please enter with correct username")
        return redirect(url_for('login'))
    
    passhash=user.passhash
    if not check_password_hash(passhash,password):
        flash("password is wrong.please enter correct password")
        return redirect(url_for('login'))
    
    # Now let us save the session id so that it can be authenciated successfully
    session['user_id']=user.id
    
    user=User.query.get(session['user_id'])
    if user.is_admin:
        return render_template('admin.html',name=name)
    parking_lots=Parking_lot.query.all()
    vehicles=len(Vehicle.query.filter_by(user_id=session['user_id']).all())
    money=0
    transactions=Transaction.query.filter_by(user_id=session['user_id']).all()
    for transaction in transactions:
        money+=transaction.total_cost      
    return render_template('home.html',name=name,parking_lots=parking_lots,money=money,vehicles=vehicles)

@app.route('/register')
def register():
    return render_template('register.html')
    
@app.route('/register',methods=['Post'])
def register_POST():
    name=request.form.get('username').strip()
    password=request.form.get('password').strip()
    confirm_password=request.form.get('confirm_password').strip()
    full_name=request.form.get('full_name')
    date_of_birth=request.form.get('date_of_birth')
    if date_of_birth:
        date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date()
    else:
        date_of_birth=None
    
    user=User.query.filter_by(username=name).first()
    if  user:
        flash("User with this name already exist,Please use unique name")
        return redirect(url_for('register'))
    
    if password!=confirm_password:
        flash("Password and confirm password are not same !!")
        return redirect(url_for('register'))
    
    if not full_name:
        full_name=None
    passhash=generate_password_hash(password)
    user=User(username=name,passhash=passhash,full_name=full_name,date_of_birth=date_of_birth)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    user_id=session['user_id']
    user=User.query.get(user_id)
    return render_template('profile.html',user=user)


@app.route('/profile',methods=['POST'])
@login_required
def profile_post():
    user_id=session['user_id']
    user=User.query.get(user_id)
    
    new_name=request.form.get('username')
    current_password=request.form.get('old_password')
    new_password=request.form.get('new_password')
    date_of_birth=request.form.get('date_of_birth')
    full_name=request.form.get('full_name')

    if not new_name or not current_password or not new_password:
        flash('Please fill out all the necessary fields')
        return redirect(url_for('profile'))
    
    if not check_password_hash(user.passhash,current_password):
        flash('Enter correct current password')
        return redirect(url_for('profile'))
    
    if user.username == new_name:
        flash("make some changes in the name please")
        return redirect(url_for('profile'))
        
    if user.username != new_name:
        user_exist=User.query.filter_by(username=new_name).first()
        if  user_exist:
            flash("Username already exists")
            return redirect(url_for('profile'))
        
        user.username=new_name
        user.passhash=generate_password_hash(new_password)
        if date_of_birth:
            user.date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        if full_name:
            user.full_name=full_name
        db.session.commit()
        
        if user.is_admin:
            return redirect(url_for('admin_'))
        return redirect(url_for('home'))
            
@app.route('/logout')
@login_required
def logout():
    
    session.pop('user_id')
    flash("You have been logged out now!!!")
    return redirect(url_for('login'))
    
@app.route('/admin')
@login_required
def admin_():
    Parking_lots=Parking_lot.query.all() 
    parking_lots = [str(lot.prime_location_name) for lot in Parking_lots]
    occupied_spots = [int(Parking_spot.query.filter_by(lot_id=lot.id, status='O').count()) for lot in Parking_lots]
    occupied_spots_number=sum(occupied_spots)
    free_spots =int(Parking_spot.query.filter_by(user_id=None,status='A').count())
    booked_spots=Parking_spot.query.count()-free_spots-occupied_spots_number
    users=len(User.query.all())
    return render_template('admin.html', parking_lots=parking_lots, occupied_spots=occupied_spots,occupied_spots_number=occupied_spots_number,free_spots=free_spots,booked_spots=booked_spots,users=users)

# decorator for admin authentication
def admin_required(f):
    @wraps(f)
    def admin_decorator(*args,**Kwargs):
        if 'user_id' not in session:
            flash('Please login first')
            return redirect(url_for('login'))
        user=User.query.get(session['user_id'])
        if not user.is_admin :
            flash("Your are not authorised to enter into admin pannel")
            return redirect(url_for('login'))
        return f(*args, **Kwargs)
    return admin_decorator



@app.route('/parking_lot/add')
@admin_required
def add_parking_lot():
    return render_template('parking_lot/add.html')
    
@app.route('/parking_lot/add',methods=['POST'])
@admin_required
def add_parking_lot_post():
    location=request.form.get('location')
    capacity=request.form.get('capacity')
    price=request.form.get('price_per_hour')
    address=request.form.get('address')
    pincode=request.form.get('pincode')
    
    if int(price)<0 or int(capacity)<0:
        flash("price and capacity cannot be less than zero")
        return redirect(url_for('add_parking_lot'))
    
    if len(pincode)!=6:
        flash("pincode is of 6 digit")
        return redirect(url_for('add_parking_lot'))
    
    parking_lot=Parking_lot.query.filter_by(prime_location_name=location).first()
    if parking_lot:
        flash("You already have parking lot here")
        return redirect(url_for('add_parking_lot'))
    
    parking_lot=Parking_lot.query.filter_by(address=address).first()
    if parking_lot:
        flash("You already have parking lot at this address")
        return redirect(url_for('add_parking_lot'))
    
    parking_lot=Parking_lot(prime_location_name=location,price=price,maximum_number_of_spots=capacity,address=address,pincode=int(pincode))
    db.session.add(parking_lot)
    db.session.commit()
    for i in range(int(capacity)):
        parking_spot=Parking_spot(lot_id=parking_lot.id,status='A')
        db.session.add(parking_spot)
    db.session.commit()
    return redirect(url_for('parking_lot'))
    
@app.route('/parking_lot')
@admin_required
def parking_lot():
    parking_lots=Parking_lot.query.all()
    return render_template('parking_lot/lot.html',parking_lots=parking_lots)

@app.route('/parking_lot/<int:lot_id>/show')
@admin_required
def parking_lot_show(lot_id):
    parking_lot=Parking_lot.query.get(lot_id)
    parking_spots=parking_lot.parking_spots
    return render_template('parking_lot/show.html',parking_spots=parking_spots,lot_id=lot_id)

@app.route('/parking_lot/<int:id>/edit')
@admin_required
def parking_lot_edit(id):
    parking_lot=Parking_lot.query.get(id)
    return render_template('parking_lot/edit.html',parking_lot=parking_lot)

@app.route('/parking_lot/<int:id>/edit', methods=['POST'])
@admin_required
def parking_lot_edit_post(id):
    parking_lot = Parking_lot.query.get(id)

    if request.form.get('location'):
        location = request.form.get('location')
        lot = Parking_lot.query.filter_by(prime_location_name=location).first()
        if lot:
            flash('Lot already exists in this location')
            return redirect(url_for('parking_lot_edit', id=id))
        parking_lot.prime_location_name = location

    if request.form.get('capacity'):
        capacity = request.form.get('capacity')
        if int(capacity) > 50 and int(capacity) < 1:
            flash("Capacity must be between 1 and 50")
            return redirect(url_for('parking_lot_edit', id=id))
        
        if parking_lot.maximum_number_of_spots>int(capacity):
            difference=parking_lot.maximum_number_of_spots-int(capacity)
            for i in range(difference):
                spots = Parking_spot.query.filter_by(lot_id=id,status='A',user_id=None).all()
                spot_id=spots[-1].id
                parking_spot=Parking_spot.query.get(spot_id)
                if parking_spot:
                    db.session.delete(parking_spot)
                else:
                    flash("The spot is occupied here therefore you cannot reduce the capacity")
                    return redirect('parking_lot')
            db.session.commit()
            
        if parking_lot.maximum_number_of_spots<int(capacity):
            difference=int(capacity)-parking_lot.maximum_number_of_spots
            for i in range(difference):
                parking_spot=Parking_spot(lot_id=id,status='A')
                db.session.add(parking_spot)
            db.session.commit()
        
        parking_lot.maximum_number_of_spots = capacity

    if request.form.get('price_per_hour'):
        price = request.form.get('price_per_hour')
        if int(price) < 0:
            flash("Price cannot be negative")
            return redirect(url_for('parking_lot_edit', id=id))
        parking_lot.price = price

    if request.form.get('address'):
        address = request.form.get('address')
        parking_lot.address = address

    if request.form.get('pincode'):
        pincode = request.form.get('pincode')
        if len(pincode) != 6 or not pincode.isdigit():
            flash("Pincode must be a 6-digit number")
            return redirect(url_for('parking_lot_edit', id=id))
        parking_lot.pincode = pincode

    db.session.commit()
    flash("Parking lot updated successfully")
    return redirect(url_for('parking_lot'))   
    

@app.route('/parking_lot/<int:id>/delete')
@admin_required
def parking_lot_delete(id):
    parking_lot=Parking_lot.query.get(id)
    paking_spots=parking_lot.parking_spots
    for parking_spot in paking_spots:
        if parking_spot.status=='O':
            flash("There are spots occupied")
            return redirect(url_for("parking_lot"))
    return render_template('parking_lot/delete.html',parking_lot=parking_lot) 

@app.route('/parking_lot/<int:id>/delete',methods=['POST'])
@admin_required
def parking_lot_delete_post(id):
    parking_lot=Parking_lot.query.get(id)
    parking_spots=parking_lot.parking_spots
    for parking_spot in parking_spots:
        if parking_spot.status=='O':
            flash("There are spots occupied")
            return redirect("parking_lot")
    db.session.delete(parking_lot)
    db.session.commit()

    return redirect(url_for('parking_lot')) 
@app.route('/<int:lot_id>/details/<int:spot_id>')
@admin_required
def details(spot_id,lot_id):
    booking=Booking.query.filter_by(spot_id=spot_id,status='B').first()
    vehicle=Vehicle.query.get(booking.vehicle_id)
    user=User.query.get(booking.user_id )
    
    return render_template('parking_spot/details.html',user=user,vehicle=vehicle)

@app.route('/user_details')
@admin_required
def user_details():
    users=User.query.all()
    return render_template('user_details.html',users=users)

@app.route('/parking_records')
@admin_required
def parking_records():
    bookings=Booking.query.all()
    return render_template('parking_records.html',bookings=bookings)
#----User
@app.route('/home')
@login_required
def home():
    parking_lots=Parking_lot.query.all()
    vehicles=len(Vehicle.query.filter_by(user_id=session['user_id']).all())
    money=0
    transactions=Transaction.query.filter_by(user_id=session['user_id']).all()
    for transaction in transactions:
        money+=transaction.total_cost      
    user=User.query.get(session['user_id'])
    name=user.username
    return render_template('home.html',name=name,parking_lots=parking_lots,money=money,vehicles=vehicles,user=user)

@app.route('/user/parking_lot')
@login_required
def user_parking_lot():
    parking_lots=Parking_lot.query.all()
    return render_template('user/parking_lot.html',parking_lots=parking_lots)

@app.route('/user/parking_lot/<int:lot_id>/book_spot',methods=['POST'])
@login_required
def book_parking_spot(lot_id):
    parking_spot=Parking_spot.query.filter_by(lot_id=lot_id,status='A',user_id=None).first()
    spot_id=parking_spot.id
    return render_template("/user/spot_info.html",lot_id=lot_id,spot_id=spot_id,user_id=session['user_id'])
    
    
@app.route("/<int:lot_id>/book_spot/<int:spot_id>", methods=['POST'])
@login_required
def spot_info_post( lot_id, spot_id):
    vehicle_number = request.form.get('vehicle_no')
    vehicle_type = request.form.get('vehicle_type')
    user_id= session['user_id']

    vehicle = Vehicle.query.filter_by(vehicle_number=vehicle_number).first()

    if vehicle and vehicle.user_id != user_id:
        flash("A vehicle with this number is already registered by another user.")
        return redirect(url_for('user_parking_lot'))

    if vehicle and vehicle.user_id == user_id:
        bookings = vehicle.bookings
        for booking in bookings:
            if booking.vehicle_id == vehicle.id and booking.status == 'B':
                flash("This vehicle has already booked a spot.")
                return redirect(url_for('user_parking_lot'))
            elif booking.vehicle_id == vehicle.id and booking.status == 'H':
                parking_spot = Parking_spot.query.filter_by(id=spot_id, lot_id=lot_id).first()
                if not parking_spot:
                    flash("Parking spot not found.")
                    return redirect(url_for('user_parking_lot'))
                parking_spot.user_id = user_id
                booking = Booking(
                    vehicle_id=vehicle.id,
                    user_id=user_id,
                    spot_id=spot_id,
                    start_time=datetime.now(),
                    status='B'
                )
                db.session.add(booking)
                db.session.commit()
                flash("Spot rebooked successfully.")
                return redirect(url_for('bookings'))

    vehicle = Vehicle(
        user_id=user_id,
        vehicle_number=vehicle_number,
        vehicle_type=vehicle_type
    )
    db.session.add(vehicle)
    db.session.commit()

    parking_spot = Parking_spot.query.filter_by(id=spot_id, lot_id=lot_id).first()
    if not parking_spot:
        flash("Invalid parking spot.")
        return redirect(url_for('book_parking_spot', lot_id=lot_id))

    parking_spot.user_id = user_id
    booking = Booking(
        vehicle_id=vehicle.id,
        user_id=user_id,
        spot_id=spot_id,
        start_time=datetime.now(),
        status='B'
    )
    db.session.add(booking)
    db.session.commit()

    flash("Booking Successful")
    return redirect(url_for('bookings', spot_id=spot_id))

@app.route("/bookings")
@login_required
def bookings():
    user_id=session['user_id']
    bookings=Parking_spot.query.filter_by(user_id=user_id)
    return render_template('user/bookings.html',bookings=bookings,user_id=user_id)
    
@app.route("/<int:lot_id>/<int:spot_id>/Parkin",methods=['POST'])
@login_required
def parkin(spot_id,lot_id):
    parking_spot = Parking_spot.query.filter_by(id=spot_id, lot_id=lot_id).first()
    parking_spot.parking_timestamp=datetime.now()
    booking=Booking.query.filter_by(spot_id=spot_id ,status='B').first()
    booking.parkin_time=parking_spot.parking_timestamp
    parking_spot.status='O'
    db.session.commit()
    return redirect(url_for('bookings'))
    
@app.route("/<int:lot_id>/<int:spot_id>/Parkout",methods=['POST'])
@login_required
def parkout(spot_id,lot_id):
    parking_spot = Parking_spot.query.filter_by(id=spot_id, lot_id=lot_id).first()
    parking_spot.leaving_timestamp=datetime.now()
    booking=Booking.query.filter_by(spot_id=spot_id ,status='B').first()
    booking.parkout_time=parking_spot.leaving_timestamp
    db.session.commit()
    return redirect(url_for('transaction',spot_id=spot_id))

@app.route('/<int:spot_id>/transaction')
@login_required
def transaction(spot_id):
    user_id=session['user_id']
    parking_spot=Parking_spot.query.get(spot_id)
    parking_spot.status='A'
    parking_spot.user_id=None
    parking_spot.parking_timestamp=None
    parking_spot.leaving_timestamp=None
    db.session.commit()
    booking=Booking.query.filter_by(spot_id=spot_id ,status='B').first()
    time_diff=booking.parkout_time-booking.start_time 
    hours=time_diff.total_seconds()/3600
    hours = max(1, round(hours,2)) 
    parking_lot=Parking_lot.query.get(parking_spot.lot_id)
    total_cost=round(parking_lot.price*hours)
    transaction=Transaction(user_id=user_id,spot_id=spot_id,datetime=datetime.now(),total_cost=total_cost)
    booking.status='H'
    db.session.add(transaction)
    db.session.commit()
    return render_template('user/transaction.html',spot_id=spot_id,transaction=transaction)

    
@app.route('/transaction_complete',methods=['POST'])
@login_required
def transaction_post():
    flash('payment Successful')
    return redirect(url_for('home'))

@app.route('/transaction_history')
@login_required
def transaction_history():
    transactions=Transaction.query.filter_by(user_id=session['user_id']).all()
    return render_template('user/transaction_history.html',transactions=transactions)

@app.route("/booking_history")
@login_required
def booking_history():
    
    user_id=session['user_id']
    bookings=Booking.query.filter_by(user_id=user_id,status='H').all()
    return render_template('user/booking_history.html',bookings=bookings)





    