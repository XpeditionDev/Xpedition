from app.extensions import db
try:
    # Try importing the required modules
    from passlib.hash import pbkdf2_sha256
    from flask_login import UserMixin
    from datetime import datetime
    from werkzeug.security import check_password_hash
except ImportError as e:
    print(f"ImportError in models/user.py: {e}")
    # Define placeholder for UserMixin class if import fails
    class UserMixin:
        pass

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))
    profile_picture = db.Column(db.String(120), default='default.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Explicitly defined relationships without using backref
    settings = db.relationship('UserSettings', foreign_keys='UserSettings.user_id', uselist=False)
    itineraries = db.relationship('Itinerary', foreign_keys='Itinerary.user_id', lazy=True)
    # Don't define saved_flights here to avoid circular backref

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        # Try passlib's pbkdf2_sha256 first
        try:
            return pbkdf2_sha256.verify(password, self.password_hash)
        except (ValueError, AttributeError):
            # If that fails, try the old Werkzeug format
            try:
                return check_password_hash(self.password_hash, password)
            except:
                return False

# UserSettings class removed - now only defined in app/models/user_settings.py
