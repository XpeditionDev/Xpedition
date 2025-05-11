from app import db
from datetime import datetime

class HotelBooking(db.Model):
    __tablename__ = 'hotel_bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    hotel_name = db.Column(db.String(200))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    check_in_date = db.Column(db.DateTime, nullable=False)
    check_out_date = db.Column(db.DateTime, nullable=False)
    guests = db.Column(db.Integer)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), server_default='GBP')
    status = db.Column(db.String(20), server_default='confirmed')
    booking_date = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    email = db.Column(db.String(120))
    booking_details = db.Column(db.Text)
    
    # Relationship with User model
    user = db.relationship('User', backref=db.backref('hotel_bookings', lazy=True))
    
    def __repr__(self):
        return f'<HotelBooking {self.reference_number}>' 