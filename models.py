
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
class VehicleUser(db.Model):
    __tablename__ = "VehicleUser"
    User_id = db.Column(db.Integer , primary_key = True)
    Login_name = db.Column(db.String , unique = True , nullable = False)
    Full_Name = db.Column(db.String ,nullable =False )
    Email_Address = db.Column(db.String , unique = True , nullable = False)
    User_Password = db.Column(db.String ,nullable = False)
    Phone_Number = db.Column(db.String , nullable = False)
    Role = db.Column(db.String ,default="user")
    Address = db.Column(db.String, nullable=False)
    Pin_Code = db.Column(db.String, nullable=False)
    user_reservations = db.relationship("ParkingReservation" , backref ='customer_booking' , cascade ="all, delete")

class ParkingLot(db.Model):
    __tablename__ = "ParkingLot"
    id = db.Column(db.Integer , primary_key=True)
    Location_Name = db.Column(db.String , nullable = False)
    Address_name = db.Column(db.String , nullable = False)
    PRICE = db.Column(db.Integer , nullable = False)
    Maximum_Number_Spots = db.Column(db.Integer , nullable = False)
    available_spots = db.relationship("ParkingSpot" , backref = "belong_to_lot" , cascade = "all, delete")

class ParkingSpot(db.Model):
    __tablename__ = "ParkingSpot"
    Spot_Id = db.Column(db.Integer, primary_key=True)
    Current_Status = db.Column(db.String(1), nullable=False, default='A')  
    Lot_Id = db.Column(db.Integer , db.ForeignKey("ParkingLot.id") , nullable = False)
    Spot_Number = db.Column(db.Integer, nullable=False)
    spot_reservations = db.relationship("ParkingReservation", backref="allocated_spot", cascade="all, delete")

class ParkingReservation(db.Model):
    __tablename__ = "ParkingReservation"
    Reservation_Id = db.Column(db.Integer ,primary_key=True )
    User_id = db.Column(db.Integer,db.ForeignKey("VehicleUser.User_id"),nullable = False)
    Spot_Id = db.Column(db.Integer, db.ForeignKey("ParkingSpot.Spot_Id"), nullable=False)  # ADDED: Missing foreign key
    Vehicle_Number = db.Column(db.String, nullable=False)
    Entry_Time = db.Column(db.DateTime, nullable=True)
    Exit_Time = db.Column(db.DateTime, nullable=True)
    Total_Cost = db.Column(db.Float, nullable=True)

 
    
