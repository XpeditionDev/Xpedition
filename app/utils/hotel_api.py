import requests
import os
from datetime import datetime, timedelta
import json
import random
import time
import logging
import traceback
import subprocess
from flask import current_app

class RapidAPIHotelClient:
    """
    Client for the Hotels API from RapidAPI
    Free tier available with limited requests per month
    """
    
    def __init__(self):
        # Get API key from Flask application configuration
        try:
            from flask import current_app
            self.api_key = current_app.config.get('RAPIDAPI_KEY', '')
            print(f"Got RapidAPI key from Flask app config: {self.api_key[:6]}...{self.api_key[-4:]}")
        except Exception as e:
            print(f"Error getting key from Flask config: {e}")
            # Fallback to direct import from Config
            try:
                from config import Config
                self.api_key = Config.RAPIDAPI_KEY
                print(f"Got RapidAPI key from Config: {self.api_key[:6]}...{self.api_key[-4:]}")
            except Exception as e:
                print(f"Error getting key from Config: {e}")
                # Final fallback to environment variable
                self.api_key = os.environ.get('RAPIDAPI_KEY', '')
                if self.api_key:
                    print(f"Got RapidAPI key from environment: {self.api_key[:6]}...{self.api_key[-4:]}")
                else:
                    print("WARNING: Could not get RAPIDAPI_KEY from any source")
                
        self.api_host = 'hotels4.p.rapidapi.com'
        self.base_url = 'https://hotels4.p.rapidapi.com'
        
        # Print debug information about the API key
        if not self.api_key:
            print("CRITICAL: No RapidAPI key found in any source")
        else:
            masked_key = self.api_key[:6] + '*' * (len(self.api_key) - 10) + self.api_key[-4:]
            print(f"RapidAPIHotelClient initialized with API key: {masked_key}")
        
        # Default headers for all requests
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }
    
    def search_hotels(self, city_code, check_in_date, check_out_date, adults=1, rooms=1, currency='GBP'):
        """
        Search for hotels using the RapidAPI Hotels API
        """
        try:
            # CRITICAL FIX: Directly use the hardcoded API key for the RapidAPI
            # This ensures we're not relying on environment variables that might not be passed correctly
            hardcoded_api_key = '3ef65386aamsh420e793f0b72475p1ac5dajsne8a6ce37783b'
            
            # Check if the API key is available
            if not self.api_key:
                print("API key is not set in the client, using hardcoded key")
                self.api_key = hardcoded_api_key
                # Update headers as well
                self.headers['X-RapidAPI-Key'] = self.api_key
                
            # Double check that the headers have the correct API key
            if self.headers['X-RapidAPI-Key'] != self.api_key:
                print("API key mismatch in headers, updating with current key")
                self.headers['X-RapidAPI-Key'] = self.api_key
                
            # Print current API key (masked)
            masked_key = self.api_key[:6] + '*****' + self.api_key[-4:]
            print(f"Using RapidAPI key for hotel search: {masked_key}")
            
            # Format dates for API (YYYY-MM-DD)
            check_in_str = check_in_date.strftime('%Y-%m-%d')
            check_out_str = check_out_date.strftime('%Y-%m-%d')
            
            print(f"DEBUG: Starting hotel search for {city_code} from {check_in_str} to {check_out_str}")
            print(f"DEBUG: Using API host: {self.api_host}")
            print(f"DEBUG: Adult count: {adults}, Room count: {rooms}")
            
            # First, we need to get the destination ID for the city
            destination_id = self._get_destination_id(city_code)
            
            if not destination_id:
                print(f"ERROR: Could not find destination ID for city code: {city_code}")
                print("DEBUG: Try using an airport code like LHR (London) or CDG (Paris) instead")
                return {
                    'status': 'error',
                    'message': f'Unable to find destination ID for {city_code}. Try using an airport code instead (e.g., LHR for London).',
                    'hotels': []
                }
            
            print(f"DEBUG: Found destination ID: {destination_id} for {city_code}")
            
            # Now perform the initial hotel search to get a search ID
            search_url = f"{self.base_url}/v2/hotels/search"
            print(f"DEBUG: Search URL: {search_url}")
            
            search_payload = {
                "currency": currency,
                "locale": "en_US",
                "destination": {"regionId": destination_id},
                "checkInDate": {
                    "day": int(check_in_date.strftime('%d')),
                    "month": int(check_in_date.strftime('%m')),
                    "year": int(check_in_date.strftime('%Y'))
                },
                "checkOutDate": {
                    "day": int(check_out_date.strftime('%d')),
                    "month": int(check_out_date.strftime('%m')),
                    "year": int(check_out_date.strftime('%Y'))
                },
                "rooms": [{"adults": adults}] * rooms,
                "resultsStartingIndex": 0,
                "resultsSize": 10,
                "sort": "PRICE_LOW_TO_HIGH"
            }
            
            print(f"DEBUG: Request payload: {json.dumps(search_payload, indent=2)}")
            print(f"DEBUG: Headers: X-RapidAPI-Host: {self.headers['X-RapidAPI-Host']}, X-RapidAPI-Key: {'*' * 10}")
            
            print(f"Initiating hotel search for {city_code}...")
            response = requests.post(search_url, json=search_payload, headers=self.headers)
            
            print(f"DEBUG: Initial search response status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"ERROR: Initial search failed with status code: {response.status_code}")
                try:
                    error_json = response.json()
                    print(f"DEBUG: Error response: {json.dumps(error_json, indent=2)}")
                except:
                    print(f"DEBUG: Error response text: {response.text}")
                
                return {
                    'status': 'error',
                    'message': f'API Error: {response.status_code} - {response.text}',
                    'hotels': []
                }
            
            # Get the search ID from the response
            data = response.json()
            print(f"DEBUG: Initial search response: {json.dumps(data, indent=2)[:500]}...")
            
            search_id = data.get('searchId')
            
            if not search_id:
                print("ERROR: No search ID found in the response")
                return {
                    'status': 'error',
                    'message': 'No search ID found in the response',
                    'hotels': []
                }
                
            print(f"Got search ID: {search_id}, now polling for results...")
            
            # Poll for results using the search ID
            poll_url = f"{self.base_url}/v2/hotels/search/polls"
            poll_headers = self.headers.copy()
            # The API requires us to poll multiple times until completionPercentage = 100
            
            max_attempts = 5
            current_attempt = 0
            hotels_data = None
            
            while current_attempt < max_attempts:
                current_attempt += 1
                print(f"DEBUG: Polling attempt {current_attempt}/{max_attempts} for search results")
                
                poll_response = requests.get(
                    poll_url,
                    headers=poll_headers,
                    params={"searchId": search_id}
                )
                
                print(f"DEBUG: Poll response status code: {poll_response.status_code}")
                
                if poll_response.status_code != 200:
                    print(f"ERROR: Polling failed with status code: {poll_response.status_code}")
                    try:
                        error_json = poll_response.json()
                        print(f"DEBUG: Error response: {json.dumps(error_json, indent=2)}")
                    except:
                        print(f"DEBUG: Error response text: {poll_response.text}")
                    # If we failed polling, try again
                    continue
                
                poll_data = poll_response.json()
                completion_percentage = poll_data.get('data', {}).get('status', {}).get('completionPercentage', 0)
                print(f"Polling attempt {current_attempt}: Completion {completion_percentage}%")
                
                # If search is complete
                if completion_percentage == 100:
                    hotels_data = poll_data
                    break
                    
                # If not complete, wait and try again
                print(f"DEBUG: Waiting 2 seconds before next polling attempt...")
                time.sleep(2)  # Wait 2 seconds between polls
            
            # If we couldn't get results after max attempts
            if not hotels_data:
                print("ERROR: Failed to get hotel results after maximum polling attempts")
                return {
                    'status': 'error',
                    'message': 'Failed to get hotel results after maximum polling attempts',
                    'hotels': []
                }
            
            # Process the response data
            properties = hotels_data.get('data', {}).get('propertySearch', {}).get('properties', [])
            print(f"Found {len(properties)} hotels")
            
            if len(properties) == 0:
                print("WARNING: No properties found in the API response")
                if 'data' in hotels_data and 'propertySearch' in hotels_data['data']:
                    print(f"DEBUG: Property search data: {json.dumps(hotels_data['data']['propertySearch'], indent=2)[:500]}...")
            
            # Format the hotel data in the expected format for our application
            formatted_hotels = []
            for prop in properties:
                # Skip properties without price info
                if not prop.get('price') or not prop.get('id'):
                    print(f"DEBUG: Skipping hotel without price or ID: {prop.get('name', 'Unknown Hotel')}")
                    continue
                    
                hotel_info = {
                    'hotel_id': prop.get('id', ''),
                    'name': prop.get('name', 'Unknown Hotel'),
                    'rating': str(prop.get('star', 3)),
                    'address': {
                        'city': prop.get('neighborhood', {}).get('name', city_code),
                        'country': 'Not Available'  # RapidAPI doesn't always provide country in basic response
                    },
                    'offers': []
                }
                
                # Add the primary offer
                price_info = prop.get('price', {})
                
                offer = {
                    'id': f"{prop.get('id')}-1",  # Create a unique offer ID
                    'price': {
                        'total': price_info.get('lead', {}).get('amount', '0'),
                        'currency': currency
                    },
                    'room_type': prop.get('type', 'STANDARD'),
                    'guests': {
                        'adults': adults
                    },
                    'check_in': check_in_str,
                    'check_out': check_out_str
                }
                
                hotel_info['offers'].append(offer)
                
                # If there are multiple room types, add them as additional offers
                if prop.get('roomTypes'):
                    for idx, room_type in enumerate(prop.get('roomTypes', [])):
                        # Skip if room price isn't available
                        if not room_type.get('price'):
                            continue
                            
                        additional_offer = {
                            'id': f"{prop.get('id')}-{idx+2}",
                            'price': {
                                'total': room_type.get('price', {}).get('lead', {}).get('amount', '0'),
                                'currency': currency
                            },
                            'room_type': room_type.get('name', 'DELUXE'),
                            'guests': {
                                'adults': adults
                            },
                            'check_in': check_in_str,
                            'check_out': check_out_str
                        }
                        
                        hotel_info['offers'].append(additional_offer)
                
                formatted_hotels.append(hotel_info)
            
            if not formatted_hotels:
                print("WARNING: No hotel results found after formatting")
            else:
                print(f"DEBUG: Successfully formatted {len(formatted_hotels)} hotels")
            
            return {
                'status': 'success',
                'hotels': formatted_hotels
            }
            
        except Exception as e:
            print(f"ERROR in RapidAPI hotel search: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'An error occurred: {str(e)}',
                'hotels': []
            }
    
    def _get_destination_id(self, city_code):
        """
        Get destination ID for a city code or name using the locations/v3/search API
        """
        try:
            print(f"DEBUG: Getting destination ID for city code: {city_code}")
            url = f"{self.base_url}/locations/v3/search"
            
            querystring = {
                "q": city_code,
                "locale": "en_US",
                "langid": "1033",
                "siteid": "300000001"
            }
            
            print(f"DEBUG: Location search URL: {url}")
            print(f"DEBUG: Location search query parameters: {querystring}")
            
            response = requests.get(url, headers=self.headers, params=querystring)
            
            print(f"DEBUG: Location search response status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"ERROR getting destination ID: {response.status_code}")
                try:
                    error_json = response.json()
                    print(f"DEBUG: Error response: {json.dumps(error_json, indent=2)}")
                except:
                    print(f"DEBUG: Error response text: {response.text}")
                return None
            
            data = response.json()
            print(f"DEBUG: Location search response data: {json.dumps(data, indent=2)[:500]}...")
            
            # Look for the first city/region result
            for suggestion in data.get('sr', []):
                if suggestion.get('type') in ['CITY', 'REGION']:
                    print(f"DEBUG: Found city/region destination ID: {suggestion.get('gaiaId')} for {suggestion.get('regionNames', {}).get('displayName', 'Unknown')}")
                    return suggestion.get('gaiaId')
            
            # If no city/region found, try any destination type
            for suggestion in data.get('sr', []):
                if suggestion.get('gaiaId'):
                    print(f"DEBUG: Found fallback destination ID: {suggestion.get('gaiaId')} of type {suggestion.get('type', 'Unknown')}")
                    return suggestion.get('gaiaId')
            
            print(f"ERROR: Could not find any destination ID for {city_code} in the API response")
            return None
            
        except Exception as e:
            print(f"ERROR getting destination ID: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


class MockHotelClient:
    """
    Mock client for hotel searches when API is not available
    """
    
    def search_hotels(self, city_code, check_in_date, check_out_date, adults=1, rooms=1, currency='GBP'):
        """
        Mock hotel search for development/testing
        """
        check_in_str = check_in_date.strftime('%Y-%m-%d')
        check_out_str = check_out_date.strftime('%Y-%m-%d')
        
        # Common city codes and their names
        city_name_map = {
            'LON': 'London',
            'PAR': 'Paris',
            'NYC': 'New York',
            'ROM': 'Rome',
            'BCN': 'Barcelona',
            'JFK': 'New York', 
            'LHR': 'London',
            'CDG': 'Paris',
            'MAD': 'Madrid',
            'LIS': 'Lisbon'
        }
        
        city_name = city_name_map.get(city_code, f'City {city_code}')
        country_map = {
            'LON': 'United Kingdom',
            'LHR': 'United Kingdom',
            'PAR': 'France',
            'CDG': 'France',
            'NYC': 'United States',
            'JFK': 'United States',
            'ROM': 'Italy',
            'BCN': 'Spain',
            'MAD': 'Spain',
            'LIS': 'Portugal'
        }
        country = country_map.get(city_code, 'Country')
        
        # Generate multiple mock hotels for a better testing experience
        mock_hotels = []
        
        hotel_types = ['Grand Hotel', 'Boutique Hotel', 'Plaza Hotel', 'Riverside Inn', 'City Center Hotel']
        room_types = ['STANDARD', 'DELUXE', 'SUITE', 'ECONOMY', 'EXECUTIVE']
        
        for i in range(1, 6):  # Generate 5 different mock hotels
            price_base = 100 + (i * 20)  # Different price points
            hotel_name = f"{hotel_types[i-1]} {city_name}"
            rating = min(5, max(3, i))  # Ratings between 3 and 5
            
            hotel = {
                'hotel_id': f'mock-hotel-{i}',
                'name': hotel_name,
                'rating': str(rating),
                'address': {
                    'city': city_name,
                    'country': country
                },
                'offers': []
            }
            
            # Add 1-2 offers per hotel
            for j in range(1, 3):
                price_total = price_base + (j * 30)
                offer = {
                    'id': f'mock-offer-{i}-{j}',
                    'price': {
                        'total': f'{price_total}.99',
                        'currency': currency
                    },
                    'room_type': room_types[(i+j-2) % len(room_types)],
                    'guests': {
                        'adults': adults
                    },
                    'check_in': check_in_str,
                    'check_out': check_out_str
                }
                hotel['offers'].append(offer)
            
            mock_hotels.append(hotel)
        
        mock_results = {
            'status': 'success',
            'hotels': mock_hotels
        }
        
        return mock_results


def get_hotel_client():
    """
    Returns an appropriate hotel client, either real RapidAPI client or mock client
    """
    try:
        # Try to get the API key from the Flask config
        try:
            from flask import current_app
            api_key = current_app.config.get('RAPIDAPI_KEY', '')
            if api_key:
                print(f"Using API key from Flask config: {api_key[:6]}...{api_key[-4:]}")
        except Exception as e:
            print(f"Error accessing Flask config: {e}")
            api_key = None
                
        # If not found in Flask config, try direct import from Config
        if not api_key:
            try:
                from config import Config
                api_key = Config.RAPIDAPI_KEY
                if api_key:
                    print(f"Using API key from Config: {api_key[:6]}...{api_key[-4:]}")
            except Exception as e:
                print(f"Error importing Config: {e}")
                api_key = None
                
        # Last resort: environment variable
        if not api_key:
            api_key = os.environ.get('RAPIDAPI_KEY')
            if api_key:
                print(f"Using API key from environment: {api_key[:6]}...{api_key[-4:]}")
        
        # Validate the API key
        if api_key and len(api_key) > 20:  # A reasonable minimum length for API keys
            print(f"Using RapidAPIHotelClient with valid API key")
            return RapidAPIHotelClient()
        else:
            print("Invalid or missing API key, falling back to MockHotelClient")
            return MockHotelClient()
    except Exception as e:
        print(f"Exception in get_hotel_client: {e}")
        print("Falling back to MockHotelClient due to exception")
        return MockHotelClient()

class HotelAPIClient:
    """API client for hotel search and booking."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        
    def search_hotels(self, city_code, check_in_date, check_out_date, adults=1, rooms=1):
        """
        Search for hotels based on the given parameters.
        In a real implementation, this would call an external API service.
        
        Returns:
            dict: A dictionary containing hotel search results or error information.
        """
        # This is a mock implementation that would be replaced with actual API calls
        return {
            'status': 'success',
            'hotels': []
        }
        
    def get_hotel_details(self, hotel_id):
        """
        Get detailed information about a specific hotel.
        
        Args:
            hotel_id (str): The ID of the hotel to retrieve details for.
            
        Returns:
            dict: Hotel details or error information.
        """
        # Mock implementation
        return {
            'status': 'success',
            'hotel': {}
        }
        
    def book_hotel(self, hotel_id, offer_id, guest_details):
        """
        Book a hotel room for the given guests.
        
        Args:
            hotel_id (str): The ID of the hotel to book.
            offer_id (str): The ID of the specific offer/room to book.
            guest_details (dict): Information about the guests.
            
        Returns:
            dict: Booking confirmation or error information.
        """
        # Mock implementation
        return {
            'status': 'success',
            'booking_reference': 'HTL456',
            'message': 'Hotel booked successfully'
        } 