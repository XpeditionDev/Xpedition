from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, UserSettings, Itinerary, Flight, Accommodation, Activity, Destination, FlightBooking, HotelBooking
from app.main.forms import ProfileForm, SettingsForm, ItineraryForm, FlightForm, AccommodationForm, ActivityForm, AIItineraryForm, FlightSearchForm, HotelSearchForm, BookingForm
from app.utils.ai_planner import ItineraryGenerator
from app.utils.api_client import get_api_client
import os
from datetime import datetime
import json
import random
import string

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Get featured itineraries to display on the homepage
    featured_itineraries = Itinerary.query.limit(6).all()
    return render_template('home.html', title='Home', itineraries=featured_itineraries)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # Handle profile picture upload
        if form.profile_picture.data:
            filename = secure_filename(form.profile_picture.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"user_{current_user.id}{file_ext}"
            
            # Save the file
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'profile_pics')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            file_path = os.path.join(upload_folder, new_filename)
            form.profile_picture.data.save(file_path)
            
            # Update user profile picture path
            current_user.profile_picture = f"uploads/profile_pics/{new_filename}"
            
        db.session.commit()
        flash('Your profile has been updated successfully!')
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('main/profile.html', title='My Profile', form=form)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    # Ensure user has settings
    if not current_user.settings:
        settings = UserSettings(user=current_user)
        db.session.add(settings)
        db.session.commit()
    
    form = SettingsForm()
    if form.validate_on_submit():
        current_user.settings.theme = form.theme.data
        current_user.settings.font_size = form.font_size.data
        current_user.settings.notifications_enabled = form.notifications_enabled.data
        db.session.commit()
        flash('Your settings have been updated successfully!')
        return redirect(url_for('main.settings'))
    elif request.method == 'GET':
        form.theme.data = current_user.settings.theme
        form.font_size.data = current_user.settings.font_size
        form.notifications_enabled.data = current_user.settings.notifications_enabled
    
    return render_template('main/settings.html', title='My Settings', form=form)

@main_bp.route('/itineraries')
@login_required
def my_itineraries():
    itineraries = Itinerary.query.filter_by(user_id=current_user.id).all()
    return render_template('main/my_itineraries.html', title='My Itineraries', itineraries=itineraries)

@main_bp.route('/itineraries/new', methods=['GET', 'POST'])
@login_required
def create_itinerary():
    form = ItineraryForm()
    if form.validate_on_submit():
        itinerary = Itinerary(
            user_id=current_user.id,
            name=form.name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            total_budget=form.total_budget.data
        )
        db.session.add(itinerary)
        db.session.commit()
        flash('Your itinerary has been created!')
        return redirect(url_for('main.itinerary_detail', itinerary_id=itinerary.id))
    
    return render_template('main/create_itinerary.html', title='Create Itinerary', form=form)

@main_bp.route('/itineraries/<int:itinerary_id>')
@login_required
def itinerary_detail(itinerary_id):
    itinerary = Itinerary.query.get_or_404(itinerary_id)
    # Ensure the itinerary belongs to the current user
    if itinerary.user_id != current_user.id:
        flash('You do not have permission to view this itinerary.')
        return redirect(url_for('main.my_itineraries'))
    
    return render_template('main/itinerary_detail.html', title=itinerary.name, itinerary=itinerary)

