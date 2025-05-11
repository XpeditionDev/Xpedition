from app import db
from datetime import datetime

class FlightBooking(db.Model):
    __tablename__ = 'flight_bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    carrier_code = db.Column(db.String(10))
    flight_number = db.Column(db.String(10))
    origin = db.Column(db.String(10))
    destination = db.Column(db.String(10))
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), server_default='GBP')
    status = db.Column(db.String(20), server_default='confirmed')
    booking_date = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    email = db.Column(db.String(120))
    booking_details = db.Column(db.Text)
    
    # Relationship with User model
    user = db.relationship('User', backref=db.backref('flight_bookings', lazy=True))
    
    def __repr__(self):
        return f'<FlightBooking {self.reference_number}>' 