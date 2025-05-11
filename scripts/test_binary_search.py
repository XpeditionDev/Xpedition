import sys
import os
import logging

# Add the parent directory to the path so we can import our app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app import create_app
from app.utils.binary_search import binary_search_flights_by_price
from app.models import Flight
from app.extensions import db

# Initialize the Flask app
app = create_app()

def test_binary_search():
    with app.app_context():
        # Check if there are flights in the database
        count = Flight.query.count()
        print(f"Number of flights in database: {count}")
        
        if count == 0:
            print("No flights found in database. Please run populate_flight_data.py first.")
            return
        
        # Find the min and max prices in the database
        min_price = db.session.query(db.func.min(Flight.cost)).scalar()
        max_price = db.session.query(db.func.max(Flight.cost)).scalar()
        
        print(f"Price range in database: £{min_price:.2f} to £{max_price:.2f}")
        
        # Try different target prices
        test_prices = [
            {"price": 500, "name": "Medium price range"},
            {"price": 200, "name": "Lower price range"},
            {"price": 800, "name": "Higher price range"}
        ]
        
        for test in test_prices:
            target_price = test["price"]
            print(f"\n=== Testing {test['name']}: £{target_price:.2f} ===")
            
            # Check if there are any flights in this price range directly
            direct_count = Flight.query.filter(
                Flight.cost >= target_price - 100,
                Flight.cost <= target_price + 100,
                Flight.departure_airport == "LHR",
                Flight.arrival_airport == "JFK"
            ).count()
            
            print(f"Direct SQL query found {direct_count} flights in price range £{target_price-100:.2f} to £{target_price+100:.2f}")
            
            # Perform binary search for flights from London to New York
            matches, performance = binary_search_flights_by_price(
                target_price=target_price,
                tolerance=100,
                origin="LHR",
                destination="JFK",
                adaptive_tolerance=True,
                collect_vis_data=True
            )
            
            # Print results
            print(f"Search results:")
            print(f"Execution time: {performance.get('duration_ms', 0):.2f} ms")
            print(f"Iterations: {performance.get('iterations', 0)}")
            print(f"Binary search found: {len(matches)} flights")
            
            if matches:
                print("\nSample matches:")
                for i, flight in enumerate(matches[:3]):  # Print first 3 matches
                    price_diff = abs(flight.cost - target_price)
                    print(f"{i+1}. {flight.airline} {flight.flight_number}: "
                          f"{flight.departure_airport} to {flight.arrival_airport}, "
                          f"£{flight.cost:.2f} (£{price_diff:.2f} from target)")
            else:
                print("No matching flights found.")

if __name__ == "__main__":
    test_binary_search() 