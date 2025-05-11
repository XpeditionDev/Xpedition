import os
import json
import random
from datetime import datetime, timedelta
from .recommendation_model import DestinationRecommender
from .itinerary_generator import ItineraryNeuralNetwork
from flask import current_app

class ItineraryGenerator:
    """
    AI-powered itinerary generator that creates personalized travel plans
    based on user preferences, budget, and duration.
    """
    def __init__(self):
        try:
            self.api_key = current_app.config.get('RAPIDAPI_KEY')
            print(f"Using API key from Config: {self.api_key[:5]}...{self.api_key[-4:] if self.api_key else 'None'}")
        except RuntimeError:
            print("Error accessing Flask config: Working outside of application context.")
            self.api_key = os.getenv('RAPIDAPI_KEY')
            
        if not self.api_key:
            print("Invalid or missing API key, falling back to MockHotelClient")
            
        # Initialize recommendation model
        self.recommender = DestinationRecommender()
        self.neural_network = ItineraryNeuralNetwork()
        print("Initialized AI planner with neural networks")
        
    def generate_itinerary(self, preferences):
        """
        Generate a complete travel itinerary based on user preferences
        
        Args:
            preferences: dict containing user preferences
                - destination: str
                - start_date: str (YYYY-MM-DD)
                - end_date: str (YYYY-MM-DD)
                - budget: float
                - interests: list of str
        
        Returns:
            dict: Complete itinerary with daily activities
        """
        # Extract key information
        destination = preferences.get('destination', 'Paris')
        start_date = preferences.get('start_date')
        end_date = preferences.get('end_date')
        budget = preferences.get('budget', 1000)
        interests = preferences.get('interests', [])
        
        # Calculate duration
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end - start).days + 1
        except (ValueError, TypeError):
            duration_days = preferences.get('duration', 3)
        
        # Convert interests to text
        interests_text = ', '.join(interests) if interests else 'sightseeing, culture'
        
        # Use the neural network to generate the itinerary
        try:
            itinerary = self.neural_network.generate_itinerary(preferences)
        except Exception as e:
            print(f"Neural network error: {e}")
            # Fallback to template-based generation
            itinerary = self._generate_template_itinerary(destination, duration_days, budget, interests)
        
        # Add metadata
        itinerary['is_ai_generated'] = True
        
        return itinerary
    
    def _generate_template_itinerary(self, destination, duration_days, budget, interests):
        """Generate a template-based itinerary as fallback"""
        # Simple template-based generation
        itinerary = {
            'destination': destination,
            'duration': duration_days,
            'budget': budget,
            'days': []
        }
        
        # Generate activities for each day
        activities = [
            'Visit local museum', 'Try local cuisine', 'Walking tour',
            'Shopping', 'Visit landmark', 'Relax at park', 'Cultural experience'
        ]
        
        for day in range(1, duration_days + 1):
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
    
    def get_destination_recommendations(self, preferences):
        """Get destination recommendations based on user preferences"""
        return self.recommender.get_destination_recommendations(preferences) 