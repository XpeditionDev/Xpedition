from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SubmitField, SelectField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional, NumberRange
from wtforms.fields import DateField
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from app.models import User
import datetime

class ItineraryForm(FlaskForm):
    name = StringField('Itinerary Name', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    total_budget = FloatField('Total Budget', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Save Itinerary')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Update Profile')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')

class SettingsForm(FlaskForm):
    theme = SelectField('Theme', choices=[
        ('light', 'Light'), 
        ('dark', 'Dark'), 
        ('custom', 'Custom')
    ])
    font_size = SelectField('Font Size', choices=[
        ('small', 'Small'), 
        ('medium', 'Medium'), 
        ('large', 'Large')
    ])
    notifications_enabled = BooleanField('Enable Notifications')
    language = SelectField('Language', choices=[
        ('en', 'English'), 
        ('fr', 'French'), 
        ('es', 'Spanish')
    ])
    submit = SubmitField('Save Settings')

class FlightForm(FlaskForm):
    departure_airport = StringField('Departure Airport', validators=[DataRequired()])
    arrival_airport = StringField('Arrival Airport', validators=[DataRequired()])
    departure_time = DateField('Departure Time', validators=[DataRequired()])
    arrival_time = DateField('Arrival Time', validators=[DataRequired()])
    airline = StringField('Airline', validators=[Optional()])
    cost = FloatField('Cost', validators=[Optional(), NumberRange(min=0)])
    booking_reference = StringField('Booking Reference', validators=[Optional()])
    flight_number = StringField('Flight Number', validators=[Optional()])
    stops = SelectField('Stops', choices=[(0, 'Non-stop'), (1, '1 stop'), (2, '2+ stops')], coerce=int, validators=[Optional()])
    duration = StringField('Duration', validators=[Optional()])
    submit = SubmitField('Save Flight')

class AccommodationForm(FlaskForm):
    name = StringField('Accommodation Name', validators=[DataRequired()])
    address = StringField('Address', validators=[Optional()])
    check_in_date = DateField('Check-in Date', validators=[DataRequired()])
    check_out_date = DateField('Check-out Date', validators=[DataRequired()])
    cost_per_night = FloatField('Cost per Night', validators=[Optional(), NumberRange(min=0)])
    booking_reference = StringField('Booking Reference', validators=[Optional()])
    type = SelectField('Type', choices=[
        ('hotel', 'Hotel'),
        ('hostel', 'Hostel'),
        ('apartment', 'Apartment'),
        ('other', 'Other')
    ])
    submit = SubmitField('Save Accommodation')

class ActivityForm(FlaskForm):
    name = StringField('Activity Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    date = DateField('Date', validators=[DataRequired()])
    duration = StringField('Duration (minutes)', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    cost = FloatField('Cost', validators=[Optional(), NumberRange(min=0)])
    booking_reference = StringField('Booking Reference', validators=[Optional()])
    submit = SubmitField('Save Activity')

class AIItineraryForm(FlaskForm):
    destination = StringField('Destination', validators=[DataRequired()])
    duration_days = SelectField('Duration (Days)', choices=[(i, str(i)) for i in range(1, 31)], coerce=int)
    budget = FloatField('Budget', validators=[DataRequired(), NumberRange(min=0)])
    interests = TextAreaField('Interests (e.g., culture, food, adventure)', validators=[Optional()])
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=18, max=100)], default=25)
    travel_style = SelectField('Travel Style', choices=[
        ('budget', 'Budget'),
        ('standard', 'Standard'),
        ('luxury', 'Luxury')
    ], default='standard')
    submit = SubmitField('Generate Itinerary')

class FlightSearchForm(FlaskForm):
    origin = StringField('Origin (City or Airport Code)', validators=[DataRequired()])
    destination = StringField('Destination (City or Airport Code)', validators=[DataRequired()])
    departure_date = DateField('Departure Date', validators=[DataRequired()], format='%Y-%m-%d')
    return_date = DateField('Return Date (Optional)', format='%Y-%m-%d')
    adults = IntegerField('Number of Passengers', validators=[DataRequired(), NumberRange(min=1, max=9)], default=1)
    submit = SubmitField('Search Flights')

    def validate_departure_date(self, field):
        if field.data < datetime.date.today():
            raise ValidationError('Departure date cannot be in the past')
        
    def validate_return_date(self, field):
        if field.data and field.data < self.departure_date.data:
            raise ValidationError('Return date must be after departure date')

class HotelSearchForm(FlaskForm):
    city = StringField('City or Airport Code', validators=[DataRequired()])
    check_in_date = DateField('Check-in Date', validators=[DataRequired()], format='%Y-%m-%d')
    check_out_date = DateField('Check-out Date', validators=[DataRequired()], format='%Y-%m-%d')
    adults = IntegerField('Number of Adults', validators=[DataRequired(), NumberRange(min=1, max=6)], default=1)
    rooms = IntegerField('Number of Rooms', validators=[DataRequired(), NumberRange(min=1, max=3)], default=1)
    submit = SubmitField('Search Hotels')

    def validate_check_in_date(self, field):
        if field.data < datetime.date.today():
            raise ValidationError('Check-in date cannot be in the past')

    def validate_check_out_date(self, field):
        if field.data <= self.check_in_date.data:
            raise ValidationError('Check-out date must be after check-in date')
        if (field.data - self.check_in_date.data).days > 30:
            raise ValidationError('Maximum stay is 30 days')

class BookingForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    postal_code = StringField('Postal Code', validators=[DataRequired()])
    special_requests = TextAreaField('Special Requests')
    agree_terms = BooleanField('I agree to the terms and conditions', validators=[DataRequired()])
    submit = SubmitField('Confirm Booking')