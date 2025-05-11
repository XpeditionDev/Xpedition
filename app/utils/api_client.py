import requests
import os
from datetime import datetime, timedelta
from amadeus import Client, ResponseError
from flask import current_app
from app.utils.flight_api import FlightAPIClient
from app.utils.hotel_api import get_hotel_client, MockHotelClient

class AmadeusClient:
    def __init__(self):
        client_id = os.environ.get('AMADEUS_CLIENT_ID')
        client_secret = os.environ.get('AMADEUS_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError("Amadeus API credentials not found in environment variables")
        
        print(f"Initializing Amadeus client with credentials (ID: {client_id[:4]}...)")
        self.amadeus = Client(
            client_id=client_id,
            client_secret=client_secret
        )
        print("Amadeus client initialized successfully")
        # Create a hotel client that will be used for hotel searches
        self.hotel_client = get_hotel_client()
    
    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1, currency='GBP'):
        """
        Search for flights using the Amadeus Flight Offers Search API
        """
        try:
            # Format dates
            departure_date_str = departure_date.strftime('%Y-%m-%d')
            
            # Build search params
            search_params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date_str,
                'adults': adults,
                'currencyCode': currency,
                'max': 10  # Limit results
            }
            
            # Add return date if provided
            if return_date:
                search_params['returnDate'] = return_date.strftime('%Y-%m-%d')
            
            # Execute the search
            response = self.amadeus.shopping.flight_offers_search.get(**search_params)
            
            # Process and format the results
            formatted_results = []
            for offer in response.data:
                flight_info = {
                    'id': offer['id'],
                    'price': {
                        'total': offer['price']['total'],
                        'currency': offer['price']['currency']
                    },
                    'segments': []
                }
                
                # Process each segment (outbound, return, connections)
                for itinerary in offer['itineraries']:
                    for segment in itinerary['segments']:
                        segment_info = {
                            'departure': {
                                'iataCode': segment['departure']['iataCode'],
                                'at': segment['departure']['at']
                            },
                            'arrival': {
                                'iataCode': segment['arrival']['iataCode'],
                                'at': segment['arrival']['at']
                            },
                            'carrierCode': segment['carrierCode'],
                            'number': segment['number'],
                            'duration': segment['duration']
                        }
                        flight_info['segments'].append(segment_info)
                
                formatted_results.append(flight_info)
            
            return {
                'status': 'success',
                'flights': formatted_results
            }
        
        except ResponseError as e:
            print(f"Amadeus API Error: {str(e)}")  # Log the error
            return {
                'status': 'error',
                'message': str(e),
                'error_code': e.code
            }
        except Exception as e:
            print(f"Unexpected error: {str(e)}")  # Log the error
            return {
                'status': 'error',
                'message': f"An unexpected error occurred: {str(e)}"
            }
    
    def search_hotels(self, city_code, check_in_date, check_out_date, adults=1, rooms=1, currency='GBP'):
        """
        Search for hotels using our hotel client instead of Amadeus
        """
        # Delegate hotel searches to our dedicated hotel client
        return self.hotel_client.search_hotels(
            city_code=city_code,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults,
            rooms=rooms,
            currency=currency
        )
    
    def get_city_search(self, keyword, max_results=10):
        """
        Search for cities and airports using the Amadeus City Search API
        """
        try:
            response = self.amadeus.reference_data.locations.get(
                keyword=keyword,
                subType=('CITY', 'AIRPORT'),
                page={'limit': max_results}
            )
            
            formatted_results = []
            for location in response.data:
                location_info = {
                    'id': location['id'],
                    'name': location['name'],
                    'iataCode': location['iataCode'],
                    'subType': location['subType'],
                    'countryName': location['address'].get('countryName', ''),
                    'cityName': location['address'].get('cityName', '')
                }
                formatted_results.append(location_info)
            
            return {
                'status': 'success',
                'locations': formatted_results
            }
        
        except ResponseError as e:
            return {
                'status': 'error',
                'message': str(e),
                'error_code': e.code
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"An unexpected error occurred: {str(e)}"
            }
    
    def search_activities(self, location, date, category=None):
        """
        Search for activities using the Amadeus Activities API
        In a real implementation, this would call the Amadeus API
        For now, we'll delegate to the hotel client
        """
        try:
            print(f"Searching for activities in {location} on {date.strftime('%Y-%m-%d')}")
            print(f"Category filter: {category if category else 'None'}")
            
            # In a real implementation, we would call the Amadeus API here
            # For now, return mock data
            return {
                'status': 'success',
                'message': 'Note: Using mock activity data',
                'activities': self._get_mock_activities(location, category)
            }
        except Exception as e:
            print(f"Error searching for activities: {str(e)}")
            return {
                'status': 'error',
                'message': f"An unexpected error occurred: {str(e)}"
            }
    
    def _get_mock_activities(self, location, category=None):
        """Generate mock activity data for demonstration purposes"""
        # Just delegate to MockApiClient's implementation
        mock_client = MockApiClient()
        mock_result = mock_client.search_activities(location, None, category)
        return mock_result.get('activities', [])

