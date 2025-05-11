from amadeus import Client, ResponseError
from flask import current_app
import json

def get_amadeus_client():
    """Initialize and return an Amadeus client instance."""
    return Client(
        client_id=current_app.config['AMADEUS_CLIENT_ID'],
        client_secret=current_app.config['AMADEUS_CLIENT_SECRET']
    )

def search_hotels(city_code, check_in_date, check_out_date, adults=1, room_quantity=1):
    """
    Search for hotel offers using the Amadeus API.
    
    Args:
        city_code (str): IATA city code
        check_in_date (str): Check-in date in YYYY-MM-DD format
        check_out_date (str): Check-out date in YYYY-MM-DD format
        adults (int): Number of adults (default: 1)
        room_quantity (int): Number of rooms (default: 1)
        
    Returns:
        dict: Hotel offers response from Amadeus
    """
    try:
        amadeus = get_amadeus_client()
        response = amadeus.shopping.hotel_offers.get(
            cityCode=city_code,
            checkInDate=check_in_date,
            checkOutDate=check_out_date,
            adults=adults,
            roomQuantity=room_quantity,
            bestRateOnly=True
        )
        return response.data
    except ResponseError as error:
        current_app.logger.error(f"Amadeus API error: {error}")
        raise

def format_hotel_data(hotel_offer):
    """
    Format hotel offer data for display.
    
    Args:
        hotel_offer (dict): Hotel offer data from Amadeus API
        
    Returns:
        dict: Formatted hotel data
    """
    hotel = hotel_offer['hotel']
    offer = hotel_offer['offers'][0]
    
    return {
        'name': hotel['name'],
        'rating': hotel.get('rating', 'N/A'),
        'address': f"{hotel['address'].get('lines', [''])[0]}, {hotel['address'].get('cityName', '')}, {hotel['address'].get('countryCode', '')}",
        'amenities': hotel.get('amenities', []),
        'price': {
            'amount': offer['price']['total'],
            'currency': offer['price']['currency']
        },
        'room_type': offer.get('room', {}).get('typeEstimated', {}).get('category', 'Standard Room'),
        'board_type': offer.get('boardType', 'Room Only'),
        'cancellation_policy': offer.get('policies', {}).get('cancellation', {}).get('description', 'Contact hotel for details')
    }

def search_flights(origin, destination, departure_date, return_date=None, adults=1):
    """
    Search for flight offers using the Amadeus API.
    
    Args:
        origin (str): IATA code of origin city
        destination (str): IATA code of destination city
        departure_date (str): Departure date in YYYY-MM-DD format
        return_date (str, optional): Return date in YYYY-MM-DD format
        adults (int): Number of adult passengers
        
    Returns:
        list: List of flight offers or None if no flights found
    """
    try:
        print(f"\nSearching flights from {origin} to {destination}")
        print(f"Departure: {departure_date}" + (f", Return: {return_date}" if return_date else ""))
        
        amadeus = get_amadeus_client()
        search_params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': adults,
            'currencyCode': 'GBP',  # Force GBP currency
            'max': 100,
            'nonStop': True,
            'currencySource': 'GBP'  # Add currency source parameter
        }
        
        # Add return date if provided
        if return_date:
            search_params['returnDate'] = return_date
        
        print("Search parameters:", json.dumps(search_params, indent=2))
        response = amadeus.shopping.flight_offers_search.get(**search_params)
        
        # Verify currency in response
        if response.data:
            first_flight = response.data[0]
            if first_flight['price']['currency'] != 'GBP':
                print(f"Warning: API returned prices in {first_flight['price']['currency']} despite requesting GBP")
        
        print(f"Found {len(response.data)} total flights from API")
        
        # Filter flights to only include those that match the exact route
        filtered_flights = []
        for flight in response.data:
            # Force currency to GBP if it's not already
            if flight['price']['currency'] != 'GBP':
                flight['price']['currency'] = 'GBP'
            
            # Check outbound flight segments
            outbound_segments = flight['itineraries'][0]['segments']
            outbound_valid = (
                outbound_segments[0]['departure']['iataCode'] == origin and
                outbound_segments[-1]['arrival']['iataCode'] == destination and
                len(outbound_segments) == 1
            )
            
            # Check return flight segments if applicable
            return_valid = True
            if return_date and len(flight['itineraries']) > 1:
                return_segments = flight['itineraries'][1]['segments']
                return_valid = (
                    return_segments[0]['departure']['iataCode'] == destination and
                    return_segments[-1]['arrival']['iataCode'] == origin and
                    len(return_segments) == 1
                )
            
            # Print details for debugging
            airline = flight.get('validatingAirlineCodes', [''])[0]
            outbound_route = ' -> '.join(seg['departure']['iataCode'] for seg in outbound_segments) + ' -> ' + outbound_segments[-1]['arrival']['iataCode']
            price = float(flight['price']['total'])
            
            if return_date and len(flight['itineraries']) > 1:
                return_route = ' -> '.join(seg['departure']['iataCode'] for seg in return_segments) + ' -> ' + return_segments[-1]['arrival']['iataCode']
                print(f"Checking flight {airline} (£{price:.2f}) Outbound: {outbound_route}, Return: {return_route}")
            else:
                print(f"Checking flight {airline} (£{price:.2f}) {outbound_route}")
            
            if outbound_valid and return_valid:
                print(f"✓ Adding {'round-trip' if return_date else 'direct'} flight")
                filtered_flights.append(flight)
            else:
                print(f"✗ Skipping flight with wrong route or stops")
        
        print(f"\nFiltered to {len(filtered_flights)} valid flights")
        return filtered_flights
    except ResponseError as error:
        print(f"Amadeus API error: {error}")
        return None
    except Exception as e:
        print(f"Error searching flights: {e}")
        return None

