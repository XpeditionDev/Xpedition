import os
import secrets
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Use a stronger secret key and ensure it's set
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Explicitly enable CSRF protection
    WTF_CSRF_ENABLED = True
    
    # Set a separate token for CSRF if needed
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or secrets.token_hex(32)
    
    # Set CSRF token to not expire during the session (for debugging)
    WTF_CSRF_TIME_LIMIT = None
    
    # Get database credentials from environment variables
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME')
    
    # Build the database URI
    if DB_USER and DB_PASSWORD and DB_NAME:
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(basedir, 'app.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AMADEUS_CLIENT_ID = os.environ.get('AMADEUS_CLIENT_ID')
    AMADEUS_CLIENT_SECRET = os.environ.get('AMADEUS_CLIENT_SECRET')
    
    # Hard-coded RapidAPI key for hotel searches
    # This is a temporary solution to avoid environment variable issues
    RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY') or '3ef65386aamsh420e793f0b72475p1ac5dajsne8a6ce37783b'