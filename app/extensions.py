from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import secrets
from amadeus import Client

# Initialize SQLAlchemy without custom parameters
db = SQLAlchemy()

# Clear the metadata to ensure clean initialization
# This helps resolve relationship conflicts
db.metadata.clear()

# Initialize the login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# Initialize CSRF protection with stronger settings
csrf = CSRFProtect()

# Initialize Amadeus client
# The actual credentials will be set in the create_app function
amadeus_client = None 