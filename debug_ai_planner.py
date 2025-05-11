import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the AI planner
from app.utils.ai_planner import ItineraryGenerator
from app.utils.recommendation_model import DestinationRecommender

# Create test preferences
test_preferences = {
    'destination': 'Paris',
    'start_date': '2023-12-01',
    'end_date': '2023-12-05',
    'budget': 2000,
    'interests': ['culture', 'food', 'sightseeing'],
    'duration': 5
}

# Initialize the components
try:
    print("Initializing DestinationRecommender...")
    recommender = DestinationRecommender()
    print("DestinationRecommender initialized successfully")
    
    print("\nInitializing ItineraryGenerator...")
    generator = ItineraryGenerator()
    print("ItineraryGenerator initialized successfully")
    
    # Try to generate recommendations
    print("\nGenerating destination recommendations...")
    recommendations = recommender.get_destination_recommendations(test_preferences)
    print(f"Recommendations generated: {recommendations}")
    
    # Try to generate an itinerary
    print("\nGenerating itinerary...")
    itinerary = generator.generate_itinerary(test_preferences)
    print("\nItinerary generated successfully!")
    print(f"Destination: {itinerary.get('destination')}")
    print(f"Duration: {itinerary.get('duration')} days")
    print(f"Number of days planned: {len(itinerary.get('days', []))}")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc() 