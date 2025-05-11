from app.extensions import db
from datetime import datetime

class Itinerary(db.Model):
    __tablename__ = 'itinerary'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_budget = db.Column(db.Float)
    is_ai_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Simplified relationships with no backrefs
    saved_flights = db.relationship('SavedFlight', lazy=True)
    flights = db.relationship('Flight', lazy=True)
    activities = db.relationship('Activity', lazy=True)
    accommodations = db.relationship('Accommodation', lazy=True, cascade='all, delete-orphan')
    transportation = db.relationship('Transportation', lazy=True)
    
    def __repr__(self):
        return f'<Itinerary {self.name}>'