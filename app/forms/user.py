try:
    from flask_wtf import FlaskForm
    from flask_wtf.file import FileField, FileAllowed
    from flask_login import current_user
    from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, HiddenField, RadioField
    from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, URL
    from app.models.user import User
except ImportError as e:
    print(f"ImportError in forms/user.py: {e}")

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already in use. Please choose a different one.')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    
    def validate_current_password(self, field):
        if not current_user.check_password(field.data):
            raise ValidationError('Current password is incorrect')

class SettingsForm(FlaskForm):
    theme = SelectField('Theme', choices=[('light', 'Light'), ('dark', 'Dark')], validators=[DataRequired()])
    font_size = SelectField('Font Size', choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], validators=[DataRequired()])
    notifications_enabled = BooleanField('Enable Notifications')
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Changes')

class BookingForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    address = StringField('Address', validators=[DataRequired(), Length(max=100)])
    city = StringField('City', validators=[DataRequired(), Length(max=50)])
    country = StringField('Country', validators=[DataRequired(), Length(max=50)])
    special_requests = TextAreaField('Special Requests', validators=[Optional(), Length(max=500)])
    terms_agreed = BooleanField('I agree to the terms and conditions', validators=[DataRequired()]) 