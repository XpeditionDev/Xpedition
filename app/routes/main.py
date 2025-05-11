from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, session

from flask_login import login_required, current_user

from app.models import Itinerary, Activity, Accommodation, Flight, Destination, User, UserSettings

from app import db

import json

from datetime import datetime, timedelta

from app.utils.ai_planner_fixed import ItineraryGenerator

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, FloatField, SubmitField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, ValidationError, Length
from flask_wtf.file import FileField, FileAllowed
import os
import secrets



main_bp = Blueprint('main', __name__)



# Create a test form for CSRF debugging
class TestForm(FlaskForm):
    test_field = StringField('Test Field', validators=[DataRequired()])
    submit = SubmitField('Submit Form 3')



class ItineraryForm(FlaskForm):
    name = StringField('Itinerary Name', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    total_budget = FloatField('Total Budget', validators=[Optional()])
    submit = SubmitField('Create Itinerary')



class SettingsForm(FlaskForm):
    theme = SelectField('Theme', choices=[
        ('light', 'Light'), 
        ('dark', 'Dark'), 
        ('blue', 'Blue')
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



class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already registered. Please choose a different one.')



class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    
    def validate_current_password(self, current_password):
        if not current_user.check_password(current_password.data):
            raise ValidationError('Current password is incorrect.')



@main_bp.route('/')

def index():

    """Home page route"""

    return render_template('main/index.html')



@main_bp.route('/dashboard')

@login_required

def dashboard():

    """User dashboard showing their itineraries"""

    itineraries = Itinerary.query.filter_by(user_id=current_user.id).all()

    return render_template('main/dashboard.html', itineraries=itineraries)



@main_bp.route('/create-itinerary', methods=['GET', 'POST'])

@login_required

def create_itinerary():

    """Create a new itinerary"""

    form = ItineraryForm()

    

    if form.validate_on_submit():

        # Create new itinerary from form data

        itinerary = Itinerary(

            name=form.name.data,

            user_id=current_user.id,

            start_date=form.start_date.data,

            end_date=form.end_date.data,

            total_budget=form.total_budget.data or 0

        )

        

        db.session.add(itinerary)

        db.session.commit()

        

        flash('Itinerary created successfully!', 'success')

        return redirect(url_for('main.view_itinerary', itinerary_id=itinerary.id))

    

    return render_template('main/create_itinerary.html', form=form)



@main_bp.route('/itinerary/<int:itinerary_id>')

@login_required

def view_itinerary(itinerary_id):

    """View a specific itinerary"""

    itinerary = Itinerary.query.get_or_404(itinerary_id)

    

    # Ensure the user owns this itinerary

    if itinerary.user_id != current_user.id:

        flash('You do not have permission to view this itinerary.', 'danger')

        return redirect(url_for('main.dashboard'))

    

    # Ensure the itinerary has a total_budget value to prevent TypeErrors

    if itinerary.total_budget is None:

        itinerary.total_budget = 0

        db.session.commit()

    

    activities = Activity.query.filter_by(itinerary_id=itinerary_id).all()

    accommodations = Accommodation.query.filter_by(itinerary_id=itinerary_id).all()

    flights = Flight.query.filter_by(itinerary_id=itinerary_id).all()

    destinations = Destination.query.filter_by(itinerary_id=itinerary_id).all()

    

    # Ensure all activities have valid cost values

    for activity in activities:

        if activity.cost is None:

            activity.cost = 0

    

    # Ensure all accommodations have valid cost values and dates

    for accommodation in accommodations:

        if accommodation.cost_per_night is None:

            accommodation.cost_per_night = 0

    

    # Ensure all flights have valid cost values

    for flight in flights:

        if flight.cost is None:

            flight.cost = 0

    

    # Commit any changes we made to prevent None values

    if activities or accommodations or flights:

        db.session.commit()

    

    return render_template(

        'main/itinerary_detail.html',

        itinerary=itinerary,

        activities=activities,

        accommodations=accommodations,

        flights=flights,

        destinations=destinations,

        timedelta=timedelta,

        datetime=datetime

    )



@main_bp.route('/ai-itinerary', methods=['GET'])

def ai_itinerary_form():

    """Show the AI itinerary generation form"""

    return render_template('main/ai_itinerary.html')



@main_bp.route('/generate-ai-itinerary', methods=['GET', 'POST'])

def generate_ai_itinerary():

    """Generate an AI-powered itinerary based on user preferences"""

    if request.method == 'POST':

        try:

            form = request.form

            

            # Extract preferences from the form

            preferences = {

                'destination': form.get('destination'),

                'duration': int(form.get('duration', 5)),

                'budget': float(form.get('budget', 2000)),

                'interests': form.getlist('interests')

            }

            

            # Initialize the AI planner

            generator = ItineraryGenerator()

            

            # Generate the itinerary with a single preferences dictionary

            ai_itinerary = generator.generate_itinerary(preferences)

            

            # Save the itinerary to the database if user is logged in

            if current_user.is_authenticated:

                # Create a new itinerary record

                itinerary = Itinerary(

                    name=f"AI Trip to {preferences.get('destination')}",

                    user_id=current_user.id,

                    start_date=datetime.now(),

                    end_date=datetime.now() + timedelta(days=preferences.get('duration', 5)),

                    total_budget=preferences.get('budget', 2000),

                    is_ai_generated=True

                )

                db.session.add(itinerary)

                db.session.commit()

                

                # Add a flash message

                flash('AI Itinerary saved to your dashboard!', 'success')

            

            return jsonify(ai_itinerary)

        except Exception as e:

            app.logger.error(f"Error generating AI itinerary: {str(e)}")

            return jsonify({'error': 'An error occurred while creating your AI itinerary'}), 500

    

    return render_template('main/ai_itinerary.html')



@main_bp.route('/edit-itinerary/<int:itinerary_id>', methods=['GET', 'POST'])

@login_required

def edit_itinerary(itinerary_id):

    """Edit an existing itinerary"""

    itinerary = Itinerary.query.get_or_404(itinerary_id)

    

    # Ensure the user owns this itinerary

    if itinerary.user_id != current_user.id:

        flash('You do not have permission to edit this itinerary.', 'danger')

        return redirect(url_for('main.dashboard'))

    

    # Create form and populate with existing itinerary data

    form = ItineraryForm(obj=itinerary)

    

    if form.validate_on_submit():

        # Update itinerary from form data

        form.populate_obj(itinerary)

        db.session.commit()

        

        flash('Itinerary updated successfully!', 'success')

        return redirect(url_for('main.view_itinerary', itinerary_id=itinerary.id))

    

    return render_template('main/edit_itinerary.html', form=form, itinerary=itinerary)



@main_bp.route('/delete-itinerary/<int:itinerary_id>', methods=['POST'])

@login_required

def delete_itinerary(itinerary_id):

    """Delete an itinerary"""

    itinerary = Itinerary.query.get_or_404(itinerary_id)

    

    # Ensure the user owns this itinerary

    if itinerary.user_id != current_user.id:

        flash('You do not have permission to delete this itinerary.', 'danger')

        return redirect(url_for('main.dashboard'))

    

    # Delete related records

    Activity.query.filter_by(itinerary_id=itinerary_id).delete()

    Accommodation.query.filter_by(itinerary_id=itinerary_id).delete()

    Flight.query.filter_by(itinerary_id=itinerary_id).delete()

    Destination.query.filter_by(itinerary_id=itinerary_id).delete()

    

    # Delete the itinerary

    db.session.delete(itinerary)

    db.session.commit()

    

    flash('Itinerary deleted successfully!', 'success')

    return redirect(url_for('main.dashboard'))



@main_bp.route('/delete-flight/<int:flight_id>', methods=['POST'])
@login_required
def delete_flight(flight_id):
    """Delete a flight from an itinerary"""
    flight = Flight.query.get_or_404(flight_id)
    itinerary = Itinerary.query.get(flight.itinerary_id)
    
    # Check if the user owns the itinerary
    if itinerary.user_id != current_user.id:
        flash('You do not have permission to modify this itinerary.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Check if we should delete entire flight group
    delete_group = request.form.get('delete_group')
    connection_group = request.form.get('connection_group')
    
    if delete_group and connection_group:
        # Delete all flights in the same connection group
        flights_to_delete = Flight.query.filter_by(
            itinerary_id=itinerary.id,
            connection_group=connection_group
        ).all()
        
        count = 0
        for f in flights_to_delete:
            db.session.delete(f)
            count += 1
        
        db.session.commit()
        
        if count > 1:
            flash(f'Flight journey with {count} segments deleted successfully.', 'success')
        else:
            flash('Flight deleted successfully.', 'success')
    else:
        # Delete just the one flight
        db.session.delete(flight)
        db.session.commit()
        flash('Flight deleted successfully.', 'success')
    
    return redirect(url_for('main.view_itinerary', itinerary_id=itinerary.id))

@main_bp.route('/delete-accommodation/<int:accommodation_id>', methods=['POST'])
@login_required
def delete_accommodation(accommodation_id):
    """Delete an accommodation from an itinerary"""
    accommodation = Accommodation.query.get_or_404(accommodation_id)
    itinerary = Itinerary.query.get(accommodation.itinerary_id)
    
    # Check if the user owns the itinerary
    if itinerary.user_id != current_user.id:
        flash('You do not have permission to modify this itinerary.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Delete the accommodation
    db.session.delete(accommodation)
    db.session.commit()
    
    flash('Accommodation deleted successfully.', 'success')
    return redirect(url_for('main.view_itinerary', itinerary_id=itinerary.id))

@main_bp.route('/delete-activity/<int:activity_id>', methods=['POST'])
@login_required
def delete_activity(activity_id):
    """Delete an activity from an itinerary"""
    activity = Activity.query.get_or_404(activity_id)
    itinerary = Itinerary.query.get(activity.itinerary_id)
    
    # Check if the user owns the itinerary
    if itinerary.user_id != current_user.id:
        flash('You do not have permission to modify this itinerary.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Delete the activity
    db.session.delete(activity)
    db.session.commit()
    
    flash('Activity deleted successfully.', 'success')
    return redirect(url_for('main.view_itinerary', itinerary_id=itinerary.id))



# Add this route to test CSRF functionality
@main_bp.route('/test_csrf', methods=['GET', 'POST'])
def test_csrf():
    test_form = TestForm()
    form = {}
    debug_info = {
        'request_method': request.method,
        'csrf_token_in_session': session.get('csrf_token', 'Not found'),
        'csrf_token_in_template': current_app.jinja_env.globals.get('csrf_token')() if hasattr(current_app.jinja_env.globals.get('csrf_token', None), '__call__') else 'Not callable'
    }
    
    if request.method == 'POST':
        debug_info['form_data'] = request.form.to_dict()
        debug_info['csrf_token_in_form'] = request.form.get('csrf_token', 'Not found')
        
        if 'form1' in request.form:
            flash('Form 1 was submitted', 'success')
        elif 'form2' in request.form:
            flash('Form 2 was submitted', 'success')
        elif test_form.validate_on_submit():
            flash('Form 3 was submitted', 'success')
        else:
            flash(f'Form validation failed: {test_form.errors}', 'danger')
    
    return render_template('test_csrf.html', test_form=test_form, form=form, debug_info=json.dumps(debug_info, indent=2))



@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page"""
    form = SettingsForm()
    
    # If form is submitted and validated
    if form.validate_on_submit():
        # Get form data
        theme = form.theme.data
        font_size = form.font_size.data
        notifications_enabled = form.notifications_enabled.data
        language = form.language.data
        
        # Create settings if they don't exist
        if not current_user.settings:
            user_settings = UserSettings(
                user_id=current_user.id,
                theme=theme,
                font_size=font_size,
                notifications_enabled=notifications_enabled,
                language=language
            )
            db.session.add(user_settings)
        else:
            # Update existing settings
            current_user.settings.theme = theme
            current_user.settings.font_size = font_size
            current_user.settings.notifications_enabled = notifications_enabled
            current_user.settings.language = language
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('main.settings'))
    
    # Populate form with current settings if they exist
    elif request.method == 'GET' and current_user.settings:
        form.theme.data = current_user.settings.theme
        form.font_size.data = current_user.settings.font_size
        form.notifications_enabled.data = current_user.settings.notifications_enabled
        form.language.data = current_user.settings.language
    else:
        # Default values if no settings exist
        form.theme.data = 'light'
        form.font_size.data = 'medium'
        form.notifications_enabled.data = True
        form.language.data = 'en'
    
    return render_template('main/settings.html', form=form)



@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page for editing account information"""
    profile_form = ProfileForm()
    password_form = PasswordChangeForm()
    
    # Handle profile update form submission
    if profile_form.validate_on_submit() and 'update_profile' in request.form:
        try:
            # Handle username and email updates
            current_user.username = profile_form.username.data
            current_user.email = profile_form.email.data
            
            # Handle profile picture upload
            if profile_form.profile_picture.data:
                # Save profile picture
                picture_file = save_profile_picture(profile_form.profile_picture.data)
                current_user.profile_picture = picture_file
            
            db.session.commit()
            flash('Your profile has been updated successfully!', 'success')
            return redirect(url_for('main.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating your profile: {str(e)}', 'danger')
    
    # Handle password change form submission
    elif password_form.validate_on_submit() and 'change_password' in request.form:
        try:
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash('Your password has been updated successfully!', 'success')
            return redirect(url_for('main.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while changing your password: {str(e)}', 'danger')
    
    # Pre-populate form fields
    if request.method == 'GET':
        profile_form.username.data = current_user.username
        profile_form.email.data = current_user.email
    
    return render_template('main/profile.html', 
                          title='My Profile',
                          profile_form=profile_form,
                          password_form=password_form)

def save_profile_picture(form_picture):
    """Save the uploaded profile picture with a random name and return the filename"""
    # Generate random filename to avoid collisions
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(form_picture.filename)
    picture_filename = random_hex + file_ext
    
    # Create directory if it doesn't exist
    pictures_dir = os.path.join(current_app.root_path, 'static/profile_pics')
    if not os.path.exists(pictures_dir):
        os.makedirs(pictures_dir)
    
    # Save the picture
    picture_path = os.path.join(pictures_dir, picture_filename)
    form_picture.save(picture_path)
    
    return picture_filename