@main_bp.route('/itineraries/<int:itinerary_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_itinerary(itinerary_id):
    itinerary = Itinerary.query.get_or_404(itinerary_id)
    
    # Ensure the itinerary belongs to the current user
    if itinerary.user_id != current_user.id:
        flash('You do not have permission to edit this itinerary.')
        return redirect(url_for('main.my_itineraries'))
    
    form = ItineraryForm()
    if form.validate_on_submit():
        itinerary.name = form.name.data
        itinerary.start_date = form.start_date.data
        itinerary.end_date = form.end_date.data
        itinerary.total_budget = form.total_budget.data
        db.session.commit()
        flash('Itinerary updated successfully!')
        return redirect(url_for('main.itinerary_detail', itinerary_id=itinerary.id))
    elif request.method == 'GET':
        form.name.data = itinerary.name
        form.start_date.data = itinerary.start_date
        form.end_date.data = itinerary.end_date
        form.total_budget.data = itinerary.total_budget
    
    return render_template('main/edit_itinerary.html', title=f'Edit {itinerary.name}', form=form, itinerary=itinerary)

@main_bp.route('/itineraries/<int:itinerary_id>/delete')
@login_required
def delete_itinerary(itinerary_id):
    itinerary = Itinerary.query.get_or_404(itinerary_id)
    
    # Ensure the itinerary belongs to the current user
    if itinerary.user_id != current_user.id:
        flash('You do not have permission to delete this itinerary.')
        return redirect(url_for('main.my_itineraries'))
    
    db.session.delete(itinerary)
    db.session.commit()
    flash('Itinerary deleted successfully!')
    return redirect(url_for('main.my_itineraries'))

@main_bp.route('/ai-planner', methods=['GET', 'POST'])
@login_required
def ai_planner():
    form = AIItineraryForm()
    
    if form.validate_on_submit():
        try:
            # Initialize the AI itinerary generator
            generator = ItineraryGenerator()
            
            # Generate an AI itinerary based on form inputs
            ai_itinerary = generator.generate_itinerary(
                destination=form.destination.data,
                duration_days=form.duration_days.data,
                budget=form.budget.data,
                interests_text=form.interests.data or "general sightseeing",
                age=form.age.data,
                travel_style=form.travel_style.data
            )
            
            # Save the AI-generated itinerary to the database
            itinerary_id = generator.save_itinerary_to_db(current_user.id, ai_itinerary)
            
            flash('Your AI-generated itinerary has been created successfully!')
            return redirect(url_for('main.itinerary_detail', itinerary_id=itinerary_id))
        
        except Exception as e:
            flash(f'An error occurred while generating your itinerary: {str(e)}', 'error')
            return redirect(url_for('main.ai_planner'))
    
    return render_template('main/ai_planner.html', title='AI Holiday Planner', form=form)

@main_bp.route('/itineraries/<int:itinerary_id>/add-destination', methods=['POST'])
@login_required
def add_destination(itinerary_id):
    itinerary = Itinerary.query.get_or_404(itinerary_id)
    
    # Ensure the itinerary belongs to the current user
    if itinerary.user_id != current_user.id:
        flash('You do not have permission to modify this itinerary.')
        return redirect(url_for('main.my_itineraries'))
    
    # Extract form data
    name = request.form.get('destName')
    country = request.form.get('destCountry')
    arrival_date = request.form.get('arrivalDate')
    departure_date = request.form.get('departureDate')
    description = request.form.get('destDescription')
    
    if not name or not country:
        flash('Destination name and country are required.')
        return redirect(url_for('main.itinerary_detail', itinerary_id=itinerary_id))
    
    # Create new destination
    destination = Destination(
        itinerary_id=itinerary_id,
        name=name,
        country=country,
        description=description
    )
    
    # Parse dates if provided
    if arrival_date:
        destination.arrival_date = datetime.strptime(arrival_date, '%Y-%m-%d')
    if departure_date:
        destination.departure_date = datetime.strptime(departure_date, '%Y-%m-%d')
    
    db.session.add(destination)
    db.session.commit()
    
    flash('Destination added successfully!')
    return redirect(url_for('main.itinerary_detail', itinerary_id=itinerary_id))

@main_bp.route('/flight-search', methods=['GET', 'POST'])
def flight_search():
    form = FlightSearchForm()
    flights = None
    
    if form.validate_on_submit():
        api_client = get_api_client()
        
        # Get form data
        origin = form.origin.data.upper()
        destination = form.destination.data.upper()
        departure_date = form.departure_date.data
        return_date = form.return_date.data if form.return_date.data else None
        adults = form.adults.data
        
        # Search for flights
        flights = api_client.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults
        )
        
        # Store search results in session for later use
        session['flight_search_results'] = flights
        
        # Flash appropriate message based on search results
        if flights.get('status') == 'success' and flights.get('flights'):
            flash(f'Found {len(flights["flights"])} flights matching your search criteria.', 'success')
        else:
            flash('No flights found for your search criteria. Please try different dates or destinations.', 'info')
    
    return render_template('main/flight_search.html', form=form, flights=flights)

@main_bp.route('/hotel-search', methods=['GET', 'POST'])
def hotel_search():
    form = HotelSearchForm()
    hotels = None
    
    if form.validate_on_submit():
        api_client = get_api_client()
        
        # Get form data
        city = form.city.data.upper()
        check_in_date = form.check_in_date.data
        check_out_date = form.check_out_date.data
        adults = form.adults.data
        rooms = form.rooms.data
        
        # Search for hotels
        hotels = api_client.search_hotels(
            city_code=city,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults,
            rooms=rooms
        )
        
        # Store search results in session for later use
        session['hotel_search_results'] = hotels
        
        # Flash appropriate message based on search results
        if hotels.get('status') == 'success' and hotels.get('hotels'):
            flash(f'Found {len(hotels["hotels"])} hotels matching your search criteria.', 'success')
        else:
            flash('No hotels found for your search criteria. Please try different dates or locations.', 'info')
    
    return render_template('main/hotel_search.html', form=form, hotels=hotels)

