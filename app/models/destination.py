from app.extensions import db
from datetime import datetime

class Destination(db.Model):
    __tablename__ = 'destinations'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100))
    description = db.Column(db.Text)
    arrival_date = db.Column(db.DateTime)
    departure_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with Itinerary
    itinerary = db.relationship('Itinerary', backref='destinations')

    def __repr__(self):
        return f'<Destination {self.name} for Itinerary {self.itinerary_id}>' 