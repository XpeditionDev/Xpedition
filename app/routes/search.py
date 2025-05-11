from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
from app.models import User, Itinerary, Flight, Destination, Activity, Accommodation
from app.utils.neural_recommender import NeuralRecommender
from app.utils.binary_search import binary_search_flights_by_price, binary_search_hotels_by_price
from app.utils.amadeus_api import search_flights
from app.extensions import db, csrf
from datetime import datetime, timedelta
import json
import logging
import traceback
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint and exempt it from CSRF temporarily for debugging
search_bp = Blueprint('search', __name__)

# Exempt all search routes from CSRF protection for debugging
@search_bp.before_request
def exempt_csrf():
    """Exempt the search blueprint routes from CSRF protection."""
    # We won't do anything in this function - the decorator is enough
    # as we'll manually exempt each route instead
    pass

@search_bp.route('/destinations', methods=['GET', 'POST'])
@csrf.exempt
def search_destinations():
    """Search for destination recommendations based on user preferences"""
    try:
        if request.method == 'POST':
            # Get user preferences from form or JSON data
            if request.is_json:
                data = request.get_json()
            else:
                data = {
                    'interests': request.form.getlist('interests'),
                    'budget': float(request.form.get('budget', 1000)),
                    'duration': int(request.form.get('duration', 7)),
                    'month': int(request.form.get('month', datetime.now().month)),
                }
                # Fix: Safely convert age to int only if it exists
                age_value = request.form.get('age')
                if age_value and age_value.strip():
                    data['age'] = int(age_value)
            
            # Get recommendations using neural recommender
            recommender = NeuralRecommender()
            recommendations = recommender.get_destination_recommendations(data)
            
            # Return JSON if the request was JSON, otherwise render template
            if request.is_json:
                return jsonify(recommendations)
        
            return render_template('search/destinations.html', 
                                  recommendations=recommendations,
                                  preferences=data)
        
        # GET request - show the search form
        return render_template('search/destinations.html')

    except Exception as e:
        logger.error(f"Error in destination search: {str(e)}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f"An error occurred: {str(e)}", 'danger')
        return render_template('search/destinations.html', error=str(e))

@search_bp.route('/similar-destinations/<destination>', methods=['GET'])
@csrf.exempt
def get_similar_destinations(destination):
    """Get destinations similar to the specified one"""
    try:
        recommender = NeuralRecommender()
        similar_destinations = recommender.get_similar_destinations(destination)
        return jsonify(similar_destinations)
    except Exception as e:
        logger.error(f"Error getting similar destinations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@search_bp.route('/flights', methods=['GET', 'POST'])
@csrf.exempt
def flight_search():
    """Search for flights based on user input using Amadeus API"""
    # Get user itineraries if user is logged in
    user_itineraries = None
    if current_user.is_authenticated:
        user_itineraries = Itinerary.query.filter_by(user_id=current_user.id).all()
    
    try:
        if request.method == 'POST':
            # Check if this is a flight save request
            flight_data_str = request.form.get('flight_data')
            if flight_data_str and current_user.is_authenticated:
                try:
                    # Process the save flight request
                    logger.info("Processing save flight request")
                    flight_data = json.loads(flight_data_str)
                    
                    # Get itinerary ID
                    itinerary_id = request.form.get('itinerary_id')
                    if not itinerary_id:
                        flash('No itinerary selected', 'danger')
                        return redirect(url_for('search.flight_search'))
                    
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
                        logger.info(f"Created new itinerary: {new_itinerary_name} (ID: {itinerary_id})")
                    
                    # Verify itinerary ownership
                    itinerary = Itinerary.query.get(itinerary_id)
                    if not itinerary or itinerary.user_id != current_user.id:
                        flash('Invalid itinerary ID', 'danger')
                        return redirect(url_for('search.flight_search'))
                    
                    # Extract flight data
                    try:
                        # Check if this is a multi-segment flight (e.g., connections or round trip)
                        is_multi_segment = False
                        flight_segments = []
                        
                        # Handle different data structures for flights
                        if 'itineraries' in flight_data:
                            # Handle full itinerary format with multiple segments
                            is_multi_segment = True
                            
                            for itinerary_idx, itinerary in enumerate(flight_data['itineraries']):
                                is_outbound = itinerary_idx == 0
                                connection_group = f"journey_{itinerary_idx}"
                                
                                for segment_idx, segment in enumerate(itinerary.get('segments', [])):
                                    segment_data = {
                                        'departure_airport': segment.get('departure', {}).get('airport', ''),
                                        'arrival_airport': segment.get('arrival', {}).get('airport', ''),
                                        'departure_time': segment.get('departure', {}).get('time', ''),
                                        'arrival_time': segment.get('arrival', {}).get('time', ''),
                                        'airline': segment.get('airline', ''),
                                        'flight_number': segment.get('flight_number', ''),
                                        'duration': segment.get('duration', ''),
                                        'segment_order': segment_idx,
                                        'is_connection': True,
                                        'connection_group': connection_group,
                                        'is_outbound': is_outbound
                                    }
                                    flight_segments.append(segment_data)
                            
                        elif 'details' in flight_data and 'outbound' in flight_data.get('details', {}):
                            # Handle outbound and potential return segments
                            outbound_data = {
                                'departure_airport': flight_data['departure'].get('airport', ''),
                                'arrival_airport': flight_data['arrival'].get('airport', ''),
                                'departure_time': flight_data['departure'].get('time', ''),
                                'arrival_time': flight_data['arrival'].get('time', ''),
                                'airline': flight_data.get('airline', ''),
                                'flight_number': flight_data.get('flight_number', ''),
                                'duration': flight_data.get('details', {}).get('outbound', {}).get('duration', ''),
                                'stops': flight_data.get('details', {}).get('outbound', {}).get('stops', 0),
                                'is_connection': False,
                                'segment_order': 0,
                                'connection_group': 'outbound',
                                'is_outbound': True
                            }
                            flight_segments.append(outbound_data)
                            
                            # Check if it has a return segment
                            if 'return' in flight_data.get('details', {}):
                                is_multi_segment = True
                                return_data = {
                                    'departure_airport': flight_data['details']['return'].get('departure', {}).get('airport', flight_data['arrival'].get('airport', '')),
                                    'arrival_airport': flight_data['details']['return'].get('arrival', {}).get('airport', flight_data['departure'].get('airport', '')),
                                    'departure_time': flight_data['details']['return'].get('departure', {}).get('time', ''),
                                    'arrival_time': flight_data['details']['return'].get('arrival', {}).get('time', ''),
                                    'airline': flight_data.get('airline', ''),
                                    'flight_number': flight_data.get('flight_number', ''),
                                    'duration': flight_data.get('details', {}).get('return', {}).get('duration', ''),
                                    'stops': flight_data.get('details', {}).get('return', {}).get('stops', 0),
                                    'is_connection': False,
                                    'segment_order': 0,
                                    'connection_group': 'return',
                                    'is_outbound': False
                                }
                                flight_segments.append(return_data)
                                
                        else:
                            # Simple single flight segment
                            segment_data = {
                                'departure_airport': flight_data['departure'].get('airport', ''),
                                'arrival_airport': flight_data['arrival'].get('airport', ''),
                                'departure_time': flight_data['departure'].get('time', ''),
                                'arrival_time': flight_data['arrival'].get('time', ''),
                                'airline': flight_data.get('airline', ''),
                                'flight_number': flight_data.get('flight_number', ''),
                                'duration': flight_data.get('details', {}).get('duration', ''),
                                'stops': flight_data.get('details', {}).get('stops', 0),
                                'is_connection': False,
                                'segment_order': 0,
                                'connection_group': 'single',
                                'is_outbound': True
                            }
                            flight_segments.append(segment_data)
                        
                        # Handle price extraction
                        if isinstance(flight_data.get('price'), dict):
                            price = flight_data['price'].get('total', 0)
                            currency = flight_data['price'].get('currency', 'GBP')
                        else:
                            price = flight_data.get('price', 0)
                            currency = 'GBP'
                        
                        # Ensure price is never None or invalid
                        if price is None or not isinstance(price, (int, float)):
                            price = 0
                            logger.warning(f"Invalid price found in API response, defaulting to 0")
                        
                        # Log the original API price for debugging
                        logger.info(f"API Flight Price (before conversion): {currency} {price}")
                        
                        # Apply currency conversion if needed (same as in the template)
                        if currency == 'USD':
                            # Convert USD to GBP using same conversion rate as template (0.79)
                            price = float(price) * 0.79
                            currency = 'GBP'
                            logger.info(f"Converted API Price: {currency} {price}")
                        
                        # Force price to be a positive float for database
                        price = max(0, float(price))
                        logger.info(f"Final price to save: {currency} {price}")
                        
                        # Handle price distribution across segments
                        segment_count = len(flight_segments)
                        if segment_count > 0:
                            # For multi-segment journey, distribute price properly
                            if is_multi_segment:
                                # If there are multiple segments, divide the price among them
                                segment_price = price / segment_count
                            else:
                                # If it's a single segment, use the full price
                                segment_price = price
                        else:
                            segment_price = 0
                        
                        # Save all flight segments
                        saved_flights = []
                        for segment in flight_segments:
                            # Convert ISO strings to datetime objects
                            dep_time_str = segment['departure_time']
                            arr_time_str = segment['arrival_time']
                            
                            departure_time = datetime.fromisoformat(dep_time_str.replace('Z', '+00:00')) if dep_time_str else datetime.now()
                            arrival_time = datetime.fromisoformat(arr_time_str.replace('Z', '+00:00')) if arr_time_str else departure_time + timedelta(hours=2)
                            
                            # Extract duration
                            duration = segment['duration']
                            
                            # Calculate duration in minutes if not provided
                            duration_minutes = 0
                            if not duration and departure_time and arrival_time:
                                # Calculate duration from departure and arrival times
                                duration_delta = arrival_time - departure_time
                                duration_minutes = int(duration_delta.total_seconds() / 60)
                                duration = f"PT{duration_minutes // 60}H{duration_minutes % 60}M"
                            elif duration:
                                # Try to parse the duration string if it's in a standard format
                                if duration.startswith('PT'):
                                    # Parse ISO 8601 duration format
                                    hours_match = re.search(r'(\d+)H', duration)
                                    minutes_match = re.search(r'(\d+)M', duration)
                                    hours = int(hours_match.group(1)) if hours_match else 0
                                    minutes = int(minutes_match.group(1)) if minutes_match else 0
                                    duration_minutes = hours * 60 + minutes
                                else:
                                    # Parse "Xh Ym" format
                                    parts = duration.lower().replace(' ', '').split('h')
                                    hours = int(parts[0]) if parts[0] else 0
                                    minutes = int(parts[1].replace('m', '')) if len(parts) > 1 and parts[1].replace('m', '') else 0
                                    duration_minutes = hours * 60 + minutes
                            
                            # Create new flight segment
                            new_flight = Flight(
                                itinerary_id=itinerary_id,
                                departure_airport=segment['departure_airport'],
                                arrival_airport=segment['arrival_airport'],
                                departure_time=departure_time,
                                arrival_time=arrival_time,
                                airline=segment['airline'],
                                flight_number=segment.get('flight_number', f"XP{1000 + int(itinerary_id)}"),
                                cost=segment_price,  # Set the distributed price for each segment
                                duration=duration,
                                stops=segment.get('stops', 0),
                                is_connection=segment.get('is_connection', False),
                                connection_group=segment.get('connection_group', 'single'),
                                segment_order=segment.get('segment_order', 0)
                            )
                            
                            db.session.add(new_flight)
                            saved_flights.append(new_flight)
                        
                        # Commit all flight segments
                        db.session.commit()
                        
                        # Generate a success message based on number of flights saved
                        if len(saved_flights) == 1:
                            message = f'Flight from {saved_flights[0].departure_airport} to {saved_flights[0].arrival_airport} saved to itinerary.'
                        else:
                            first_flight = saved_flights[0]
                            last_flight = saved_flights[-1]
                            message = f'Journey from {first_flight.departure_airport} to {last_flight.arrival_airport} with {len(saved_flights)} segments saved to itinerary.'
                        
                        logger.info(message)
                        flash(message, 'success')
                        return redirect(url_for('main.view_itinerary', itinerary_id=itinerary_id))
                        
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error extracting flight data: {str(e)}")
                        flash(f"Error saving flight: {str(e)}", 'danger')
                        return redirect(url_for('search.flight_search'))
                
                except json.JSONDecodeError:
                    flash('Invalid flight data format', 'danger')
                    return redirect(url_for('search.flight_search'))
                except Exception as e:
                    logger.error(f"Error saving flight: {str(e)}")
                    flash(f"Error saving flight: {str(e)}", 'danger')
                    return redirect(url_for('search.flight_search'))
            
            # Normal flight search processing
            # Get search parameters from form
            origin = request.form.get('from', '').strip().upper()
            destination = request.form.get('to', '').strip().upper()
            departure_date = request.form.get('departure_date')
            return_date = request.form.get('return_date')
            passengers = int(request.form.get('passengers', 1))
            
            # Validate inputs
            if not origin or len(origin) != 3:
                flash('Please enter a valid origin airport code (3 letters)', 'danger')
                return render_template('flight_search.html', user_itineraries=user_itineraries)
            
            if not destination or len(destination) != 3:
                flash('Please enter a valid destination airport code (3 letters)', 'danger')
                return render_template('flight_search.html', user_itineraries=user_itineraries)
            
            if not departure_date:
                flash('Please enter a departure date', 'danger')
                return render_template('flight_search.html', user_itineraries=user_itineraries)
            
            try:
                # Convert date strings to date objects (needed for the API)
                departure_datetime = datetime.strptime(departure_date, '%Y-%m-%d')
                return_datetime = None
                if return_date:
                    return_datetime = datetime.strptime(return_date, '%Y-%m-%d')
                
                # Search for flights using Amadeus API
                formatted_flights, api_response = search_flights(
                    origin=origin, 
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    adults=passengers
                )
                
                # Handle potential API errors
                if 'error' in api_response:
                    logger.warning(f"Amadeus API error: {api_response['error']}")
                    flash(f"Couldn't retrieve flights from Amadeus: {api_response['error']}", 'warning')
                    
                    # Fallback to database or mock data
                    logger.info("Falling back to database search")
                    db_flights = Flight.query.filter(
                        Flight.departure_airport == origin,
                        Flight.arrival_airport == destination
                    ).all()
                    
                    # Format database flights if any found
                    if db_flights:
                        for flight in db_flights:
                            formatted_flight = {
                                'airline': flight.airline,
                                'departure': {
                                    'airport': flight.departure_airport,
                                    'time': flight.departure_time.isoformat()
                                },
                                'arrival': {
                                    'airport': flight.arrival_airport,
                                    'time': flight.arrival_time.isoformat()
                                },
                                'details': {
                                    'duration': flight.duration,
                                    'stops': flight.stops,
                                    'outbound': {
                                        'duration': flight.duration,
                                        'stops': flight.stops
                                    }
                                },
                                'price': {
                                    'total': flight.cost,
                                    'currency': 'USD',
                                    'display': f'${flight.cost}'
                                },
                                'is_round_trip': False
                            }
                            formatted_flights.append(formatted_flight)
                
                # If no flights found (from API or database), use mock data
                if not formatted_flights:
                    # Create some mock flights for demo purposes
                    logger.info("No flights found, using mock data")
                    formatted_flights = [
                        {
                            'airline': 'Demo Airlines',
                            'departure': {
                                'airport': origin,
                                'time': f"{departure_date}T08:00:00+00:00"
                            },
                            'arrival': {
                                'airport': destination,
                                'time': f"{departure_date}T10:00:00+00:00"
                            },
                            'details': {
                                'duration': '2h 00m',
                                'stops': 0,
                                'outbound': {
                                    'duration': '2h 00m',
                                    'stops': 0
                                }
                            },
                            'price': {
                                'total': 299.99,
                                'currency': 'USD',
                                'display': '$299.99'
                            },
                            'is_round_trip': False
                        },
                        {
                            'airline': 'Budget Air',
                            'departure': {
                                'airport': origin,
                                'time': f"{departure_date}T12:30:00+00:00"
                            },
                            'arrival': {
                                'airport': destination,
                                'time': f"{departure_date}T14:45:00+00:00"
                            },
                            'details': {
                                'duration': '2h 15m',
                                'stops': 0,
                                'outbound': {
                                    'duration': '2h 15m',
                                    'stops': 0
                                }
                            },
                            'price': {
                                'total': 249.99,
                                'currency': 'USD',
                                'display': '$249.99'
                            },
                            'is_round_trip': False
                        }
                    ]
                
                return render_template('flight_search.html',
                                     user_itineraries=user_itineraries,
                                     formatted_flights=formatted_flights,
                                     search_params={
                                         'from': origin,
                                         'to': destination,
                                         'departure_date': departure_date,
                                         'return_date': return_date,
                                         'passengers': passengers
                                     })
                
            except Exception as e:
                logger.error(f"Error searching flights: {str(e)}")
                flash(f"An error occurred while searching for flights: {str(e)}", 'danger')
                return render_template('flight_search.html', user_itineraries=user_itineraries, error=str(e))
        
        # GET request - show search form
        return render_template('flight_search.html', user_itineraries=user_itineraries)
    
    except Exception as e:
        logger.error(f"Error in flight search: {str(e)}")
        flash(f"An error occurred: {str(e)}", 'danger')
        return render_template('flight_search.html', user_itineraries=user_itineraries)

@search_bp.route('/flight-price', methods=['GET', 'POST'])
@csrf.exempt
def flight_price_search():
    """Search for flights by price using binary search algorithm"""
    try:
        if request.method == 'POST':
            # Get search parameters
            if request.is_json:
                data = request.get_json()
                target_price = float(data.get('price', 500))
                tolerance = float(data.get('tolerance', 100))
                origin = data.get('from')
                destination = data.get('to')
                departure_date = data.get('departure_date')
                return_date = data.get('return_date')
                adaptive_tolerance = data.get('adaptive_tolerance', False)
            else:
                target_price = float(request.form.get('price', 500))
                tolerance = float(request.form.get('tolerance', 100))
                origin = request.form.get('from')
                destination = request.form.get('to')
                departure_date = request.form.get('departure_date')
                return_date = request.form.get('return_date')
                adaptive_tolerance = request.form.get('adaptive_tolerance') == 'on'
            
            # Log the search parameters
            destination_info = f"destination={destination}" if destination else "destination=Any (searching all destinations)"
            logger.info(f"Flight price search: target=£{target_price}, tolerance=£{tolerance}, origin={origin}, {destination_info}, departure_date={departure_date}")
            
            # Perform binary search
            matching_flights, performance_data = binary_search_flights_by_price(
                target_price=target_price,
                tolerance=tolerance,
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                adaptive_tolerance=adaptive_tolerance,
                collect_vis_data=True
            )
            
            # Format the results
            results = []
            for flight in matching_flights:
                results.append({
                    'id': flight.id,
                    'airline': flight.airline,
                    'departure_airport': flight.departure_airport,
                    'arrival_airport': flight.arrival_airport,
                    'departure_time': flight.departure_time.isoformat(),
                    'arrival_time': flight.arrival_time.isoformat(),
                    'price': flight.cost,
                    'flight_number': flight.flight_number,
                    'stops': flight.stops,
                    'duration': flight.duration,
                    'price_difference': abs(flight.cost - target_price),
                    'price_percentage': round((flight.cost / target_price - 1) * 100, 1)
                })
            
            # Add performance metrics
            response = {
                'flights': results,
                'count': len(results),
                'target_price': target_price,
                'initial_tolerance': performance_data.get('initial_tolerance', tolerance),
                'final_tolerance': performance_data.get('final_tolerance', tolerance),
                'performance': {
                    'execution_time_ms': performance_data.get('duration_ms', 0),
                    'iterations': performance_data.get('iterations', 0),
                    'algorithm': 'binary_search',
                    'adaptive_tolerance_used': adaptive_tolerance,
                    'min_price': performance_data.get('min_price'),
                    'max_price': performance_data.get('max_price')
                },
                'visualization': {
                    'search_steps': performance_data.get('search_steps', []),
                    'histogram_data': performance_data.get('histogram_data')
                },
                'found_exact_match': performance_data.get('found_exact_match', False)
            }
            
            if request.is_json:
                return jsonify(response)
            
            return render_template('search/flight_price_results.html', 
                                  results=response,
                                  search_params={
                                      'price': target_price,
                                      'tolerance': tolerance,
                                      'from': origin,
                                      'to': destination,
                                      'departure_date': departure_date,
                                      'return_date': return_date,
                                      'adaptive_tolerance': adaptive_tolerance
                                  })
        
        # GET request - show search form
        # Set today's date as default
        today_date = datetime.now().strftime('%Y-%m-%d')
        return render_template('search/flight_price_search.html', today_date=today_date)
    
    except Exception as e:
        logger.error(f"Error in flight price search: {str(e)}")
        logger.error(traceback.format_exc())
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f"An error occurred: {str(e)}", 'danger')
        return render_template('search/flight_price_search.html')

@search_bp.route('/hotel-search', methods=['GET', 'POST'])
@csrf.exempt
def hotel_search():
    """Search for hotels based on user input"""
    try:
        # Get user itineraries if user is logged in
        user_itineraries = None
        if current_user.is_authenticated:
            user_itineraries = Itinerary.query.filter_by(user_id=current_user.id).all()
        
        if request.method == 'POST':
            # Get hotel search parameters
            city = request.form.get('city')
            check_in = request.form.get('check_in')
            check_out = request.form.get('check_out')
            guests = int(request.form.get('guests', 1))
            
            # For demo purposes, create some mock hotel data
            mock_hotels = [
                {
                    'id': 1,
                    'name': f'Luxury Hotel in {city}',
                    'address': f'{city} Downtown, 123 Main St',
                    'city': city,
                    'rating': 4.8,
                    'price': 199.99,
                    'currency': 'GBP',
                    'type': 'luxury',
                    'amenities': ['Free WiFi', 'Pool', 'Spa', 'Fitness Center', 'Restaurant'],
                    'image_url': '/static/images/hotels/luxury.jpg',
                    'room_type': 'Deluxe King'
                },
                {
                    'id': 2,
                    'name': f'Budget Inn {city}',
                    'address': f'{city} Airport Area, 456 Travel Blvd',
                    'city': city,
                    'rating': 3.5,
                    'price': 89.99,
                    'currency': 'GBP',
                    'type': 'budget',
                    'amenities': ['Free WiFi', 'Free Parking', 'Continental Breakfast'],
                    'image_url': '/static/images/hotels/budget.jpg',
                    'room_type': 'Standard Double'
                },
                {
                    'id': 3,
                    'name': f'Midtown Suites {city}',
                    'address': f'{city} Midtown, 789 Center Ave',
                    'city': city,
                    'rating': 4.2,
                    'price': 149.99,
                    'currency': 'GBP',
                    'type': 'midrange',
                    'amenities': ['Free WiFi', 'Kitchen', 'Laundry', 'Business Center'],
                    'image_url': '/static/images/hotels/midrange.jpg',
                    'room_type': 'Suite'
                }
            ]
            
            return render_template('search/hotel_search_results.html', 
                                  hotels=mock_hotels,
                                  user_itineraries=user_itineraries,
                                  search_params={
                                      'city': city,
                                      'check_in': check_in,
                                      'check_out': check_out,
                                      'guests': guests
                                  })
        
        # GET request - show search form
        return render_template('search/hotel_search.html', user_itineraries=user_itineraries)
    
    except Exception as e:
        logger.error(f"Error in hotel search: {str(e)}")
        flash(f"An error occurred: {str(e)}", 'danger')
        return render_template('search/hotel_search.html', user_itineraries=None)

@search_bp.route('/activities', methods=['GET', 'POST'])
@csrf.exempt
def activity_search():
    """Search for activities based on location and preferences"""
    try:
        # Get user itineraries if user is logged in
        user_itineraries = None
        if current_user.is_authenticated:
            user_itineraries = Itinerary.query.filter_by(user_id=current_user.id).all()

        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
                location = data.get('location')
                activity_date = data.get('activity_date')
                activity_type = data.get('activity_type')
                participants = int(data.get('participants', 1))
            else:
                location = request.form.get('location')
                activity_date = request.form.get('activity_date')
                activity_type = request.form.get('activity_type')
                participants = int(request.form.get('participants', 1))
        
            # Create some mock activity data
            mock_activities = [
                {
                    'name': 'City Walking Tour',
                    'description': f'Explore the historic center of {location} with a knowledgeable guide.',
                    'location': location,
                    'price': 29.99,
                    'currency': 'GBP',
                    'max_participants': 15,
                    'type': 'cultural',
                    'duration': '2 hours',
                    'rating': 4.7
                },
                {
                    'name': 'Food Tasting Experience',
                    'description': f'Sample the best cuisine {location} has to offer.',
                    'location': location,
                    'price': 49.99,
                    'currency': 'GBP',
                    'max_participants': 10,
                    'type': 'food',
                    'duration': '3 hours',
                    'rating': 4.9
                },
                {
                    'name': f'{location} Adventure Tour',
                    'description': 'Get your adrenaline pumping with outdoor activities.',
                    'location': location,
                    'price': 79.99,
                    'currency': 'GBP',
                    'max_participants': 8,
                    'type': 'adventure',
                    'duration': '5 hours',
                    'rating': 4.6
                }
            ]
        
            # Filter by activity type if specified
            if activity_type:
                mock_activities = [a for a in mock_activities if a['type'] == activity_type]
        
            if request.is_json:
                return jsonify(mock_activities)
    
            return render_template('search/activity_results.html', 
                                activities=mock_activities,
                                user_itineraries=user_itineraries,
                                search_params={
                                    'location': location,
                                    'activity_date': activity_date,
                                    'activity_type': activity_type,
                                    'participants': participants
                                })
    
        # GET request - show search form
        return render_template('search/activity_search.html')
    
    except Exception as e:
        logger.error(f"Error in activity search: {str(e)}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f"An error occurred: {str(e)}", 'danger')
        return render_template('search/activity_search.html')

@search_bp.route('/hotel-price', methods=['GET', 'POST'])
@csrf.exempt
def hotel_price_search():
    """Search for hotels by price using binary search algorithm"""
    try:
        # Get user itineraries if user is logged in
        user_itineraries = None
        if current_user.is_authenticated:
            user_itineraries = Itinerary.query.filter_by(user_id=current_user.id).all()
        
        if request.method == 'POST':
            # Get search parameters
            if request.is_json:
                data = request.get_json()
                target_price = float(data.get('price', 150))
                tolerance = float(data.get('tolerance', 50))
                city = data.get('city')
                check_in_date = str(data.get('check_in', ''))
                check_out_date = str(data.get('check_out', ''))
                guests = int(data.get('guests', 1))
                adaptive_tolerance = data.get('adaptive_tolerance', False)
            else:
                target_price = float(request.form.get('price', 150))
                tolerance = float(request.form.get('tolerance', 50))
                city = request.form.get('city')
                check_in_date = str(request.form.get('check_in', ''))
                check_out_date = str(request.form.get('check_out', ''))
                guests = int(request.form.get('guests', 1))
                adaptive_tolerance = request.form.get('adaptive_tolerance') == 'on'
            
            # Log the search parameters
            logger.info(f"Hotel price search: target=£{target_price}, tolerance=£{tolerance}, city={city}, check_in={check_in_date}, check_out={check_out_date}, guests={guests}")
            
            # Perform binary search
            matching_hotels, performance_data = binary_search_hotels_by_price(
                target_price=target_price,
                tolerance=tolerance,
                city=city,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                guests=guests,
                adaptive_tolerance=adaptive_tolerance,
                collect_vis_data=True
            )
            
            # Calculate the length of stay
            check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
            check_out = datetime.strptime(check_out_date, '%Y-%m-%d')
            nights = (check_out - check_in).days
            
            # Format the results with total price for stay
            results = []
            for hotel in matching_hotels:
                # Calculate total price for the stay
                total_price = hotel['cost_per_night'] * nights
                
                # Calculate price difference
                price_diff = abs(hotel['cost_per_night'] - target_price)
                price_percentage = round((hotel['cost_per_night'] / target_price - 1) * 100, 1)
                
                results.append({
                    'id': hotel['id'],
                    'name': hotel['name'],
                    'address': hotel['address'],
                    'rating': hotel['rating'],
                    'price_per_night': hotel['cost_per_night'],
                    'total_price': total_price,
                    'currency': hotel['currency'],
                    'type': hotel['type'],
                    'amenities': hotel['amenities'],
                    'image_url': hotel['image_url'],
                    'room_type': hotel['room_type'],
                    'price_difference': price_diff,
                    'price_percentage': price_percentage
                })
            
            # Sort results by price difference from target
            results.sort(key=lambda x: x['price_difference'])
            
            # Add performance metrics
            response = {
                'hotels': results,
                'count': len(results),
                'target_price': target_price,
                'initial_tolerance': performance_data.get('initial_tolerance', tolerance),
                'final_tolerance': performance_data.get('final_tolerance', tolerance),
                'performance': {
                    'execution_time_ms': performance_data.get('duration_ms', 0),
                    'iterations': performance_data.get('iterations', 0),
                    'algorithm': 'binary_search',
                    'adaptive_tolerance_used': adaptive_tolerance,
                    'min_price': performance_data.get('min_price'),
                    'max_price': performance_data.get('max_price')
                },
                'visualization': {
                    'search_steps': performance_data.get('search_steps', []),
                    'histogram_data': performance_data.get('histogram_data')
                },
                'found_exact_match': performance_data.get('found_exact_match', False),
                'nights': nights
            }
            
            if request.is_json:
                return jsonify(response)
            
            return render_template('search/hotel_price_results.html', 
                                  results=response,
                                  user_itineraries=user_itineraries,
                                  search_params={
                                      'price': target_price,
                                      'tolerance': tolerance,
                                      'city': city,
                                      'check_in': check_in_date,
                                      'check_out': check_out_date,
                                      'guests': guests,
                                      'adaptive_tolerance': adaptive_tolerance,
                                      'nights': nights
                                  })
        
        # GET request - show search form
        today_date = datetime.now().strftime('%Y-%m-%d')
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        return render_template('search/hotel_price_search.html', 
                              today_date=today_date, 
                              tomorrow_date=tomorrow_date,
                              user_itineraries=user_itineraries)
    
    except Exception as e:
        logger.error(f"Error in hotel price search: {str(e)}")
        logger.error(traceback.format_exc())
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f"An error occurred: {str(e)}", 'danger')
        return render_template('search/hotel_price_search.html')

@search_bp.route('/save-hotel-to-itinerary', methods=['POST'])
@login_required
def save_hotel_to_itinerary():
    """Save a hotel to a user's itinerary"""
    try:
        # Get form data
        hotel_data = request.form.get('hotel_data')
        itinerary_id = request.form.get('itinerary_id')
        new_itinerary_name = request.form.get('new_itinerary_name')
        check_in_date = str(request.form.get('check_in_date', ''))
        check_out_date = str(request.form.get('check_out_date', ''))
        
        if not hotel_data:
            flash('No hotel data provided', 'danger')
            return redirect(url_for('search.hotel_search'))
        
        # Parse hotel data
        try:
            # Log the hotel data for debugging
            logger.info(f"Hotel data received: {hotel_data}")
            hotel_data = json.loads(hotel_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}, Data: {hotel_data}")
            flash('Invalid hotel data format', 'danger')
            return redirect(url_for('search.hotel_search'))
        
        # Create new itinerary if specified
        if itinerary_id == 'new':
            if not new_itinerary_name:
                flash('Please provide a name for the new itinerary', 'danger')
                return redirect(url_for('search.hotel_search'))
            
            # Create new itinerary
            new_itinerary = Itinerary(
                user_id=current_user.id,
                name=new_itinerary_name,
                start_date=datetime.strptime(check_in_date, '%Y-%m-%d') if check_in_date else datetime.now(),
                end_date=datetime.strptime(check_out_date, '%Y-%m-%d') if check_out_date else datetime.now() + timedelta(days=7)
            )
            
            db.session.add(new_itinerary)
            db.session.commit()
            
            itinerary_id = new_itinerary.id
            logger.info(f"Created new itinerary: {new_itinerary_name} (ID: {itinerary_id})")
        
        # Verify itinerary ownership
        itinerary = Itinerary.query.get(itinerary_id)
        if not itinerary:
            flash('Invalid itinerary ID', 'danger')
            return redirect(url_for('search.hotel_search'))
        
        if itinerary.user_id != current_user.id:
            flash('You do not have permission to modify this itinerary', 'danger')
            return redirect(url_for('search.hotel_search'))
        
        # Extract hotel data
        try:
            # Get hotel data fields with appropriate fallbacks
            hotel_name = hotel_data.get('name', 'Unknown Hotel')
            hotel_address = hotel_data.get('address', '')
            hotel_type = hotel_data.get('type', 'hotel')
            cost_per_night = float(hotel_data.get('price', 0))
            
            # Parse dates
            check_in = datetime.strptime(check_in_date, '%Y-%m-%d') if check_in_date else datetime.now()
            check_out = datetime.strptime(check_out_date, '%Y-%m-%d') if check_out_date else datetime.now() + timedelta(days=7)
            
            # Create new accommodation
            new_accommodation = Accommodation(
                itinerary_id=itinerary.id,
                name=hotel_name,
                address=hotel_address,
                check_in_date=check_in,
                check_out_date=check_out,
                cost_per_night=cost_per_night,
                type=hotel_type
            )
            
            db.session.add(new_accommodation)
            db.session.commit()
            
            flash(f'Hotel "{hotel_name}" saved to itinerary "{itinerary.name}" successfully!', 'success')
            return redirect(url_for('main.view_itinerary', itinerary_id=itinerary_id))
            
        except KeyError as e:
            db.session.rollback()
            logger.error(f"Error extracting hotel data: {str(e)}")
            flash(f"Error saving hotel: Missing required data ({str(e)})", 'danger')
            return redirect(url_for('search.hotel_search'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving hotel: {str(e)}")
            flash(f"Error saving hotel: {str(e)}", 'danger')
            return redirect(url_for('search.hotel_search'))
    
    except Exception as e:
        logger.error(f"Error in save_hotel_to_itinerary: {str(e)}")
        flash(f"An error occurred: {str(e)}", 'danger')
        return redirect(url_for('search.hotel_search'))

@search_bp.route('/book-activity', methods=['POST'])
@csrf.exempt
def book_activity():
    """Book an activity"""
    try:
        # Get form data for activity details
        activity_name = request.form.get('activity_name')
        activity_price = float(request.form.get('activity_price', 0))
        activity_duration = request.form.get('activity_duration')
        activity_location = request.form.get('activity_location')
        
        # Get booking details
        participant_count = int(request.form.get('participant_count', 1))
        booker_name = request.form.get('booker_name')
        booker_email = request.form.get('booker_email')
        special_requests = request.form.get('special_requests', '')
        activity_date = request.form.get('activity_date')
        
        if not activity_name:
            flash('No activity data provided', 'danger')
            return redirect(url_for('search.activity_search'))
        
        # Calculate total price
        total_price = activity_price * participant_count
        
        # In a real app, you would save the booking to a database
        # and possibly integrate with a payment processor
        
        # For now, just show a success message
        flash(f"Activity '{activity_name}' booked successfully for {participant_count} participants. Total: £{total_price:.2f}", 'success')
        
        # If user is logged in, redirect to dashboard, otherwise to homepage
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        else:
            return redirect(url_for('main.index'))
            
    except Exception as e:
        logger.error(f"Error booking activity: {str(e)}")
        flash(f"An error occurred while booking: {str(e)}", 'danger')
        return redirect(url_for('search.activity_search'))

@search_bp.route('/save-activity-to-itinerary', methods=['POST'])
@login_required
@csrf.exempt
def save_activity_to_itinerary():
    """Save an activity to a user's itinerary"""
    try:
        # Get activity details from form
        activity_name = request.form.get('activity_name')
        activity_description = request.form.get('activity_description')
        activity_location = request.form.get('activity_location')
        activity_price = float(request.form.get('activity_price', 0))
        activity_duration = request.form.get('activity_duration', '2 hours')
        
        # Get itinerary details
        itinerary_id = request.form.get('itinerary_id')
        new_itinerary_name = request.form.get('new_itinerary_name')
        activity_date = request.form.get('activity_date')
        start_time = request.form.get('start_time')
        
        if not activity_name:
            flash('No activity data provided', 'danger')
            return redirect(url_for('search.activity_search'))
        
        # Create a new itinerary if needed
        if itinerary_id == 'new':
            if not new_itinerary_name:
                flash('Please provide a name for the new itinerary', 'danger')
                return redirect(url_for('search.activity_search'))
            
            # Get today's date as default start date and add a week for end date
            today = datetime.now().date()
            # Use activity_date if available, otherwise use today
            if activity_date:
                start_date = datetime.strptime(activity_date, '%Y-%m-%d').date()
            else:
                start_date = today
            
            end_date = start_date + timedelta(days=7)
            
            # Create new itinerary
            itinerary = Itinerary(
                user_id=current_user.id,
                name=new_itinerary_name,
                start_date=start_date,
                end_date=end_date
            )
            
            db.session.add(itinerary)
            db.session.flush()  # Get the ID without committing
            
            itinerary_id = itinerary.id
        else:
            # Verify itinerary exists and belongs to user
            itinerary = Itinerary.query.get(itinerary_id)
            if not itinerary:
                flash('Invalid itinerary ID', 'danger')
                return redirect(url_for('search.activity_search'))
            
            if itinerary.user_id != current_user.id:
                flash('You do not have permission to modify this itinerary', 'danger')
                return redirect(url_for('search.activity_search'))
        
        # Make sure we have a valid activity date
        if not activity_date:
            activity_date = datetime.now().strftime('%Y-%m-%d')
            logger.info(f"No activity date provided, defaulting to today: {activity_date}")
        
        # Make sure we have a valid start time
        if not start_time:
            start_time = datetime.now().strftime('%H:%M')
            logger.info(f"No start time provided, defaulting to current time: {start_time}")
        
        # Combine date and time to create activity datetime
        try:
            activity_datetime = datetime.strptime(f"{activity_date} {start_time}", '%Y-%m-%d %H:%M')
            
            # Extract duration value as a float (default to 2 if parsing fails)
            try:
                if isinstance(activity_duration, str):
                    if 'hours' in activity_duration:
                        duration_hours = float(activity_duration.split('hours')[0].strip())
                    elif 'hour' in activity_duration:
                        duration_hours = float(activity_duration.split('hour')[0].strip())
                    else:
                        duration_hours = float(activity_duration.split()[0])
                else:
                    duration_hours = 2.0
            except (ValueError, IndexError):
                duration_hours = 2.0
                logger.warning(f"Could not parse duration '{activity_duration}', defaulting to {duration_hours} hours")
            
            # Calculate end time (add duration in hours)
            end_datetime = activity_datetime + timedelta(hours=duration_hours)
            
            logger.info(f"Activity will be scheduled on {activity_datetime.date()} from {activity_datetime.time()} to {end_datetime.time()}")
        except ValueError as e:
            logger.error(f"Error parsing activity date/time: {e}")
            # Default values as fallback
            activity_datetime = datetime.now()
            end_datetime = activity_datetime + timedelta(hours=2)
        
        # Create a new activity in the database
        new_activity = Activity(
            itinerary_id=itinerary_id,
            name=activity_name,
            description=activity_description,
            location=activity_location,
            start_time=activity_datetime,  # Set the start time
            end_time=end_datetime,         # Set the end time
            cost=activity_price,
            duration=int(duration_hours * 60)  # Convert hours to minutes
        )
        
        # The date field will be updated by the database triggers or manually if needed
        # Since we already set the start_time field which includes the date
        
        db.session.add(new_activity)
        db.session.commit()
        
        flash(f"Activity '{activity_name}' added to your itinerary", 'success')
        return redirect(url_for('main.view_itinerary', itinerary_id=itinerary_id))
            
    except Exception as e:
        logger.error(f"Error saving activity to itinerary: {str(e)}")
        db.session.rollback()
        flash(f"An error occurred while saving the activity: {str(e)}", 'danger')
        return redirect(url_for('search.activity_search'))