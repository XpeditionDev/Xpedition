import sys
import os

# Add the parent directory to the path so we can import our app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import Flight
from app.extensions import db

# Initialize the Flask app
app = create_app()

def check_flight_prices():
    with app.app_context():
        # Check a sample of flights between LHR and JFK
        lhr_jfk_flights = Flight.query.filter_by(
            departure_airport='LHR', 
            arrival_airport='JFK'
        ).limit(5).all()
        
        print("Sample LHR to JFK flights:")
        for flight in lhr_jfk_flights:
            print(f"{flight.airline} {flight.flight_number}: {flight.departure_time} -> {flight.arrival_time}, £{flight.cost}")
        
        # Check the price range
        min_price = Flight.query.order_by(Flight.cost.asc()).first()
        max_price = Flight.query.order_by(Flight.cost.desc()).first()
        
        print("\nPrice range in database:")
        print(f"Minimum price: £{min_price.cost} ({min_price.departure_airport} to {min_price.arrival_airport})")
        print(f"Maximum price: £{max_price.cost} ({max_price.departure_airport} to {max_price.arrival_airport})")
        
        # Get average price
        from sqlalchemy import func
        avg_price = db.session.query(func.avg(Flight.cost)).scalar()
        print(f"Average flight price: £{avg_price:.2f}")

if __name__ == "__main__":
    check_flight_prices() 