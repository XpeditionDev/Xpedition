from app.extensions import db


from datetime import datetime





class SavedFlight(db.Model):


    __tablename__ = 'saved_flight'


    __table_args__ = {'extend_existing': True}


    


    id = db.Column(db.Integer, primary_key=True)


    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=True)


    flight_number = db.Column(db.String(20))


    departure_airport = db.Column(db.String(10))


    arrival_airport = db.Column(db.String(10))


    departure_time = db.Column(db.DateTime)


    arrival_time = db.Column(db.DateTime)


    airline = db.Column(db.String(100))


    price = db.Column(db.Float)


    currency = db.Column(db.String(3))


    booking_reference = db.Column(db.String(100))


    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    


    # Fix relationships with back_populates and overlaps


    user = db.relationship('User', foreign_keys=[user_id])


    itinerary = db.relationship('Itinerary', foreign_keys=[itinerary_id], back_populates='saved_flights', overlaps="saved_flights")





    def __repr__(self):


        return f'<SavedFlight {self.departure_airport} to {self.arrival_airport}>' 