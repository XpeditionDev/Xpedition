from app import create_app, db
from app.models import User, UserSettings, Itinerary, SavedFlight
from datetime import datetime

app = create_app()

with app.app_context():
    print("Starting database creation...")
    
    # Create all tables
    db.create_all()
    print("Tables created!")
    
    # Create a test user
    test_user = User(
        username='testuser',
        email='test@example.com'
    )
    test_user.set_password('test123')
    db.session.add(test_user)
    db.session.commit()
    print("Test user created!")
    
    # Create user settings for test user
    user_settings = UserSettings(
        user_id=test_user.id,
        theme='light',
        notifications_enabled=True
    )
    db.session.add(user_settings)
    db.session.commit()
    print("User settings created!")
    
    # Create a test itinerary
    test_itinerary = Itinerary(
        name='Summer Trip',
        user_id=test_user.id,
        start_date=datetime.strptime('2024-07-01', '%Y-%m-%d'),
        end_date=datetime.strptime('2024-07-14', '%Y-%m-%d')
    )
    db.session.add(test_itinerary)
    db.session.commit()
    print("Test itinerary created!")
    
    print("Database setup completed successfully!") 