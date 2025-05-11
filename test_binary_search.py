import sys
import os

# First ensure all our app modules are in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try importing Flask and the other required modules
try:
    from flask import Flask
    from app.extensions import db
    print("Flask is installed and imported successfully.")
except ImportError as e:
    print(f"Error importing Flask: {e}")
    print("Please run: pip install flask flask-sqlalchemy flask-login flask-wtf python-dotenv")
    sys.exit(1)

# Create a simple Flask app and db instance for testing
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Import our binary search module
try:
    from app.utils.binary_search import binary_search_flights_by_price, linear_search_flights_by_price, compare_search_algorithms
    print("Binary search module imported successfully.")
except ImportError as e:
    print(f"Error importing binary search module: {e}")
    sys.exit(1)

# Create a simple Flight model for testing
from app.models.flight import Flight

# Mock data to test our binary search
MOCK_FLIGHTS = [
    {"departure_airport": "LHR", "arrival_airport": "JFK", "cost": 350.0, "airline": "British Airways"},
    {"departure_airport": "LHR", "arrival_airport": "JFK", "cost": 450.0, "airline": "Virgin Atlantic"},
    {"departure_airport": "LHR", "arrival_airport": "JFK", "cost": 550.0, "airline": "American Airlines"},
    {"departure_airport": "LHR", "arrival_airport": "JFK", "cost": 650.0, "airline": "Delta"},
    {"departure_airport": "LHR", "arrival_airport": "CDG", "cost": 150.0, "airline": "Air France"},
    {"departure_airport": "LHR", "arrival_airport": "CDG", "cost": 175.0, "airline": "British Airways"},
    {"departure_airport": "LHR", "arrival_airport": "BCN", "cost": 200.0, "airline": "Iberia"},
    {"departure_airport": "MAN", "arrival_airport": "JFK", "cost": 480.0, "airline": "Virgin Atlantic"},
    {"departure_airport": "MAN", "arrival_airport": "CDG", "cost": 170.0, "airline": "Air France"},
]

def setup_test_data():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Add mock flights
        for flight_data in MOCK_FLIGHTS:
            flight = Flight(
                departure_airport=flight_data["departure_airport"],
                arrival_airport=flight_data["arrival_airport"],
                cost=flight_data["cost"],
                airline=flight_data["airline"],
                # Add required fields with mock values
                itinerary_id=1,
                departure_time="2023-12-01 10:00:00",
                arrival_time="2023-12-01 12:00:00"
            )
            db.session.add(flight)
        
        # Commit changes
        db.session.commit()
        print(f"Added {len(MOCK_FLIGHTS)} test flights to the database.")

def test_binary_search():
    with app.app_context():
        print("\nTesting binary search...")
        target_price = 450.0
        tolerance = 50.0
        
        # Binary search
        binary_results, binary_metrics = binary_search_flights_by_price(
            target_price=target_price, 
            tolerance=tolerance
        )
        
        # Linear search
        linear_results, linear_metrics = linear_search_flights_by_price(
            target_price=target_price,
            tolerance=tolerance
        )
        
        # Compare results
        print(f"\nBinary search found {len(binary_results)} flights with target price {target_price} (±{tolerance})")
        for flight in binary_results:
            print(f"  - {flight.airline}: {flight.departure_airport} to {flight.arrival_airport}, £{flight.cost}")
        
        print(f"\nLinear search found {len(linear_results)} flights with target price {target_price} (±{tolerance})")
        for flight in linear_results:
            print(f"  - {flight.airline}: {flight.departure_airport} to {flight.arrival_airport}, £{flight.cost}")
        
        # Performance comparison
        print("\nPerformance comparison:")
        print(f"  Binary search: {binary_metrics['execution_time']*1000:.2f}ms, {binary_metrics['iterations']} iterations, {binary_metrics['comparisons']} DB queries")
        print(f"  Linear search: {linear_metrics['execution_time']*1000:.2f}ms, {linear_metrics['comparisons']} DB queries")

if __name__ == "__main__":
    print("Testing binary search implementation...")
    try:
        # Setup test data
        setup_test_data()
        
        # Test binary search
        test_binary_search()
        
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"Error testing binary search: {e}")
        import traceback
        traceback.print_exc() 