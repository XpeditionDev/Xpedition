from app.extensions import db


from datetime import datetime





class Flight(db.Model):


    __tablename__ = 'flight'


    __table_args__ = {'extend_existing': True}


    


    id = db.Column(db.Integer, primary_key=True)


    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)


    departure_airport = db.Column(db.String(100), nullable=False)


    arrival_airport = db.Column(db.String(100), nullable=False)


    departure_time = db.Column(db.DateTime, nullable=False)


    arrival_time = db.Column(db.DateTime, nullable=False)


    airline = db.Column(db.String(100))


    flight_number = db.Column(db.String(20))


    cost = db.Column(db.Float)


    booking_reference = db.Column(db.String(100))


    stops = db.Column(db.Integer, default=0)


    duration = db.Column(db.String(20))


    is_connection = db.Column(db.Boolean, default=False)


    connection_group = db.Column(db.String(100))  # To group connecting flights together


    segment_order = db.Column(db.Integer, default=0)  # Order of segments in a connection


    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    


    # Fix relationship with back_populates and overlaps


    itinerary = db.relationship('Itinerary', foreign_keys=[itinerary_id], back_populates='flights', overlaps="flights")





    def __repr__(self):


        return f'<Flight {self.departure_airport} to {self.arrival_airport}>'