from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Itinerary, SavedFlight, Booking, Accommodation, Activity, Flight, Transportation, HotelBooking
from amadeus import Client, ResponseError
from app.extensions import db
import json
from datetime import datetime, timedelta
import requests
from flask import current_app
from app.utils.amadeus_helper import search_hotels, format_hotel_data, search_flights, format_flight_data
import traceback
import logging

protected_bp = Blueprint('protected', __name__)

@protected_bp.route('/search-flights', methods=['GET', 'POST'])
@login_required
def search_flights_route():
    if request.method == 'POST':
        print("\nProcessing flight search request")
        origin = request.form.get('from')
        destination = request.form.get('to')
        departure_date = request.form.get('departure_date')
        return_date = request.form.get('return_date')
        passengers = int(request.form.get('passengers', 1))

        print(f"Search parameters:")
        print(f"From: {origin} to {destination}")
        print(f"Departure: {departure_date}, Return: {return_date}")
        print(f"Passengers: {passengers}")

        # Validate inputs
        if not all([origin, destination, departure_date]):
            flash('Please fill in all required fields.', 'error')
            return render_template('flight_search.html')

        # Validate dates
        try:
            dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
            if return_date:
                ret_date = datetime.strptime(return_date, '%Y-%m-%d')
                if ret_date < dep_date:
                    flash('Return date cannot be before departure date.', 'error')
                    return render_template('flight_search.html')
        except ValueError:
            flash('Invalid date format.', 'error')
            return render_template('flight_search.html')

        try:
            flights = search_flights(origin, destination, departure_date, return_date, passengers)
            if flights:
                formatted_flights = [format_flight_data(flight) for flight in flights]
                user_itineraries = Itinerary.query.filter_by(user_id=current_user.id).all()
                return render_template('flight_search.html', 
                                    flights=flights,
                                    formatted_flights=formatted_flights,
                                    user_itineraries=user_itineraries)
            else:
                flash('No flights found for the specified criteria.', 'info')
        except Exception as e:
            print(f"Error searching flights: {str(e)}")
            print(traceback.format_exc())
            flash(f'Error searching flights: {str(e)}', 'error')
    
    # For both GET and failed POST
    return render_template('flight_search.html')

@protected_bp.route('/plan-holiday', methods=['GET', 'POST'])
@login_required
def plan_holiday():
    print("\n=== Plan Holiday Route ===")
    print(f"Current user ID: {current_user.id}")
    
    # Get existing itineraries
    user_itineraries = Itinerary.query.filter_by(user_id=current_user.id).all()
    print(f"Found {len(user_itineraries)} itineraries for user")
    for itin in user_itineraries:
        print(f"Itinerary: {itin.id} - {itin.name}")
    
    if request.method == 'POST':
        try:
            print("\nProcessing POST request")
            itinerary_name = request.form.get('itinerary_name')
            print(f"Received itinerary name: {itinerary_name}")
            
            if not itinerary_name:
                print("No itinerary name provided")
                flash('Please provide an itinerary name')
                return redirect(url_for('protected.plan_holiday'))
            
            # Create new itinerary
            new_itinerary = Itinerary(
                name=itinerary_name,
                user_id=current_user.id,
                start_date=datetime.now(),
                end_date=datetime.now()
            )
            print(f"Created itinerary object: {new_itinerary.name} for user {new_itinerary.user_id}")
            
            # Add and commit to database
            db.session.add(new_itinerary)
            db.session.commit()
            print(f"Saved itinerary to database with ID: {new_itinerary.id}")
            
            # Verify it was saved
            saved_itinerary = Itinerary.query.get(new_itinerary.id)
            print(f"Verified saved itinerary: {saved_itinerary.id} - {saved_itinerary.name}")
            
            flash('New itinerary created successfully!')
            
            # Get updated list of itineraries
            user_itineraries = Itinerary.query.filter_by(user_id=current_user.id).all()
            print(f"Now user has {len(user_itineraries)} itineraries")
            
            return render_template('plan_holiday.html', user_itineraries=user_itineraries)
            
        except Exception as e:
            print(f"Error creating itinerary: {str(e)}")
            db.session.rollback()
            flash(f'Error creating itinerary: {str(e)}')
            return redirect(url_for('protected.plan_holiday'))
    
    print("\nRendering template with itineraries")
    return render_template('plan_holiday.html', user_itineraries=user_itineraries)