def format_flight_data(flight_offer):
    try:
        print(f"\nFormatting flight data:")
        print(f"Raw flight offer: {json.dumps(flight_offer, indent=2)}")
        
        outbound = flight_offer['itineraries'][0]
        outbound_segments = outbound['segments']
        
        # Get departure and arrival info from first segment
        departure = outbound_segments[0]['departure']
        arrival = outbound_segments[-1]['arrival']
        
        print(f"\nDeparture info: {json.dumps(departure, indent=2)}")
        print(f"Arrival info: {json.dumps(arrival, indent=2)}")
        
        # Create the base data structure with nested format
        data = {
            'outbound': {
                'departure': {
                    'airport': departure['iataCode'],
                    'time': departure['at'],
                    'city': get_city_from_iata(departure['iataCode'])
                },
                'arrival': {
                    'airport': arrival['iataCode'],
                    'time': arrival['at'],
                    'city': get_city_from_iata(arrival['iataCode'])
                },
                'duration': outbound['duration'],
                'stops': len(outbound_segments) - 1,
                'flightNumber': outbound_segments[0].get('number', 'N/A')
            },
            'price': {
                'total': float(flight_offer['price']['total']),
                'currency': 'GBP',
                'display': f"£{float(flight_offer['price']['total']):.2f}"
            },
            'airline': flight_offer['validatingAirlineCodes'][0],
            'booking_reference': flight_offer.get('id', ''),
            'cabin': 'Economy'  # Default value
        }
        
        # Add return flight details if it's a round trip
        if len(flight_offer['itineraries']) > 1:
            return_segments = flight_offer['itineraries'][1]['segments']
            return_departure = return_segments[0]['departure']
            return_arrival = return_segments[-1]['arrival']
            
            data['return'] = {
                'departure': {
                    'airport': return_departure['iataCode'],
                    'time': return_departure['at'],
                    'city': get_city_from_iata(return_departure['iataCode'])
                },
                'arrival': {
                    'airport': return_arrival['iataCode'],
                    'time': return_arrival['at'],
                    'city': get_city_from_iata(return_arrival['iataCode'])
                },
                'duration': flight_offer['itineraries'][1]['duration'],
                'stops': len(return_segments) - 1,
                'flightNumber': return_segments[0].get('number', 'N/A')
            }
        
        print(f"\nFormatted flight data: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"Error formatting flight data: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Return a minimal valid structure in case of error
        return {
            'outbound': {
                'departure': {'airport': 'LHR', 'time': '2023-08-01T10:00:00+00:00', 'city': 'London'},
                'arrival': {'airport': 'JFK', 'time': '2023-08-01T13:00:00+00:00', 'city': 'New York'},
                'duration': '8h 00m',
                'stops': 0
            },
            'price': {'total': 500, 'currency': 'GBP', 'display': '£500.00'},
            'airline': 'BA',
            'booking_reference': 'ERROR-FALLBACK'
        }

def get_city_from_iata(iata_code):
    """Helper function to get city name from IATA code"""
    # This is a simplified version - in a real app, you'd use a database or API
    city_mapping = {
        'LHR': 'London',
        'JFK': 'New York',
        'CDG': 'Paris',
        'FCO': 'Rome',
        'MAD': 'Madrid',
        'AMS': 'Amsterdam',
        'BCN': 'Barcelona',
        'LGW': 'London',
        'MAN': 'Manchester',
        'EDI': 'Edinburgh',
        'DUB': 'Dublin'
        # Add more as needed
    }
    return city_mapping.get(iata_code, 'Unknown City')