@main_bp.route('/book-flight/<flight_id>', methods=['GET', 'POST'])
@login_required
def book_flight(flight_id):
    # Retrieve flight search results from session
    flights = session.get('flight_search_results')
    if not flights or flights.get('status') != 'success':
        flash('Flight information not found. Please search for flights again.', 'warning')
        return redirect(url_for('main.flight_search'))
    
    # Find the selected flight
    selected_flight = None
    for flight in flights.get('flights', []):
        if flight.get('id') == flight_id:
            selected_flight = flight
            break
    
    if not selected_flight:
        flash('The selected flight is no longer available. Please search for flights again.', 'warning')
        return redirect(url_for('main.flight_search'))
    
    form = BookingForm()
    
    if form.validate_on_submit():
        # Generate a unique booking reference
        reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Create a new booking
        booking = FlightBooking(
            user_id=current_user.id,
            reference_number=reference,
            carrier_code=selected_flight['segments'][0]['carrierCode'],
            flight_number=selected_flight['segments'][0]['number'],
            origin=selected_flight['segments'][0]['departure']['iataCode'],
            destination=selected_flight['segments'][0]['arrival']['iataCode'],
            departure_time=datetime.strptime(
                selected_flight['segments'][0]['departure']['at'].replace('Z', ''), 
                '%Y-%m-%dT%H:%M:%S'
            ),
            arrival_time=datetime.strptime(
                selected_flight['segments'][0]['arrival']['at'].replace('Z', ''), 
                '%Y-%m-%dT%H:%M:%S'
            ),
            price=float(selected_flight['price']['total']),
            currency=selected_flight['price']['currency'],
            booking_details=json.dumps(selected_flight),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Redirect to booking confirmation page
        return redirect(url_for('main.booking_confirmation', 
                               booking_type='flight', 
                               booking_reference=reference))
    
    # Pre-fill form with user data if available
    if request.method == 'GET' and current_user.is_authenticated:
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email
    
    # Render the booking form
    return render_template('main/booking_form.html', 
                          form=form, 
                          booking_type='flight',
                          booking_details=selected_flight,
                          booking_params={'flight_id': flight_id})

@main_bp.route('/book-hotel/<hotel_id>/<offer_id>', methods=['GET', 'POST'])
@login_required
def book_hotel(hotel_id, offer_id):
    # Retrieve hotel search results from session
    hotels = session.get('hotel_search_results')
    if not hotels or hotels.get('status') != 'success':
        flash('Hotel information not found. Please search for hotels again.', 'warning')
        return redirect(url_for('main.hotel_search'))
    
    # Find the selected hotel and offer
    selected_hotel = None
    selected_offer = None
    
    for hotel in hotels.get('hotels', []):
        if hotel.get('hotel_id') == hotel_id:
            selected_hotel = hotel
            for offer in hotel.get('offers', []):
                if offer.get('id') == offer_id:
                    selected_offer = offer
                    break
            break
    
    if not selected_hotel or not selected_offer:
        flash('The selected hotel or offer is no longer available. Please search for hotels again.', 'warning')
        return redirect(url_for('main.hotel_search'))
    
    # Add the selected offer to the hotel object for template rendering
    selected_hotel['offer'] = selected_offer
    
    form = BookingForm()
    
    if form.validate_on_submit():
        # Generate a unique booking reference
        reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Create a new booking
        booking = HotelBooking(
            user_id=current_user.id,
            reference_number=reference,
            hotel_id=hotel_id,
            hotel_name=selected_hotel['name'],
            city=selected_hotel['address']['city'],
            country=selected_hotel['address']['country'],
            check_in_date=datetime.strptime(selected_offer['check_in'], '%Y-%m-%d').date(),
            check_out_date=datetime.strptime(selected_offer['check_out'], '%Y-%m-%d').date(),
            room_type=selected_offer['room_type'],
            guests=selected_offer['guests']['adults'],
            price=float(selected_offer['price']['total']),
            currency=selected_offer['price']['currency'],
            booking_details=json.dumps(selected_hotel),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            special_requests=form.special_requests.data
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Redirect to booking confirmation page
        return redirect(url_for('main.booking_confirmation', 
                               booking_type='hotel', 
                               booking_reference=reference))
    
    # Pre-fill form with user data if available
    if request.method == 'GET' and current_user.is_authenticated:
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email
    
    # Render the booking form
    return render_template('main/booking_form.html', 
                          form=form, 
                          booking_type='hotel',
                          booking_details=selected_hotel,
                          booking_params={'hotel_id': hotel_id, 'offer_id': offer_id})

@main_bp.route('/booking-confirmation/<booking_type>/<booking_reference>')
@login_required
def booking_confirmation(booking_type, booking_reference):
    booking = None
    booking_details = None
    email = None
    
    if booking_type == 'flight':
        booking = FlightBooking.query.filter_by(
            reference_number=booking_reference,
            user_id=current_user.id
        ).first_or_404()
        
        booking_details = json.loads(booking.booking_details)
        email = booking.email
        
    elif booking_type == 'hotel':
        booking = HotelBooking.query.filter_by(
            reference_number=booking_reference,
            user_id=current_user.id
        ).first_or_404()
        
        booking_details = json.loads(booking.booking_details)
        email = booking.email
    
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('main/booking_confirmation.html',
                          booking_type=booking_type,
                          booking_reference=booking_reference,
                          booking_details=booking_details,
                          email=email)

@main_bp.route('/my-bookings')
@login_required
def my_bookings():
    flight_bookings = FlightBooking.query.filter_by(user_id=current_user.id).order_by(FlightBooking.booking_date.desc()).all()
    hotel_bookings = HotelBooking.query.filter_by(user_id=current_user.id).order_by(HotelBooking.booking_date.desc()).all()
    
    return render_template('main/my_bookings.html',
                          flight_bookings=flight_bookings,
                          hotel_bookings=hotel_bookings)