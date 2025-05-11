import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import os
import pickle
from datetime import datetime

class PricePredictor:
    def __init__(self, model_type='flight'):
        self.model_type = model_type
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', f'{model_type}_price_predictor.pkl')
        
        # Different input dimensions for flight vs hotel predictions
        self.feature_dim = 12 if model_type == 'flight' else 8
        
        # Create or load the model
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
                self.scaler = pickle.load(f)
        else:
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()
            self._initialize_model()
    
    def _initialize_model(self):
        # Initialize with some sample data
        n_samples = 1000
        X = np.random.rand(n_samples, self.feature_dim)
        y = np.random.uniform(50, 1000, n_samples)  # Random prices between 50 and 1000
        
        # Fit the model with sample data
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        
        # Save the model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
            pickle.dump(self.scaler, f)
    
    def predict_price(self, features):
        """
        Predict price based on features
        
        Args:
            features: dict containing relevant features for prediction
                For flights: departure_city, arrival_city, date, class, etc.
                For hotels: city, dates, room_type, amenities, etc.
        
        Returns:
            Predicted price and confidence interval
        """
        # Convert features to model input format
        X = self._encode_features(features)
        X_scaled = self.scaler.transform(X.reshape(1, -1))
        
        # Get prediction
        prediction = self.model.predict(X_scaled)[0]
        
        # Calculate confidence interval using tree variance
        tree_predictions = np.array([tree.predict(X_scaled)[0] 
                                   for tree in self.model.estimators_])
        confidence_interval = np.std(tree_predictions) * 2  # 95% confidence interval
        
        return {
            'predicted_price': float(prediction),
            'min_price': float(prediction - confidence_interval),
            'max_price': float(prediction + confidence_interval),
            'confidence': 0.95
        }
    
    def _encode_features(self, features):
        """Convert raw features to model input format"""
        if self.model_type == 'flight':
            return self._encode_flight_features(features)
        else:
            return self._encode_hotel_features(features)
    
    def _encode_flight_features(self, features):
        """Encode flight-specific features"""
        encoded = np.zeros(self.feature_dim)
        
        # Encode temporal features
        date = datetime.strptime(features['date'], '%Y-%m-%d')
        encoded[0] = date.month / 12.0  # Month
        encoded[1] = date.weekday() / 7.0  # Day of week
        encoded[2] = 1 if date.weekday() >= 5 else 0  # Weekend flag
        
        # Encode route features (you would expand this with actual city encodings)
        encoded[3] = hash(features['departure_city']) % 100 / 100.0
        encoded[4] = hash(features['arrival_city']) % 100 / 100.0
        
        # Encode class and other features
        encoded[5] = 1 if features.get('class') == 'business' else 0
        encoded[6] = features.get('duration', 0) / 24.0  # Normalize to days
        encoded[7] = features.get('stops', 0) / 3.0  # Normalize to max 3 stops
        
        return encoded
    
    def _encode_hotel_features(self, features):
        """Encode hotel-specific features"""
        encoded = np.zeros(self.feature_dim)
        
        # Encode temporal features
        check_in = datetime.strptime(features['check_in'], '%Y-%m-%d')
        encoded[0] = check_in.month / 12.0  # Month
        encoded[1] = check_in.weekday() / 7.0  # Day of week
        
        # Encode stay duration
        check_out = datetime.strptime(features['check_out'], '%Y-%m-%d')
        duration = (check_out - check_in).days
        encoded[2] = min(duration / 30.0, 1.0)  # Normalize to max 30 days
        
        # Encode location and hotel features
        encoded[3] = hash(features['city']) % 100 / 100.0
        encoded[4] = features.get('star_rating', 3) / 5.0
        encoded[5] = 1 if features.get('breakfast_included') else 0
        encoded[6] = features.get('room_size', 20) / 100.0  # Normalize to 100mÂ²
        
        return encoded
    
    def train(self, X_train, y_train):
        """Train the model with new data"""
        X_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_scaled, y_train)
        
        # Save the trained model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
            pickle.dump(self.scaler, f) 