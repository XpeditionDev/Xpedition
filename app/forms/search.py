from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange, ValidationError
from wtforms.fields import DateField
import datetime

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

class ActivitySearchForm(FlaskForm):
    location = StringField('Location (City)', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    category = StringField('Category (Optional)')
    submit = SubmitField('Search Activities')
    
    def validate_date(self, field):
        if field.data < datetime.date.today():
            raise ValidationError('Activity date cannot be in the past') 