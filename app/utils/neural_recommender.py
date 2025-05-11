import os
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NeuralRecommender:
    def __init__(self):
        # Create models directory path
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        self.model_path = os.path.join(models_dir, 'neural_recommender.pkl')
        self.scaler_path = os.path.join(models_dir, 'neural_scaler.pkl')
        self.knn_path = os.path.join(models_dir, 'knn_model.pkl')
        
        # Popular destinations list
        self.destinations = [
            'London', 'Paris', 'Rome', 'Barcelona', 'Amsterdam',
            'Berlin', 'Prague', 'Vienna', 'Venice', 'Madrid',
            'New York', 'Tokyo', 'Sydney', 'Dubai', 'Bangkok',
            'Hong Kong', 'Singapore', 'Istanbul', 'Athens', 'Budapest'
        ]
        
        # Feature mapping for interests
        self.interest_mapping = {
            'beach': 0, 'mountains': 1, 'city': 2, 'culture': 3, 
            'food': 4, 'adventure': 5, 'relaxation': 6, 'history': 7
        }
        
        self.feature_dim = 12  # interests + budget + duration + season + age
        
        # Create models directory if it doesn't exist
        os.makedirs(models_dir, exist_ok=True)
        
        # Try to load existing model or create a new one
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                # Load KNN model if it exists
                if os.path.exists(self.knn_path):
                    with open(self.knn_path, 'rb') as f:
                        self.knn_model = pickle.load(f)
                else:
                    self.knn_model = self._create_knn_model()
                logger.info("Loaded existing recommender models")
            else:
                logger.info("Initializing new recommender models")
                self.model = self._create_model()
                self.scaler = StandardScaler()
                self.knn_model = self._create_knn_model()
                self._initialize_model()
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            # Create fallback models
            self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            self.scaler = StandardScaler()
            self.knn_model = NearestNeighbors(n_neighbors=5, algorithm='auto')
            self._initialize_model()
    
    def _create_model(self):
        """Create a scikit-learn model for destination recommendations"""
        return RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
    
    def _create_knn_model(self):
        """Create a KNN model for finding similar destinations"""
        return NearestNeighbors(n_neighbors=5, algorithm='auto')
    
    def _initialize_model(self):
        """Initialize the model with synthetic data"""
        try:
            # Generate synthetic training data
            n_samples = 1000
            X = np.random.rand(n_samples, self.feature_dim)
            
            # Scale the features
            X_scaled = self.scaler.fit_transform(X)
            
            # Generate some random labels (one destination per sample)
            y = np.random.randint(0, len(self.destinations), size=n_samples)
            
            # Train the model
            self.model.fit(X_scaled, y)
            
            # Create destination embeddings for KNN model
            # Simple embedding: one-hot encoding with some noise
            dest_features = np.eye(len(self.destinations)) + np.random.rand(len(self.destinations), len(self.destinations)) * 0.1
            self.knn_model.fit(dest_features)
            
            # Save models
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            with open(self.knn_path, 'wb') as f:
                pickle.dump(self.knn_model, f)
                
            logger.info("Successfully initialized and saved recommender models")
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            # Don't fail the application if model initialization fails
    
    def get_destination_recommendations(self, user_preferences):
        """
        Generate destination recommendations based on user preferences
        
        Args:
            user_preferences: dict containing:
                - interests: list of interest categories (strings)
                - budget: float (budget in currency)
                - duration: int (duration in days)
                - month: int (1-12, representing travel month)
                - age: int (optional, age of traveler)
                - previous_destinations: list (optional, previously visited places)
        
        Returns:
            List of recommended destinations with scores
        """
        try:
            # Encode user preferences into feature vector
            features = self._encode_preferences(user_preferences)
            
            # Scale features - Fix: Use features as np.ndarray instead of list
            features_array = np.array([features])
            scaled_features = self.scaler.transform(features_array)
            
            # Get probabilities for each destination
            probabilities = self.model.predict_proba(scaled_features)[0]
            
            # Create recommendations list with confidence scores
            recommendations = [
                {
                    'destination': self.destinations[i],
                    'score': float(probabilities[i]),
                    'description': self._get_destination_description(self.destinations[i]),
                    'image_url': f'/static/images/destinations/{self.destinations[i].lower().replace(" ", "_")}.jpg'
                }
                for i in range(len(self.destinations))
            ]
            
            # Sort by score (highest first)
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            # Return top 5 recommendations
            return recommendations[:5]
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            # Fallback: return some popular destinations
            return self._get_fallback_recommendations()
    
    def _encode_preferences(self, preferences):
        """
        Encode user preferences into feature vector
        """
        features = np.zeros(self.feature_dim)
        
        # Encode interests (first 8 features)
        for interest in preferences.get('interests', []):
            if interest in self.interest_mapping:
                features[self.interest_mapping[interest]] = 1.0
        
        # Budget (normalized)
        budget = preferences.get('budget', 1000)
        features[8] = min(budget / 5000, 1.0)  # Cap at 5000
        
        # Duration (normalized)
        duration = preferences.get('duration', 7)
        features[9] = min(duration / 30, 1.0)  # Cap at 30 days
        
        # Season/month (normalized)
        month = preferences.get('month', datetime.now().month)
        features[10] = month / 12.0
        
        # Age (normalized)
        age = preferences.get('age', 30)
        features[11] = min(age / 100, 1.0)  # Cap at 100
        
        return features
    
    def _get_fallback_recommendations(self):
        """Return fallback recommendations if model fails"""
        return [
            {
                'destination': 'Paris',
                'score': 0.95,
                'description': 'The romantic capital of France with iconic landmarks.',
                'image_url': '/static/images/destinations/paris.jpg'
            },
            {
                'destination': 'Rome',
                'score': 0.92,
                'description': 'The eternal city with ancient history and amazing cuisine.',
                'image_url': '/static/images/destinations/rome.jpg'
            },
            {
                'destination': 'London',
                'score': 0.88,
                'description': 'A vibrant metropolis with rich history and culture.',
                'image_url': '/static/images/destinations/london.jpg'
            },
            {
                'destination': 'Tokyo',
                'score': 0.85,
                'description': 'Ultra-modern city with a perfect blend of tradition.',
                'image_url': '/static/images/destinations/tokyo.jpg'
            },
            {
                'destination': 'New York',
                'score': 0.82,
                'description': 'The city that never sleeps with endless attractions.',
                'image_url': '/static/images/destinations/new_york.jpg'
            }
        ]
    
    def _get_destination_description(self, destination):
        """Generate a description for a destination"""
        descriptions = {
            'London': 'A vibrant metropolis with royal heritage and modern attractions.',
            'Paris': 'The romantic capital of France with iconic landmarks.',
            'Rome': 'The eternal city with ancient history and amazing cuisine.',
            'Barcelona': 'Stunning architecture and Mediterranean beaches.',
            'Amsterdam': 'Beautiful canals and rich cultural heritage.',
            'Berlin': 'A hub of history, art, and vibrant nightlife.',
            'Prague': 'Fairytale architecture and rich cultural history.',
            'Vienna': 'Imperial palaces and world-class musical heritage.',
            'Venice': 'Romantic canal city with unique architecture.',
            'Madrid': 'Spain\'s lively capital with great food and museums.',
            'New York': 'The city that never sleeps with endless attractions.',
            'Tokyo': 'Ultra-modern city with a perfect blend of tradition.',
            'Sydney': 'Stunning harbor city with magnificent beaches.',
            'Dubai': 'Futuristic architecture and luxury experiences.',
            'Bangkok': 'Vibrant street life and ornate shrines.',
            'Hong Kong': 'Skyscrapers and shopping with traditional roots.',
            'Singapore': 'Clean, green urban oasis with diverse culture.',
            'Istanbul': 'Where East meets West with rich historical sites.',
            'Athens': 'The cradle of Western civilization.',
            'Budapest': 'Thermal baths and stunning Gothic architecture.'
        }
        return descriptions.get(destination, 'A fascinating destination waiting to be explored.')
    
    def get_similar_destinations(self, destination_name, n=3):
        """Find destinations similar to the given one"""
        try:
            # Find the index of the destination
            if destination_name in self.destinations:
                idx = self.destinations.index(destination_name)
                
                # Get nearest neighbors - Fix: Use np.array directly instead of wrapping in list
                dest_vector = np.eye(len(self.destinations))[idx]
                dest_vector_reshaped = dest_vector.reshape(1, -1)  # Reshape to 2D array
                distances, indices = self.knn_model.kneighbors(dest_vector_reshaped)
                
                # Return similar destinations (excluding the input destination)
                similar = [
                    {
                        'destination': self.destinations[i],
                        'similarity': float(1.0 - distances[0][j]),
                        'description': self._get_destination_description(self.destinations[i]),
                        'image_url': f'/static/images/destinations/{self.destinations[i].lower().replace(" ", "_")}.jpg'
                    }
                    for j, i in enumerate(indices[0]) if self.destinations[i] != destination_name
                ]
                
                return similar[:n]
            else:
                # If destination not found, return some popular alternatives
                return self._get_fallback_recommendations()[:n]
        except Exception as e:
            logger.error(f"Error finding similar destinations: {str(e)}")
            return self._get_fallback_recommendations()[:n]