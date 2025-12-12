import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template, request, flash, redirect, url_for, session
from api.models import db, VehicleUser, ParkingLot, ParkingSpot, ParkingReservation
from datetime import datetime
from sqlalchemy import func


app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicle_park.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db.init_app(app)

#define route
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/user_register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        Login_name = request.form['Login_name']
        Full_Name = request.form['Full_Name']
        Email_Address = request.form['Email_Address']
        Phone_Number = request.form['Phone_Number']
        User_Password = request.form['User_Password']
        Address = request.form['Address']
        Pin_Code = request.form['Pin_Code']

        existing_user = VehicleUser.query.filter_by(Email_Address=Email_Address).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('user_register'))

        new_user = VehicleUser(
            Login_name=Login_name,
            Full_Name=Full_Name,
            Email_Address=Email_Address,
            Phone_Number=Phone_Number,
            User_Password=User_Password,
            Address=Address,
            Pin_Code=Pin_Code,
            Role='user'
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('user_login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('user_registration.html')



@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        Email_Address = request.form['Email_Address']
        User_Password = request.form['User_Password']

        user = VehicleUser.query.filter_by(Email_Address=Email_Address).first()

        if user and user.User_Password == User_Password:
            session['user_id'] = user.User_id
            session['user_role'] = user.Role
            session['user_name'] = user.Full_Name
            
            flash('Login successful!', 'success')
            
            if user.Role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('user_login.html')




@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('user_login'))
    
    user = VehicleUser.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Invalid session', 'danger')
        return redirect(url_for('user_login'))
    
    lots = ParkingLot.query.all()
    search_query = ""
    
    if request.method == 'POST':
        search_query = request.form.get('search_location', '').strip()
        if search_query:
            lots = ParkingLot.query.filter(
                (ParkingLot.Location_Name.ilike(f"%{search_query}%")) | 
                (ParkingLot.Address_name.ilike(f"%{search_query}%"))
            ).all()

    reservations = user.user_reservations
    chart_url = None
    
    if reservations:
        lot_counter = {}
        for res in reservations:
            lot_name = res.allocated_spot.belong_to_lot.Location_Name
            lot_counter[lot_name] = lot_counter.get(lot_name, 0) + 1
        
        lot_names = list(lot_counter.keys())
        lot_counts = list(lot_counter.values())
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(lot_names, lot_counts, color='skyblue')
        ax.set_title('Your Bookings by Location')
        ax.set_xlabel('Location')
        ax.set_ylabel('Bookings')
        plt.xticks(rotation=30)
        
        img = io.BytesIO()
        fig.tight_layout()
        fig.savefig(img, format='png')
        img.seek(0)
        chart_url = base64.b64encode(img.getvalue()).decode()
        plt.close(fig)
    
    return render_template('dashboard.html', user=user, lots=lots, search_query=search_query, chart_url=chart_url)





@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))


@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session:
        flash('Please log in first', 'warning')
        return redirect(url_for('user_login'))
    
    current_user = VehicleUser.query.get(session['user_id'])
    if not current_user or current_user.Role != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('user_login'))
    
    search_query = request.form.get('search_query', '')
    search_type = request.form.get('search_type', 'location')
    
    users = VehicleUser.query.all()
    lots = ParkingLot.query.all()
    spots = ParkingSpot.query.all()
    reservations = ParkingReservation.query.all()
    
    total_revenue = db.session.query(
        func.coalesce(func.sum(ParkingReservation.Total_Cost), 0)
    ).scalar()
    
    if request.method == 'POST' and search_query:
        if search_type == 'location':
            lots = ParkingLot.query.filter(
                ParkingLot.Location_Name.contains(search_query)
            ).all()
        elif search_type == 'user':
            users = VehicleUser.query.filter(
                VehicleUser.Full_Name.contains(search_query)
            ).all()
    
    return render_template('admin_dashboard.html', 
                         user=current_user,
                         users=users, 
                         lots=lots, 
                         spots=spots, 
                         reservations=reservations,
                         search_query=search_query,
                         total_revenue=total_revenue)


