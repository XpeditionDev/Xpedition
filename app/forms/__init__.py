"""Forms module for the application."""

from app.forms.auth import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.forms.user import ProfileForm, SettingsForm, BookingForm
from app.forms.itinerary import ItineraryForm, FlightForm, AccommodationForm, ActivityForm, AiItineraryForm
from app.forms.search import FlightSearchForm, HotelSearchForm, ActivitySearchForm

__all__ = [
    'LoginForm',
    'RegistrationForm',
    'ResetPasswordRequestForm',
    'ResetPasswordForm',
    'ProfileForm',
    'SettingsForm',
    'BookingForm',
    'ItineraryForm',
    'FlightForm',
    'AccommodationForm',
    'ActivityForm',
    'AiItineraryForm',
    'FlightSearchForm',
    'HotelSearchForm',
    'ActivitySearchForm'
]