# Fallback mock API for development and testing when API keys are not available
class MockApiClient:
    def __init__(self):
        # Create a hotel client - either real or mock
        self.hotel_client = get_hotel_client()
    
    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1, currency='GBP'):
        """
        Mock flight search for development/testing
        """
        departure_datetime = datetime.combine(departure_date, datetime.min.time())
        arrival_datetime = departure_datetime + timedelta(hours=2, minutes=30)
        
        return_flight = None
        if return_date:
            return_departure = datetime.combine(return_date, datetime.min.time())
            return_arrival = return_departure + timedelta(hours=2, minutes=15)
            return_flight = {
                'departure': {
                    'iataCode': destination,
                    'at': return_departure.isoformat()
                },
                'arrival': {
                    'iataCode': origin,
                    'at': return_arrival.isoformat()
                },
                'carrierCode': 'BA',
                'number': '1234',
                'duration': 'PT2H15M'
            }
        
        mock_results = {
            'status': 'success',
            'flights': [
                {
                    'id': 'mock-flight-1',
                    'price': {
                        'total': '199.99',
                        'currency': currency
                    },
                    'segments': [
                        {
                            'departure': {
                                'iataCode': origin,
                                'at': departure_datetime.isoformat()
                            },
                            'arrival': {
                                'iataCode': destination,
                                'at': arrival_datetime.isoformat()
                            },
                            'carrierCode': 'BA',
                            'number': '4321',
                            'duration': 'PT2H30M'
                        }
                    ]
                }
            ]
        }
        
        if return_flight:
            mock_results['flights'][0]['segments'].append(return_flight)
            mock_results['flights'][0]['price']['total'] = '349.99'
        
        return mock_results
    
    def search_hotels(self, city_code, check_in_date, check_out_date, adults=1, rooms=1, currency='GBP'):
        """
        Delegate hotel searches to our dedicated hotel client
        """
        return self.hotel_client.search_hotels(
            city_code=city_code,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults,
            rooms=rooms,
            currency=currency
        )
    
    def get_city_search(self, keyword, max_results=10):
        """
        Mock city search for development/testing
        """
        mock_cities = [
            {
                'id': 'CLON',
                'name': 'London',
                'iataCode': 'LON',
                'subType': 'CITY',
                'countryName': 'United Kingdom',
                'cityName': 'London'
            },
            {
                'id': 'ALHR',
                'name': 'Heathrow Airport',
                'iataCode': 'LHR',
                'subType': 'AIRPORT',
                'countryName': 'United Kingdom',
                'cityName': 'London'
            },
            {
                'id': 'CPAR',
                'name': 'Paris',
                'iataCode': 'PAR',
                'subType': 'CITY',
                'countryName': 'France',
                'cityName': 'Paris'
            },
            {
                'id': 'ACDG',
                'name': 'Charles de Gaulle Airport',
                'iataCode': 'CDG',
                'subType': 'AIRPORT',
                'countryName': 'France',
                'cityName': 'Paris'
            }
        ]
        
        filtered_results = [city for city in mock_cities 
                            if keyword.lower() in city['name'].lower() 
                            or keyword.lower() in city['cityName'].lower()]
        
        return {
            'status': 'success',
            'locations': filtered_results[:max_results]
        }
    
    def search_activities(self, location, date, category=None):
        """
        Mock activity search for development/testing
        """
        print(f"MockApiClient: Searching for activities in {location}")
        
        # Base set of activities for various locations
        mock_activities_by_location = {
            'LONDON': [
                {
                    'id': 'act-lon-1',
                    'name': 'Tower of London Tour',
                    'description': 'Explore the historic Tower of London with a Beefeater guide.',
                    'category': 'sightseeing',
                    'price': {
                        'amount': '25.00',
                        'currency': 'GBP'
                    },
                    'duration': '120',
                    'location': 'Tower Hill, London',
                    'rating': 4.7,
                    'reviews_count': 1250
                },
                {
                    'id': 'act-lon-2',
                    'name': 'British Museum Guided Tour',
                    'description': 'Discover the wonders of the British Museum with an expert guide.',
                    'category': 'culture',
                    'price': {
                        'amount': '15.00',
                        'currency': 'GBP'
                    },
                    'duration': '90',
                    'location': 'Great Russell St, London',
                    'rating': 4.8,
                    'reviews_count': 980
                },
                {
                    'id': 'act-lon-3',
                    'name': 'London Eye Experience',
                    'description': 'See London from above on the iconic London Eye.',
                    'category': 'sightseeing',
                    'price': {
                        'amount': '32.50',
                        'currency': 'GBP'
                    },
                    'duration': '30',
                    'location': 'South Bank, London',
                    'rating': 4.5,
                    'reviews_count': 2150
                },
                {
                    'id': 'act-lon-4',
                    'name': 'Thames River Dinner Cruise',
                    'description': 'Enjoy a luxurious dinner while cruising along the Thames.',
                    'category': 'food',
                    'price': {
                        'amount': '75.00',
                        'currency': 'GBP'
                    },
                    'duration': '150',
                    'location': 'Westminster Pier, London',
                    'rating': 4.6,
                    'reviews_count': 750
                },
                {
                    'id': 'act-lon-5',
                    'name': 'West End Theatre Show',
                    'description': 'Experience the magic of London\'s West End with a top theatre show.',
                    'category': 'entertainment',
                    'price': {
                        'amount': '65.00',
                        'currency': 'GBP'
                    },
                    'duration': '180',
                    'location': 'West End, London',
                    'rating': 4.9,
                    'reviews_count': 1800
                }
            ],
            'PARIS': [
                {
                    'id': 'act-par-1',
                    'name': 'Eiffel Tower Skip-the-Line Tickets',
                    'description': 'Skip the long lines and head straight to the top of the Eiffel Tower.',
                    'category': 'sightseeing',
                    'price': {
                        'amount': '45.00',
                        'currency': 'EUR'
                    },
                    'duration': '90',
                    'location': 'Champ de Mars, Paris',
                    'rating': 4.7,
                    'reviews_count': 3200
                },
                {
                    'id': 'act-par-2',
                    'name': 'Louvre Museum Guided Tour',
                    'description': 'Explore the world\'s most visited museum with an expert guide.',
                    'category': 'culture',
                    'price': {
                        'amount': '35.00',
                        'currency': 'EUR'
                    },
                    'duration': '120',
                    'location': 'Rue de Rivoli, Paris',
                    'rating': 4.8,
                    'reviews_count': 2800
                }
            ],
            'NEW YORK': [
                {
                    'id': 'act-nyc-1',
                    'name': 'Empire State Building Observation Deck',
                    'description': 'Take in spectacular views from the Empire State Building observation deck.',
                    'category': 'sightseeing',
                    'price': {
                        'amount': '42.00',
                        'currency': 'USD'
                    },
                    'duration': '60',
                    'location': 'Midtown Manhattan, New York',
                    'rating': 4.6,
                    'reviews_count': 4500
                },
                {
                    'id': 'act-nyc-2',
                    'name': 'Broadway Show Tickets',
                    'description': 'Experience the magic of Broadway with tickets to a top show.',
                    'category': 'entertainment',
                    'price': {
                        'amount': '120.00',
                        'currency': 'USD'
                    },
                    'duration': '180',
                    'location': 'Theater District, New York',
                    'rating': 4.9,
                    'reviews_count': 3200
                }
            ]
        }
        
        # Add generic activities for any location if needed
        generic_activities = [
            {
                'id': 'act-gen-1',
                'name': 'Local City Tour',
                'description': 'Discover the best sights of the city with a knowledgeable local guide.',
                'category': 'sightseeing',
                'price': {
                    'amount': '25.00',
                    'currency': 'GBP'
                },
                'duration': '180',
                'location': 'City Center',
                'rating': 4.5,
                'reviews_count': 850
            },
            {
                'id': 'act-gen-2',
                'name': 'Food Tasting Experience',
                'description': 'Sample local delicacies and learn about the local cuisine.',
                'category': 'food',
                'price': {
                    'amount': '45.00',
                    'currency': 'GBP'
                },
                'duration': '150',
                'location': 'Various Locations',
                'rating': 4.7,
                'reviews_count': 620
            },
            {
                'id': 'act-gen-3',
                'name': 'Historical Walking Tour',
                'description': 'Step back in time as you explore historical sites with an expert historian.',
                'category': 'culture',
                'price': {
                    'amount': '15.00',
                    'currency': 'GBP'
                },
                'duration': '120',
                'location': 'Historical District',
                'rating': 4.6,
                'reviews_count': 430
            }
        ]
        
        # Normalize location input
        normalized_location = location.upper() if location else ""
        
        # Find activities that match the location
        activities = []
        for loc, acts in mock_activities_by_location.items():
            if normalized_location in loc:
                activities.extend(acts)
        
        # If no activities found for the specific location, return generic ones
        if not activities:
            activities = generic_activities
        
        # Filter by category if provided
        if category:
            activities = [a for a in activities if category.lower() in a['category'].lower()]
        
        # Ensure all activities have prices/costs
        for activity in activities:
            if 'price' not in activity:
                activity['price'] = {
                    'amount': '25.00',  # Default price
                    'currency': 'GBP'
                }
        
        return {
            'status': 'success',
            'activities': activities
        }

def get_api_client():
    """
    Factory function to get an API client instance
    """
    print("\nChecking API credentials...")
    
    # Check Amadeus API credentials
    amadeus_client_id = os.environ.get('AMADEUS_CLIENT_ID')
    amadeus_client_secret = os.environ.get('AMADEUS_CLIENT_SECRET')
    
    print(f"AMADEUS_CLIENT_ID found: {'Yes' if amadeus_client_id else 'No'}")
    print(f"AMADEUS_CLIENT_SECRET found: {'Yes' if amadeus_client_secret else 'No'}")
    
    if amadeus_client_id and amadeus_client_secret:
        try:
            print("Using Amadeus client for flights")
            return AmadeusClient()
        except Exception as e:
            print(f"Error creating Amadeus client: {str(e)}")
            print("Falling back to mock API client...")
    else:
        print("No Amadeus API credentials found in environment variables.")
        print("Current environment variables:")
        for key, value in os.environ.items():
            if 'AMADEUS' in key:
                print(f"{key}: {'*' * len(value)}")  # Print masked value for security
    
    # Fall back to mock client if Amadeus fails or credentials are missing
    print("Using mock API client for development")
    return MockApiClient() 