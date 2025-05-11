from app import create_app, db
from app.models import Itinerary, Flight
from flask_login import current_user
from datetime import datetime
import json

app = create_app()

def save_test_flight():
    """
    This function tests saving a flight to a new itinerary.
    It uses the simplest possible data structure.
    """
    with app.app_context():
        # Create a test flight with the flattened structure
        flight_data = {
            "departure": {
                "airport": "LHR",
                "time": "2023-08-15T10:00:00Z",
                "city": "London"
            },
            "arrival": {
                "airport": "JFK",
                "time": "2023-08-15T13:00:00Z",
                "city": "New York"
            },
            "airline": "British Airways",
            "price": {
                "total": 500,
                "currency": "GBP",
                "display": "Â£500"
            },
            "booking_reference": "TEST123",
            "stops": 0,
            "duration": "8h 00m"
        }
        
        # Extract flight data
        departure_airport = flight_data['departure']['airport']
        arrival_airport = flight_data['arrival']['airport']
        departure_time = datetime.fromisoformat(flight_data['departure']['time'].replace('Z', '+00:00'))
        arrival_time = datetime.fromisoformat(flight_data['arrival']['time'].replace('Z', '+00:00'))
        airline = flight_data.get('airline', '')
        price = flight_data['price']['total'] if isinstance(flight_data.get('price'), dict) else flight_data.get('price', 0)
        booking_reference = flight_data.get('booking_reference', '')
        stops = flight_data.get('stops', 0)
        duration = flight_data.get('duration', '')
        
        # Create a new itinerary
        itinerary = Itinerary(
            name="Test Itinerary",
            user_id=1,  # Use your actual user ID here
            start_date=datetime.now(),
            end_date=datetime.now()
        )
        db.session.add(itinerary)
        db.session.commit()
        
        # Create a new flight
        flight = Flight(
            itinerary_id=itinerary.id,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            departure_time=departure_time,
            arrival_time=arrival_time,
            airline=airline,
            cost=price,
            booking_reference=booking_reference
        )
        
        db.session.add(flight)
        db.session.commit()
        
        print(f"Successfully saved flight {flight.id} to itinerary {itinerary.id}")
        return flight, itinerary

if __name__ == "__main__":
    save_test_flight() 