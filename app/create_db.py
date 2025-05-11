from app import create_app, db
from app.models import User, UserSettings, Itinerary, SavedFlight

print("Starting database creation...")

app = create_app()
with app.app_context():
    db.create_all()
    print("Tables created!")

    # Only create test user if it doesn't exist
    if not User.query.filter_by(username='testuser').first():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        print("Test user created!")
    else:
        print("Test user already exists!") 