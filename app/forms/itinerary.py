from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, TextAreaField, SelectField, BooleanField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Optional, NumberRange, ValidationError, Length
from wtforms.fields import DateField
from datetime import date, timedelta

class ItineraryForm(FlaskForm):
    name = StringField('Itinerary Name', validators=[DataRequired(), Length(min=3, max=100)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    total_budget = FloatField('Total Budget', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Create Itinerary')

    def validate_end_date(form, field):
        if field.data < form.start_date.data:
            raise ValidationError('End date must be after start date')

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

class AiItineraryForm(FlaskForm):
    destination = StringField('Destination (optional)', validators=[Optional(), Length(max=100)])
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today() + timedelta(days=30))
    duration_days = IntegerField('Duration (Days)', validators=[DataRequired(), NumberRange(min=1, max=30)], default=7)
    budget = FloatField('Total Budget', validators=[DataRequired(), NumberRange(min=100)], default=1000)
    interests = StringField('Interests (comma separated)', validators=[DataRequired(), Length(min=3, max=200)], 
                          default='culture, food, sightseeing')
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=18, max=99)], default=25)
    travel_style = SelectField('Travel Style', choices=[
        ('budget', 'Budget'),
        ('mid_range', 'Mid-range'),
        ('luxury', 'Luxury')
    ], default='mid_range')
    submit = SubmitField('Generate AI Itinerary')

    def validate_start_date(form, field):
        if field.data < date.today():
            raise ValidationError('Start date must be in the future') 