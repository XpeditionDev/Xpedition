try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: NumPy not available. Recommendation features will be limited.")

from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import os
import pickle

class DestinationRecommender:
    def __init__(self):
        if not NUMPY_AVAILABLE:
            print("NumPy is required for recommendation functionality.")
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', 'destination_recommender.pkl')
        self.feature_dim = 10  # Number of features (interests + budget + duration)
        self.destinations = [
            'London', 'Paris', 'Rome', 'Barcelona', 'Amsterdam',
            'Berlin', 'Prague', 'Vienna', 'Venice', 'Madrid'
        ]
        
        # Create or load the model
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
                self.scaler = pickle.load(f)
        else:
            self.model = NearestNeighbors(n_neighbors=5, algorithm='ball_tree')
            self.scaler = StandardScaler()
            self._initialize_model()
    
    def _initialize_model(self):
        # Initialize with some sample data
        n_samples = len(self.destinations)
        X = np.random.rand(n_samples, self.feature_dim)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        
        # Save the model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
            pickle.dump(self.scaler, f)
    
    def get_destination_recommendations(self, user_preferences):
        """
        Generate destination recommendations based on user preferences
        
        Args:
            user_preferences: dict containing:
                - interests: list of interest categories
                - budget: float
                - duration: int (days)
                - previous_destinations: list of previously visited places
        
        Returns:
            List of recommended destinations with scores
        """
        # Convert preferences to feature vector
        features = self._encode_preferences(user_preferences)
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        # Get nearest neighbors
        distances, indices = self.model.kneighbors(features_scaled)
        
        # Convert to recommendations
        recommendations = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.destinations):
                score = 1 / (1 + dist)  # Convert distance to similarity score
                recommendations.append({
                    'name': self.destinations[idx],
                    'score': float(score),
                    'match_percentage': int(score * 100)
                })
        
        return recommendations
    
    def _encode_preferences(self, preferences):
        """Convert user preferences to a feature vector"""
        features = np.zeros(self.feature_dim)
        
        # Encode interests (first 7 dimensions)
        interest_categories = ['culture', 'historic', 'food', 'outdoors', 
                             'shopping', 'entertainment', 'sightseeing']
        for i, category in enumerate(interest_categories):
            if category in preferences['interests']:
                features[i] = 1
        
        # Encode normalized budget (8th dimension)
        features[7] = min(preferences['budget'] / 5000.0, 1.0)
        
        # Encode normalized duration (9th dimension)
        features[8] = min(preferences['duration'] / 30.0, 1.0)
        
        # Encode season (10th dimension)
        current_month = preferences.get('month', 1)
        features[9] = current_month / 12.0
        
        return features
    
    def train(self, X_train):
        """Train the model with new data"""
        X_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_scaled)
        
        # Save the trained model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
            pickle.dump(self.scaler, f) 