@app.route('/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    user_id = session.get('user_id')
    user = VehicleUser.query.get(user_id)
    if not user or user.Role != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('user_login'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == 'POST':
        try:
            lot.Location_Name = request.form['Location_Name']
            lot.Address_name = request.form['Address_name']
            lot.PRICE = int(request.form['PRICE'])
            new_max_spots = int(request.form['Maximum_Number_Spots'])
            
            if lot.PRICE <= 0:
                flash('Price must be positive', 'danger')
                return render_template('vehicle_edit_lot.html', lot=lot)
                
            if new_max_spots <= 0:
                flash('Number of spots must be positive', 'danger')
                return render_template('vehicle_edit_lot.html', lot=lot)
            
            current_spots = len(lot.available_spots)
            lot.Maximum_Number_Spots = new_max_spots
            
            if new_max_spots > current_spots:
                for i in range(current_spots + 1, new_max_spots + 1):
                    spot = ParkingSpot(
                        Lot_Id=lot.id,
                        Current_Status='A',
                        Spot_Number=i
                    )
                    db.session.add(spot)
            
            elif new_max_spots < current_spots:
                spots_to_remove = ParkingSpot.query.filter_by(
                    Lot_Id=lot.id, 
                    Current_Status='A'
                ).offset(new_max_spots).all()
                
                for spot in spots_to_remove:
                    db.session.delete(spot)
            
            db.session.commit()
            flash('Parking lot updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except ValueError:
            flash('Invalid number format', 'danger')
            return render_template('vehicle_edit_lot.html', lot=lot)
        except Exception as e:
            db.session.rollback()
            flash(f'Update failed: {str(e)}', 'danger')
    
    return render_template('vehicle_edit_lot.html', lot=lot)



@app.route('/add_lot', methods=['GET', 'POST'])
def add_lot():
    user_id = session.get('user_id')
    user = VehicleUser.query.get(user_id)
    if not user or user.Role != 'admin':
        flash("Only admin can add parking lots.", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            Location_Name = request.form['Location_Name']
            Address_name = request.form['Address_name']
            PRICE = int(request.form['PRICE'])
            Maximum_Number_Spots = int(request.form['Maximum_Number_Spots'])
            
            if PRICE <= 0:
                flash('Price must be positive', 'danger')
                return render_template('add_lot.html')
                
            if Maximum_Number_Spots <= 0:
                flash('Number of spots must be positive', 'danger')
                return render_template('add_lot.html')
            
            new_lot = ParkingLot(
                Location_Name=Location_Name,
                Address_name=Address_name,
                PRICE=PRICE,
                Maximum_Number_Spots=Maximum_Number_Spots
            )
            db.session.add(new_lot)
            db.session.flush()
            
            for i in range(1, Maximum_Number_Spots + 1):
                spot = ParkingSpot(
                    Lot_Id=new_lot.id,
                    Current_Status='A',
                    Spot_Number=i
                )
                db.session.add(spot)
            
            db.session.commit()
            flash('Parking lot and spots created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except ValueError:
            flash('Invalid number format', 'danger')
            return render_template('add_lot.html')
        except Exception as e:
            db.session.rollback()
            flash(f'Creation failed: {str(e)}', 'danger')
    
    return render_template('add_lot.html')



@app.route('/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    
    user_id = session.get('user_id')
    user = VehicleUser.query.get(user_id)
    if not user or user.Role != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('user_login'))

    occupied_spots = ParkingSpot.query.filter_by(
        Lot_Id=lot_id, 
        Current_Status='O'
    ).count()
    
    if occupied_spots > 0:
        flash("Cannot delete lot. Some spots are occupied.", "warning")
        return redirect(url_for('admin_dashboard'))

    try:
        ParkingSpot.query.filter_by(Lot_Id=lot_id).delete()
        db.session.delete(lot)
        db.session.commit()
        flash("Parking lot deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Deletion failed: {str(e)}", "danger")
    
    return redirect(url_for('admin_dashboard'))



@app.route('/reserve_spot/<int:spot_id>', methods=['POST'])
def reserve_spot(spot_id):
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('user_login'))
    
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.Current_Status != 'A':
        flash('Spot not available!', 'danger')
        return redirect(url_for('dashboard'))
    
    Vehicle_Number = request.form.get('Vehicle_Number')
    if not Vehicle_Number:
        flash('Vehicle number is required!', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        reservation = ParkingReservation(
            User_id=session['user_id'],
            Spot_Id=spot.Spot_Id,
            Vehicle_Number=Vehicle_Number,
            Entry_Time=datetime.now(),
            Exit_Time=None,
            Total_Cost=None
        )
        spot.Current_Status = 'O'
        db.session.add(reservation)
        db.session.commit()
        flash('Spot booked successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Booking failed: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))



@app.route('/add_spot', methods=['GET', 'POST'])
def add_spot():
    user_id = session.get('user_id')
    user = VehicleUser.query.get(user_id)
    if not user or user.Role != 'admin':
        flash("Only admin can add parking spots.", "danger")
        return redirect(url_for('home'))
    
    lots = ParkingLot.query.all()
    
    if request.method == 'POST':
        try:
            Lot_Id = int(request.form['Lot_Id'])
            lot = ParkingLot.query.get(Lot_Id)
            
            if not lot:
                flash("Invalid parking lot selected", "danger")
                return render_template('add_spot.html', lots=lots)
            
            existing_spots = ParkingSpot.query.filter_by(Lot_Id=Lot_Id).count()
            next_spot_number = existing_spots + 1
            
            new_spot = ParkingSpot(
                Lot_Id=Lot_Id, 
                Current_Status='A',
                Spot_Number=next_spot_number
            )
            db.session.add(new_spot)
            db.session.commit()
            flash('Parking spot added!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except ValueError:
            flash('Invalid lot ID', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to add spot: {str(e)}', 'danger')
    
    return render_template('add_spot.html', lots=lots)


@app.route('/delete_spot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    user_id = session.get('user_id')
    user = VehicleUser.query.get(user_id)
    
    if not user or user.Role != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('user_login'))
    
    if spot.Current_Status == 'O':
        flash("Cannot delete occupied spot", "warning")
        return redirect(url_for('admin_dashboard'))
    
    active_reservations = ParkingReservation.query.filter_by(
        Spot_Id=spot_id, Exit_Time=None
    ).count()
    
    if active_reservations > 0:
        flash("Cannot delete spot with active reservations", "warning")
        return redirect(url_for('admin_dashboard'))
    
    try:
        db.session.delete(spot)
        db.session.commit()
        flash("Parking spot deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Deletion failed: {str(e)}", "danger")
    
    return redirect(url_for('admin_dashboard'))



@app.route('/release_spot/<int:reservation_id>', methods=['POST'])
def release_spot(reservation_id):
    reservation = ParkingReservation.query.get_or_404(reservation_id)
    spot = ParkingSpot.query.get(reservation.Spot_Id)
    reservation.Exit_Time = datetime.now()

    entry = reservation.Entry_Time
    exit = reservation.Exit_Time
    duration_hours = max(1, int((exit - entry).total_seconds() // 3600))

    lot = ParkingLot.query.get(spot.Lot_Id)
    reservation.Total_Cost = duration_hours * lot.PRICE
    spot.Current_Status = 'A'
    db.session.commit()
    flash('Spot released!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/search_parking', methods=['GET', 'POST'])
def search_parking():
    if request.method == 'POST':
        search_location = request.form.get('search_location')
        lots = ParkingLot.query.filter(ParkingLot.Location_Name.contains(search_location)).all()
    else:
        lots = ParkingLot.query.all()
    return render_template('search_parking.html', lots=lots)

@app.route('/occupied_spot_details/<int:spot_id>')
def occupied_spot_details(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.Current_Status == 'O':
        reservation = ParkingReservation.query.filter_by(Spot_Id=spot_id, Exit_Time=None).first()
        return render_template('occupied_spot_details.html', spot=spot, reservation=reservation)
    else:
        flash('Spot is not occupied', 'info')
        return redirect(url_for('admin_dashboard'))
    
@app.route('/book_spot/<int:lot_id>')
def book_spot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    available_spots = [spot for spot in lot.available_spots if spot.Current_Status == 'A']
    return render_template('book_spot.html', lot=lot, spots=available_spots)

@app.route('/summary_charts')
def summary_charts():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('user_login'))
    
    current_user = VehicleUser.query.get(session['user_id'])
    if not current_user or current_user.Role != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('user_login'))

    users = VehicleUser.query.filter_by(Role='user').all()
    usernames = [user.Login_name for user in users]
    reservation_counts = [len(user.user_reservations) for user in users]

    fig1, ax1 = plt.subplots()
    ax1.bar(usernames, reservation_counts, color='lightblue')
    ax1.set_title('Total Reservations per User')
    ax1.set_xlabel('Users')
    ax1.set_ylabel('Reservations')
    plt.xticks(rotation=45)
    img1 = io.BytesIO()
    fig1.tight_layout()
    fig1.savefig(img1, format='png')
    img1.seek(0)
    plot_url1 = base64.b64encode(img1.getvalue()).decode()
    plt.close(fig1)

    spots = ParkingSpot.query.all()
    available_spots = sum(1 for spot in spots if spot.Current_Status == 'A')
    occupied_spots = sum(1 for spot in spots if spot.Current_Status == 'O')

    fig2, ax2 = plt.subplots()
    ax2.bar(['Available', 'Occupied'], [available_spots, occupied_spots], 
            color=['lightgreen', 'salmon'])
    ax2.set_title('Parking Spot Status')
    ax2.set_ylabel('Number of Spots')
    img2 = io.BytesIO()
    fig2.tight_layout()
    fig2.savefig(img2, format='png')
    img2.seek(0)
    plot_url2 = base64.b64encode(img2.getvalue()).decode()
    plt.close(fig2)

    lots = ParkingLot.query.all()
    lot_names = [lot.Location_Name for lot in lots]
    total_bookings = []
    
    for lot in lots:
        booking_count = 0
        for spot in lot.available_spots:
            booking_count += len(spot.spot_reservations)
        total_bookings.append(booking_count)

    fig3, ax3 = plt.subplots()
    ax3.bar(lot_names, total_bookings, color='gold')
    ax3.set_title('Bookings by Location')
    ax3.set_xlabel('Parking Locations')
    ax3.set_ylabel('Total Bookings')
    plt.xticks(rotation=45)
    img3 = io.BytesIO()
    fig3.tight_layout()
    fig3.savefig(img3, format='png')
    img3.seek(0)
    plot_url3 = base64.b64encode(img3.getvalue()).decode()
    plt.close(fig3)

    return render_template('summary.html',
                           plot_url1=plot_url1,
                           plot_url2=plot_url2,
                           plot_url3=plot_url3,
                           user=current_user)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('user_login'))
    
    user = VehicleUser.query.get(session['user_id'])
    if request.method == 'POST':
        user.Full_Name = request.form.get('Full_Name')
        user.Email_Address = request.form.get('Email_Address')
        user.Phone_Number = request.form.get('Phone_Number')
        user.Address = request.form.get('Address')
        user.Pin_Code = request.form.get('Pin_Code')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)


# Initialize database tables
with app.app_context():
    db.create_all()
