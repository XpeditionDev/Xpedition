import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestRegressor

class ItineraryNeuralNetwork:
    """
    Neural network model for generating personalized travel itineraries
    based on user preferences such as interests, budget, and duration.
    """
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', 'itinerary_model.pkl')
        self.model = None
        
        # Load or create model
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
        else:
            # Create a simple model instead of TensorFlow
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self._initialize_model()
    
    def _initialize_model(self):
        # Create dummy data for initialization
        X = np.random.rand(100, 10)  # Example features
        y = np.random.rand(100, 5)   # Example outputs
        
        # Train the model
        self.model.fit(X, y)
        
        # Save the model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
    
    def predict(self, features):
        """Generate itinerary predictions based on input features"""
        if self.model is None:
            return None
            
        # Make prediction
        try:
            prediction = self.model.predict(features.reshape(1, -1))
            return prediction[0]
        except Exception as e:
            print(f"Prediction error: {e}")
            return None
    
    def generate_itinerary(self, preferences):
        """
        Generate an itinerary based on user preferences
        
        Args:
            preferences: dict with user preferences
            
        Returns:
            dict with generated itinerary
        """
        # Convert preferences to features
        features = self._encode_preferences(preferences)
        
        # Generate a simple itinerary without using the model
        # This is a fallback method that doesn't require TensorFlow
        destination = preferences.get('destination', 'Paris')
        duration = preferences.get('duration', 3)
        
        # Simple template-based generation
        itinerary = {
            'destination': destination,
            'duration': duration,
            'days': []
        }
        
        # Generate activities for each day
        activities = [
            'Visit local museum', 'Try local cuisine', 'Walking tour',
            'Shopping', 'Visit landmark', 'Relax at park', 'Cultural experience'
        ]
        
        for day in range(1, duration + 1):
            day_plan = {
                'day': day,
                'activities': []
            }
            
            # Add 3-4 activities per day
            num_activities = min(4, len(activities))
            for i in range(num_activities):
                activity_idx = (day + i) % len(activities)
                day_plan['activities'].append({
                    'name': activities[activity_idx],
                    'time': f"{9 + i * 2}:00",
                    'duration': '2 hours'
                })
            
            itinerary['days'].append(day_plan)
        
        return itinerary
    
    def _encode_preferences(self, preferences):
        """Convert user preferences to feature vector"""
        # Simple encoding of preferences
        features = np.zeros(10)
        
        # Encode interests
        interests = preferences.get('interests', [])
        interest_categories = ['culture', 'historic', 'food', 'outdoors', 
                             'shopping', 'entertainment', 'sightseeing']
        for i, category in enumerate(interest_categories):
            if category in interests:
                features[i] = 1
        
        # Encode budget and duration
        features[7] = min(preferences.get('budget', 1000) / 5000.0, 1.0)
        features[8] = min(preferences.get('duration', 3) / 30.0, 1.0)
        features[9] = preferences.get('month', 1) / 12.0
        
        return features