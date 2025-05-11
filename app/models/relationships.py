from app.models.itinerary import Itinerary
from app.models.booking import Booking

# Set up the relationship between Itinerary and Booking
Itinerary.bookings = Itinerary.relationship('Booking', backref='itinerary', lazy=True) 