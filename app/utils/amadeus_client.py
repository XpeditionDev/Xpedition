from amadeus import Client, ResponseError
import os
from datetime import datetime

class AmadeusAPI:
    def __init__(self):
        self.amadeus = Client(
            client_id=os.getenv('AMADEUS_CLIENT_ID'),
            client_secret=os.getenv('AMADEUS_CLIENT_SECRET'),
            hostname='test'
        )

    def search_flights(self, origin, destination, departure_date):
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date.strftime('%Y-%m-%d'),
                adults=1,
                max=5
            )
            return response.data
        except ResponseError as e:
            print(f"Flight search error: {str(e)}")
            return None

    def search_hotels(self, city_code, check_in, check_out):
        try:
            # First get hotel list
            hotels = self.amadeus.reference_data.locations.hotels.by_city.get(
                cityCode=city_code
            )
            
            # Then get offers for the first few hotels
            hotel_offers = []
            for hotel in hotels.data[:5]:  # Limit to 5 hotels
                try:
                    offers = self.amadeus.shopping.hotel_offers_search.get(
                        hotelIds=hotel['hotelId'],
                        checkInDate=check_in.strftime('%Y-%m-%d'),
                        checkOutDate=check_out.strftime('%Y-%m-%d')
                    )
                    hotel_offers.extend(offers.data)
                except ResponseError:
                    continue
                    
            return hotel_offers
        except ResponseError as e:
            print(f"Hotel search error: {str(e)}")
            return None

    def search_activities(self, latitude, longitude):
        try:
            activities = self.amadeus.shopping.activities.get(
                latitude=latitude,
                longitude=longitude
            )
            return activities.data
        except ResponseError as e:
            print(f"Activity search error: {str(e)}")
            return None

    def get_city_code(self, city_name):
        try:
            response = self.amadeus.reference_data.locations.get(
                keyword=city_name,
                subType=["CITY"]
            )
            if response.data:
                return response.data[0]['iataCode']
            return None
        except ResponseError as e:
            print(f"City search error: {str(e)}")
            return None 