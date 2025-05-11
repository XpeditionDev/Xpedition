from app.extensions import amadeus_client
from datetime import datetime
import logging
from flask import current_app

# Set up logging
logger = logging.getLogger(__name__)

def search_flights(origin, destination, departure_date, return_date=None, adults=1):
    """
    Search for flights using the Amadeus API
    
    Args:
        origin: Origin airport IATA code (e.g., 'LHR')
        destination: Destination airport IATA code (e.g., 'JFK')
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Optional return date in YYYY-MM-DD format
        adults: Number of adult passengers
        
    Returns:
        A list of formatted flight offers or an empty list if no flights found
    """
    try:
        # Get the Amadeus client from the current app context
        amadeus_client = current_app.config.get('AMADEUS_CLIENT')
        
        if not amadeus_client:
            logger.error("Amadeus client not initialized")
            return [], {'error': 'Amadeus API client not initialized'}
            
        # Format dates to required format YYYY-MM-DD
        departure_date_str = departure_date
        if isinstance(departure_date, datetime):
            departure_date_str = departure_date.strftime('%Y-%m-%d')
            
        # Build request parameters
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date_str,
            'adults': adults,
            'currencyCode': 'GBP',
            'max': 20  # Limit to 20 results for performance
        }
        
        # Add return date if provided (for round trips)
        if return_date:
            return_date_str = return_date
            if isinstance(return_date, datetime):
                return_date_str = return_date.strftime('%Y-%m-%d')
            params['returnDate'] = return_date_str
        
        # Make API call to Amadeus
        logger.info(f"Searching Amadeus API for flights from {origin} to {destination} on {departure_date_str}")
        
        try:
            flight_offers_response = amadeus_client.shopping.flight_offers_search.get(**params)
            flight_offers = flight_offers_response.data
        except Exception as api_error:
            logger.error(f"Amadeus API error: {str(api_error)}")
            return [], {'error': str(api_error)}
        
        # No flights found
        if not flight_offers:
            logger.info("No flights found in Amadeus response")
            return [], {'error': 'No flights found'}
        
        formatted_flights = []
        for offer in flight_offers:
            try:
                # Process each flight offer
                formatted_flight = format_flight_offer(offer)
                formatted_flights.append(formatted_flight)
            except Exception as e:
                logger.error(f"Error processing flight offer: {str(e)}")
                continue
                
        return formatted_flights, {'success': True, 'count': len(formatted_flights)}
        
    except Exception as e:
        logger.error(f"Error in search_flights: {str(e)}")
        return [], {'error': str(e)}
    
def format_flight_offer(offer):
    """
    Format an Amadeus flight offer into a standardized format for the application
    
    Args:
        offer: An Amadeus flight offer object
        
    Returns:
        A formatted flight object
    """
    try:
        # Get itinerary information
        itineraries = offer['itineraries']
        price_info = offer['price']
        total_price = float(price_info['total'])
        currency = price_info['currency']
        
        # Get outbound flight
        outbound = itineraries[0]
        
        # Get first and last segment of outbound flight for origin and destination
        first_segment = outbound['segments'][0]
        last_segment = outbound['segments'][-1]
        
        # Determine airline (use first segment's carrier code)
        airline_code = first_segment['carrierCode']
        
        # Check if return flight exists
        has_return = len(itineraries) > 1
        is_round_trip = has_return
        
        # Create formatted flight object
        formatted_flight = {
            'airline': airline_code,  # Ideally we would map this to full airline name
            'departure': {
                'airport': first_segment['departure']['iataCode'],
                'time': first_segment['departure']['at']
            },
            'arrival': {
                'airport': last_segment['arrival']['iataCode'],
                'time': last_segment['arrival']['at']
            },
            'details': {
                'duration': outbound['duration'],
                'stops': len(outbound['segments']) - 1,
                'outbound': {
                    'duration': outbound['duration'],
                    'stops': len(outbound['segments']) - 1
                }
            },
            'price': {
                'total': total_price,
                'currency': currency,
                'display': f'£{total_price:.2f}' if currency == 'GBP' else f'${total_price:.2f}'
            },
            'is_round_trip': is_round_trip,
            'offer_id': offer['id']
        }
        
        # Add return flight information if it exists
        if has_return:
            return_flight = itineraries[1]
            first_return_segment = return_flight['segments'][0]
            last_return_segment = return_flight['segments'][-1]
            
            formatted_flight['details']['return'] = {
                'duration': return_flight['duration'],
                'stops': len(return_flight['segments']) - 1,
                'departure': {
                    'airport': first_return_segment['departure']['iataCode'],
                    'time': first_return_segment['departure']['at']
                },
                'arrival': {
                    'airport': last_return_segment['arrival']['iataCode'],
                    'time': last_return_segment['arrival']['at']
                }
            }
        
        return formatted_flight
        
    except KeyError as e:
        logger.error(f"Missing key in Amadeus response: {str(e)}")
        raise Exception(f"Couldn't process Amadeus flight data: {str(e)}")
    except Exception as e:
        logger.error(f"Error formatting flight offer: {str(e)}")
        raise 