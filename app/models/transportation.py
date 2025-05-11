from datetime import datetime


from app.extensions import db





class Transportation(db.Model):


    __tablename__ = 'transportation'


    __table_args__ = {'extend_existing': True}


    


    id = db.Column(db.Integer, primary_key=True)


    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)


    type = db.Column(db.String(50))  # taxi, bus, train, etc.


    departure_time = db.Column(db.DateTime)


    arrival_time = db.Column(db.DateTime)


    from_location = db.Column(db.String(200))


    to_location = db.Column(db.String(200))


    booking_reference = db.Column(db.String(100))


    price = db.Column(db.Float)


    currency = db.Column(db.String(3))


    details = db.Column(db.Text)


    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    


    # Fix relationship using back_populates and overlaps


    itinerary = db.relationship('Itinerary', back_populates='transportation', overlaps="transportation")


    


    def __repr__(self):


        return f'<Transportation {self.type} from {self.from_location} to {self.to_location}>' 