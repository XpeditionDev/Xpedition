from app.extensions import db


from datetime import datetime


from flask_login import UserMixin


# from werkzeug.security import generate_password_hash, check_password_hash


from passlib.hash import pbkdf2_sha256


from werkzeug.security import check_password_hash





class User(UserMixin, db.Model):


    id = db.Column(db.Integer, primary_key=True)


    username = db.Column(db.String(64), unique=True, nullable=False)


    email = db.Column(db.String(120), unique=True, nullable=False)


    password_hash = db.Column(db.String(128), nullable=False)


    profile_picture = db.Column(db.String(200), default='default-profile.jpg')


    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    # Relationships


    settings = db.relationship('UserSettings', back_populates='user', uselist=False, cascade='all, delete-orphan')


    itineraries = db.relationship('Itinerary', back_populates='user', lazy=True)


    flight_bookings = db.relationship('FlightBooking', back_populates='user', lazy=True)


    hotel_bookings = db.relationship('HotelBooking', back_populates='user', lazy=True)


    


    def set_password(self, password):


        self.password_hash = pbkdf2_sha256.hash(password)


        


    def check_password(self, password):


        # Try passlib's pbkdf2_sha256 first


        try:


            return pbkdf2_sha256.verify(password, self.password_hash)


        except ValueError:


            # If that fails, try the old Werkzeug format


            return check_password_hash(self.password_hash, password)





class Itinerary(db.Model):


    id = db.Column(db.Integer, primary_key=True)


    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    name = db.Column(db.String(100), nullable=False)


    start_date = db.Column(db.DateTime)


    end_date = db.Column(db.DateTime)


    total_budget = db.Column(db.Float)


    is_ai_generated = db.Column(db.Boolean, default=False)


    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    


    # Relationships


    user = db.relationship('User', back_populates='itineraries')


    destinations = db.relationship('Destination', back_populates='itinerary', lazy=True, cascade='all, delete-orphan')


    flights = db.relationship('Flight', back_populates='itinerary', lazy=True, cascade='all, delete-orphan')


    accommodations = db.relationship('Accommodation', back_populates='itinerary', lazy=True, cascade='all, delete-orphan')


    activities = db.relationship('Activity', back_populates='itinerary', lazy=True, cascade='all, delete-orphan')


    transportation = db.relationship('Transportation', back_populates='itinerary', lazy=True, cascade='all, delete-orphan')


    saved_flights = db.relationship('SavedFlight', back_populates='itinerary', lazy=True, cascade='all, delete-orphan')





class Destination(db.Model):


    id = db.Column(db.Integer, primary_key=True)


    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)


    name = db.Column(db.String(100), nullable=False)


    country = db.Column(db.String(100))


    description = db.Column(db.Text)


    arrival_date = db.Column(db.DateTime)


    departure_date = db.Column(db.DateTime)


    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    # Add bidirectional relationship to Itinerary


    itinerary = db.relationship('Itinerary', back_populates='destinations', overlaps="destinations")





class Flight(db.Model):


    id = db.Column(db.Integer, primary_key=True)


    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)


    departure_airport = db.Column(db.String(10), nullable=False)


    arrival_airport = db.Column(db.String(10), nullable=False)


    departure_time = db.Column(db.DateTime, nullable=False)


    arrival_time = db.Column(db.DateTime, nullable=False)


    airline = db.Column(db.String(100))


    cost = db.Column(db.Float, default=0)


    booking_reference = db.Column(db.String(20))


    flight_number = db.Column(db.String(20))


    stops = db.Column(db.Integer, default=0)


    duration = db.Column(db.String(20))


    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    is_connection = db.Column(db.Boolean, default=False)


    connection_group = db.Column(db.String(20))  # To group connecting flights together


    segment_order = db.Column(db.Integer, default=0)  # Order of segments in a connection


    


    # Add bidirectional relationship to Itinerary


    itinerary = db.relationship('Itinerary', back_populates='flights', overlaps="flights")


    


    def __repr__(self):
        return f"<Flight {self.departure_airport}-{self.arrival_airport} {self.departure_time}, Cost: £{self.cost:.2f}>"





class Accommodation(db.Model):


    id = db.Column(db.Integer, primary_key=True)


    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)


    name = db.Column(db.String(100), nullable=False)


    address = db.Column(db.String(200))


    check_in_date = db.Column(db.DateTime)


    check_out_date = db.Column(db.DateTime)


    cost_per_night = db.Column(db.Float, default=0)


    booking_reference = db.Column(db.String(50))


    type = db.Column(db.String(50))  # hotel, hostel, apartment, etc.


    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    # Add bidirectional relationship to Itinerary


    itinerary = db.relationship('Itinerary', back_populates='accommodations', overlaps="accommodations")





class Activity(db.Model):


    id = db.Column(db.Integer, primary_key=True)


    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)


    name = db.Column(db.String(100), nullable=False)


    description = db.Column(db.Text)


    date = db.Column(db.DateTime)
    
    start_time = db.Column(db.DateTime)
    
    end_time = db.Column(db.DateTime)


    duration = db.Column(db.Integer)


    location = db.Column(db.String(200))


    cost = db.Column(db.Float, default=0)


    booking_reference = db.Column(db.String(50))


    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    # Add bidirectional relationship to Itinerary


    itinerary = db.relationship('Itinerary', back_populates='activities', overlaps="activities")
    
    def __repr__(self):
        return f'<Activity {self.name} for Itinerary {self.itinerary_id}>'





class FlightBooking(db.Model):


    __tablename__ = 'flight_bookings'


    id = db.Column(db.Integer, primary_key=True)


    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    reference_number = db.Column(db.String(20), unique=True, nullable=False)


    booking_date = db.Column(db.DateTime, default=datetime.utcnow)


    total_cost = db.Column(db.Float, nullable=False)


    booking_details = db.Column(db.Text)  # JSON string containing all flight segments


    status = db.Column(db.String(20), default='confirmed')


    


    # Relationships


    user = db.relationship('User', back_populates='flight_bookings')


    flights = db.relationship('Flight', secondary='flight_booking_flights',


                            backref=db.backref('bookings', lazy=True))





# Association table for FlightBooking and Flight


flight_booking_flights = db.Table('flight_booking_flights',


    db.Column('booking_id', db.Integer, db.ForeignKey('flight_bookings.id'), primary_key=True),


    db.Column('flight_id', db.Integer, db.ForeignKey('flight.id'), primary_key=True)


)





class HotelBooking(db.Model):


    __tablename__ = 'hotel_bookings'


    id = db.Column(db.Integer, primary_key=True)


    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


    reference_number = db.Column(db.String(20), unique=True, nullable=False)


    hotel_id = db.Column(db.String(50))


    hotel_name = db.Column(db.String(100))


    city = db.Column(db.String(50))


    country = db.Column(db.String(50))


    check_in_date = db.Column(db.Date)


    check_out_date = db.Column(db.Date)


    room_type = db.Column(db.String(50))


    guests = db.Column(db.Integer)


    price = db.Column(db.Float)


    currency = db.Column(db.String(3))


    booking_details = db.Column(db.Text)


    first_name = db.Column(db.String(100))


    last_name = db.Column(db.String(100))


    email = db.Column(db.String(100))


    phone = db.Column(db.String(20))


    special_requests = db.Column(db.Text)


    booking_date = db.Column(db.DateTime, default=datetime.utcnow)


    status = db.Column(db.String(20), default='confirmed')


    


    user = db.relationship('User', back_populates='hotel_bookings')


    


    def __repr__(self):


        return f'<HotelBooking {self.reference_number} - {self.hotel_name}>' 