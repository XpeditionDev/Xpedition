from datetime import datetime
from app.extensions import db

class Booking(db.Model):
    __tablename__ = 'booking'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=True)
    booking_reference = db.Column(db.String(100), unique=True)
    booking_type = db.Column(db.String(50))  # flight, hotel, etc.
    provider = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Simplified relationships with no backrefs
    itinerary = db.relationship('Itinerary', foreign_keys=[itinerary_id])
    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<Booking {self.id}>'