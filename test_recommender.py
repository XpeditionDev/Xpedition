import sys
print(f"Python version: {sys.version}")

try:
    from app.utils.neural_recommender import NeuralRecommender
    print("Successfully imported NeuralRecommender")
    
    # Create an instance of the recommender
    recommender = NeuralRecommender()
    print("Successfully created NeuralRecommender instance")
    
    # Test with some sample preferences
    test_preferences = {
        'interests': ['culture', 'food', 'history'],
        'budget': 2000,
        'duration': 7,
        'month': 6,
        'age': 30
    }
    
    # Get recommendations
    recommendations = recommender.get_destination_recommendations(test_preferences)
    print("\nTop 5 recommended destinations:")
    for i, rec in enumerate(recommendations[:5]):
        print(f"{i+1}. {rec['name']} - Match: {rec['match_percentage']}%")
    
    # Test similar destinations
    if hasattr(recommender, 'get_similar_destinations'):
        similar = recommender.get_similar_destinations('Paris')
        print("\nDestinations similar to Paris:")
        for i, dest in enumerate(similar):
            print(f"{i+1}. {dest['name']} - Similarity: {dest['similarity']:.2f}")
    
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")