@protected_bp.route('/save_flight', methods=['POST'])
@login_required
def save_flight():
    # Get and validate flight data
    flight_data_str = request.form.get('flight_data')
    if not flight_data_str:
        print("No flight data received in form")
        print("Available form fields:", list(request.form.keys()))
        return jsonify({'success': False, 'error': 'No flight data received'}), 400
    
    print("\nRaw flight data string:", flight_data_str)
    try:
        flight_data = json.loads(flight_data_str)
        print("\nParsed flight data:", json.dumps(flight_data, indent=2))
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", str(e))
        print("Problematic string:", flight_data_str)
        return jsonify({'success': False, 'error': 'Invalid flight data format'}), 400
    
    # Get itinerary ID
    itinerary_id = request.form.get('itinerary_id')
    if not itinerary_id:
        return jsonify({'success': False, 'error': 'No itinerary selected'}), 400
    
    # Handle new itinerary creation
    if itinerary_id == 'new':
        new_itinerary_name = request.form.get('new_itinerary_name', f"Trip on {datetime.now().strftime('%Y-%m-%d')}")
        
        # Create new itinerary
        new_itinerary = Itinerary(
            name=new_itinerary_name,
            user_id=current_user.id,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        db.session.add(new_itinerary)
        db.session.commit()
        
        itinerary_id = new_itinerary.id
        print(f"Created new itinerary: {new_itinerary_name} (ID: {itinerary_id})")
    
    # Verify itinerary ownership
    itinerary = Itinerary.query.get(itinerary_id)
    if not itinerary or itinerary.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Invalid itinerary ID'}), 403
    
    try:
        # Extract flight data based on structure
        if 'outbound' in flight_data:
            # New nested structure
            outbound = flight_data['outbound']
            departure_airport = outbound['departure'].get('airport', '')
            arrival_airport = outbound['arrival'].get('airport', '')
            departure_time = datetime.fromisoformat(outbound['departure']['time'].replace('Z', '+00:00'))
            arrival_time = datetime.fromisoformat(outbound['arrival']['time'].replace('Z', '+00:00'))
            duration = outbound.get('duration', '')
        else:
            # Old flat structure
            departure_airport = flight_data['departure'].get('airport', '')
            arrival_airport = flight_data['arrival'].get('airport', '')
            departure_time = datetime.fromisoformat(flight_data['departure']['time'].replace('Z', '+00:00'))
            arrival_time = datetime.fromisoformat(flight_data['arrival']['time'].replace('Z', '+00:00'))
            duration = flight_data.get('duration', '')
        
        # Extract other flight details
        airline = flight_data.get('airline', '')
        if isinstance(flight_data.get('price'), dict):
            price = flight_data['price'].get('total', 0)
        else:
            price = flight_data.get('price', 0)
        booking_reference = flight_data.get('booking_reference', '')
            
        # Create new flight
        new_flight = Flight(
            itinerary_id=itinerary_id,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            departure_time=departure_time,
            arrival_time=arrival_time,
            airline=airline,
            cost=price,
            booking_reference=booking_reference
        )
        
        db.session.add(new_flight)
        db.session.commit()
        
        print(f"Successfully saved flight {new_flight.id} to itinerary {itinerary_id}")
        
        # Redirect to the itinerary page
        return jsonify({
            'success': True, 
            'message': 'Flight saved successfully',
            'redirect': url_for('protected.view_itinerary', itinerary_id=itinerary_id)
        })
        
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        print(f"Error saving flight: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': error_msg}), 500

@protected_bp.route('/test_flight_page')
@login_required
def test_flight_page():
    """Simple test page for flight saving"""
    # Get all itineraries for the current user
    user_itineraries = Itinerary.query.filter_by(user_id=current_user.id).all()
    
    return render_template('protected/test_flight.html', 
                          user_itineraries=user_itineraries,
                          title="Test Flight Saving")

@protected_bp.route('/itinerary/<int:itinerary_id>')
@login_required
def view_itinerary(itinerary_id):
    itinerary = Itinerary.query.filter_by(id=itinerary_id, user_id=current_user.id).first_or_404()
    return render_template('itinerary_details.html', itinerary=itinerary)

@protected_bp.route('/delete-flight/<int:flight_id>', methods=['POST'])
@login_required
def delete_flight(flight_id):
    try:
        # Find the flight
        flight = Flight.query.get_or_404(flight_id)
        
        # Check if the itinerary belongs to the current user
        itinerary = Itinerary.query.get_or_404(flight.itinerary_id)
        if itinerary.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'You are not authorized to delete this flight'}), 403
        
        # Store the itinerary_id before deletion for redirect
        itinerary_id = flight.itinerary_id
        
        # Delete the flight
        db.session.delete(flight)
        db.session.commit()
        
        flash('Flight deleted successfully', 'success')
        return redirect(url_for('protected.view_itinerary', itinerary_id=itinerary_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting flight: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@protected_bp.route('/delete-accommodation/<int:accommodation_id>', methods=['POST'])
@login_required
def delete_accommodation(accommodation_id):
    try:
        accommodation = Accommodation.query.filter_by(id=accommodation_id).first_or_404()
        
        # Verify the accommodation belongs to the current user's itinerary
        itinerary = Itinerary.query.filter_by(id=accommodation.itinerary_id, user_id=current_user.id).first_or_404()
        
        db.session.delete(accommodation)
        db.session.commit()
        
        flash('Accommodation removed successfully')
        return redirect(url_for('protected.view_itinerary', itinerary_id=itinerary.id))
        
    except Exception as e:
        print(f"Error deleting accommodation: {str(e)}")
        flash('Error removing accommodation')
        return redirect(url_for('protected.view_itinerary', itinerary_id=accommodation.itinerary_id))

@protected_bp.route('/add-activity/<int:itinerary_id>', methods=['POST'])
@login_required
def add_activity(itinerary_id):
    try:
        # Verify the itinerary belongs to the current user
        itinerary = Itinerary.query.filter_by(id=itinerary_id, user_id=current_user.id).first_or_404()
        
        name = request.form.get('name')
        start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        
        if start_time > end_time:
            flash('Start time cannot be after end time')
            return redirect(url_for('protected.view_itinerary', itinerary_id=itinerary_id))
        
        activity = Activity(
            itinerary_id=itinerary_id,
            name=name,
            start_time=start_time,
            end_time=end_time
        )
        
        db.session.add(activity)
        db.session.commit()
        
        flash('Activity added successfully')
        return redirect(url_for('protected.view_itinerary', itinerary_id=itinerary_id))
        
    except Exception as e:
        print(f"Error adding activity: {str(e)}")
        flash('Error adding activity')
        return redirect(url_for('protected.view_itinerary', itinerary_id=itinerary_id))

@protected_bp.route('/delete-activity/<int:activity_id>', methods=['POST'])
@login_required
def delete_activity(activity_id):
    try:
        activity = Activity.query.filter_by(id=activity_id).first_or_404()
        
        # Verify the activity belongs to the current user's itinerary
        itinerary = Itinerary.query.filter_by(id=activity.itinerary_id, user_id=current_user.id).first_or_404()
        
        db.session.delete(activity)
        db.session.commit()
        
        flash('Activity removed successfully')
        return redirect(url_for('protected.view_itinerary', itinerary_id=itinerary.id))
        
    except Exception as e:
        print(f"Error deleting activity: {str(e)}")
        flash('Error removing activity')
        return redirect(url_for('protected.view_itinerary', itinerary_id=activity.itinerary_id))

@protected_bp.route('/search-hotels', methods=['GET', 'POST'])
@login_required
def search_hotels():
    try:
        if request.method == 'POST':
            # Get form data
            city_code = request.form.get('city')
            check_in_date = request.form.get('check_in')
            check_out_date = request.form.get('check_out')
            guests = int(request.form.get('guests', 1))
            
            # Initialize Amadeus client
            amadeus = Client(
                client_id=current_app.config['AMADEUS_CLIENT_ID'],
                client_secret=current_app.config['AMADEUS_CLIENT_SECRET']
            )
            
            # Search for hotel offers
            response = amadeus.shopping.hotel_offers.get(
                cityCode=city_code,
                checkInDate=check_in_date,
                checkOutDate=check_out_date,
                adults=guests,
                radius=5,
                radiusUnit='KM',
                paymentPolicy='NONE',
                includeClosed=False,
                bestRateOnly=True
            )
            
            # Process hotel data
            hotels = []
            for hotel_offer in response.data:
                hotel = {
                    'id': hotel_offer['hotel']['hotelId'],
                    'name': hotel_offer['hotel']['name'],
                    'address': hotel_offer['hotel']['address'].get('lines', [''])[0],
                    'city': hotel_offer['hotel']['address'].get('cityName', ''),
                    'rating': hotel_offer['hotel'].get('rating', 'N/A'),
                    'price': hotel_offer['offers'][0]['price']['total'],
                    'currency': hotel_offer['offers'][0]['price']['currency'],
                    'room_type': hotel_offer['offers'][0].get('room', {}).get('type', 'Standard Room'),
                    'amenities': hotel_offer['hotel'].get('amenities', [])
                }
                hotels.append(hotel)
            
            return render_template('hotel_search_results.html', hotels=hotels)
            
    except ResponseError as error:
        flash(f"Error searching hotels: {str(error)}")
        print(f"Amadeus API error: {str(error)}")
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}")
        print(f"Unexpected error: {str(e)}")
    
    return render_template('hotel_search.html')

@protected_bp.route('/save_hotel', methods=['POST'])
@login_required
def save_hotel():
    # Get form data
    hotel_name = request.form.get('hotel_name')
    hotel_address = request.form.get('hotel_address')
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    itinerary_id = request.form.get('itinerary_id')
    
    if not all([hotel_name, hotel_address, check_in, check_out, itinerary_id]):
        flash('Missing required information', 'error')
        return redirect(url_for('protected.search_hotels_route'))
    
    try:
        itinerary = Itinerary.query.get(itinerary_id)
        if not itinerary or itinerary.user_id != current_user.id:
            flash('Invalid itinerary selected', 'error')
            return redirect(url_for('protected.search_hotels_route'))
        
        accommodation = Accommodation(
            name=hotel_name,
            address=hotel_address,
            check_in_date=datetime.strptime(check_in, '%Y-%m-%d'),
            check_out_date=datetime.strptime(check_out, '%Y-%m-%d'),
            itinerary_id=itinerary_id
        )
        
        db.session.add(accommodation)
        db.session.commit()
        
        flash('Hotel successfully added to your itinerary!', 'success')
        return redirect(url_for('protected.view_itinerary', id=itinerary_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding hotel to itinerary: {str(e)}', 'error')
        return redirect(url_for('protected.search_hotels_route'))

@protected_bp.route('/test_itinerary')
@login_required
def test_itinerary():
    """
    Creates a test itinerary with sample flights for testing the itinerary details view
    """
    # Check if test itinerary already exists
    test_itinerary = Itinerary.query.filter_by(user_id=current_user.id, name="Test Itinerary").first()
    
    if not test_itinerary:
        # Create a new test itinerary
        test_itinerary = Itinerary(
            name="Test Itinerary",
            user_id=current_user.id,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            total_budget=1500.00
        )
        db.session.add(test_itinerary)
        db.session.commit()
        
        # Add sample flights
        flight1 = Flight(
            itinerary_id=test_itinerary.id,
            departure_airport="LHR",
            arrival_airport="JFK",
            departure_time=datetime.now() + timedelta(days=1),
            arrival_time=datetime.now() + timedelta(days=1, hours=8),
            airline="British Airways",
            flight_number="BA177",
            cost=450.00,
            booking_reference="BA12345",
            stops=0,
            duration="8h 20m"
        )
        
        flight2 = Flight(
            itinerary_id=test_itinerary.id,
            departure_airport="JFK",
            arrival_airport="LHR",
            departure_time=datetime.now() + timedelta(days=6),
            arrival_time=datetime.now() + timedelta(days=6, hours=7),
            airline="Virgin Atlantic",
            flight_number="VS26",
            cost=480.00,
            booking_reference="VS67890",
            stops=0,
            duration="7h 05m"
        )
        
        db.session.add(flight1)
        db.session.add(flight2)
        db.session.commit()
        
        flash("Test itinerary created with sample flights!")
    else:
        flash("Test itinerary already exists!")
    
    return redirect(url_for('protected.view_itinerary', itinerary_id=test_itinerary.id))

@protected_bp.route('/test-flight-search', methods=['GET'])
@login_required
def test_flight_search():
    try:
        # Test data
        origin = 'LHR'  # London Heathrow
        destination = 'JFK'  # New York JFK
        departure_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        amadeus = Client(
            client_id=current_app.config['AMADEUS_CLIENT_ID'],
            client_secret=current_app.config['AMADEUS_CLIENT_SECRET']
        )
        
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=1,
            max=5
        )
        
        # Process flight data
        flights = []
        for flight_offer in response.data:
            flight = {
                'price': {
                    'total': flight_offer['price']['total'],
                    'currency': flight_offer['price']['currency']
                },
                'outbound': {
                    'departure': {
                        'airport': flight_offer['itineraries'][0]['segments'][0]['departure']['iataCode'],
                        'time': flight_offer['itineraries'][0]['segments'][0]['departure']['at']
                    },
                    'arrival': {
                        'airport': flight_offer['itineraries'][0]['segments'][-1]['arrival']['iataCode'],
                        'time': flight_offer['itineraries'][0]['segments'][-1]['arrival']['at']
                    }
                },
                'airline': flight_offer['validatingAirlineCodes'][0],
                'booking_reference': flight_offer['id']
            }
            flights.append(flight)
        
        return render_template('test_flight_search.html', flights=flights)
        
    except ResponseError as error:
        flash(f"Error searching flights: {str(error)}")
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}")
        print(f"Error details: {str(e)}")  # For debugging
    
    return render_template('test_flight_search.html', flights=[])

@protected_bp.route('/test-hotel-api')
@login_required
def test_hotel_api():
    try:
        print("Testing hotel API connection...")
        amadeus = Client(
            client_id=current_app.config['AMADEUS_CLIENT_ID'],
            client_secret=current_app.config['AMADEUS_CLIENT_SECRET']
        )
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        day_after = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        
        print(f"Searching for hotels in London from {tomorrow} to {day_after}")
        
        response = amadeus.shopping.hotel_offers.get(
            cityCode='LON',
            checkInDate=tomorrow,
            checkOutDate=day_after,
            adults=1
        )
        
        return jsonify({
            'status': 'success',
            'message': 'API connection successful',
            'hotels_found': len(response.data)
        })
        
    except Exception as e:
        print(f"Error in test_hotel_api: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@protected_bp.route('/book-hotel/<hotel_id>', methods=['POST'])
@login_required
def book_hotel():
    try:
        hotel_data = request.get_json()
        
        booking = HotelBooking(
            user_id=current_user.id,
            hotel_id=hotel_data['hotel_id'],
            hotel_name=hotel_data['hotel_name'],
            hotel_address=hotel_data['hotel_address'],
            check_in_date=datetime.strptime(hotel_data['check_in'], '%Y-%m-%d'),
            check_out_date=datetime.strptime(hotel_data['check_out'], '%Y-%m-%d'),
            guests=hotel_data.get('guests', 1),
            price_total=float(hotel_data['price']),
            currency=hotel_data['currency']
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Hotel booked successfully!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})