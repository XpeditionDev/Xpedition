from app.extensions import db

# Import models in dependency order
from .user import User
from .itinerary import Itinerary
from .saved_flight import SavedFlight
from .booking import Booking
from .accommodation import Accommodation
from .activity import Activity
from .flight import Flight
from .transportation import Transportation
from .hotel_booking import HotelBooking
from .flight_booking import FlightBooking
from .user_settings import UserSettings  # Make sure this is included
from .destination import Destination  # Import from local file

__all__ = [
    'User',
    'Itinerary',
    'SavedFlight',
    'Booking',
    'Accommodation',
    'Activity',
    'Flight',
    'Transportation',
    'HotelBooking',
    'FlightBooking',
    'UserSettings',
    'Destination'  # Keep this in exports
]