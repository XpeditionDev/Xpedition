from datetime import datetime
from app.extensions import db

class Activity(db.Model):
    __tablename__ = 'activity'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    cost = db.Column(db.Float, default=0.0)
    duration = db.Column(db.Integer, nullable=True)  # Duration in minutes
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship managed through backref from Itinerary model

    def __repr__(self):
        return f'<Activity {self.name}>' 