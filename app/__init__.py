from flask import Flask


from flask_sqlalchemy import SQLAlchemy


from flask_login import LoginManager


from flask_migrate import Migrate


from dotenv import load_dotenv


import os





# Load environment variables from .env file before importing config


basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


load_dotenv(os.path.join(basedir, '.env'))





# Now import config after loading environment variables


from config import Config


from app.extensions import db, login_manager, csrf, amadeus_client


from amadeus import Client


from datetime import datetime





def create_app(config_class=Config):


    app = Flask(__name__)


    app.config.from_object(config_class)





    # Print debug info about Amadeus credentials


    print("\n=== Debug: Amadeus Credentials ===")


    print(f"AMADEUS_CLIENT_ID found: {'Yes' if os.environ.get('AMADEUS_CLIENT_ID') else 'No'}")


    print(f"AMADEUS_CLIENT_SECRET found: {'Yes' if os.environ.get('AMADEUS_CLIENT_SECRET') else 'No'}")


    print(f"Config AMADEUS_CLIENT_ID: {'Yes' if app.config.get('AMADEUS_CLIENT_ID') else 'No'}")


    print(f"Config AMADEUS_CLIENT_SECRET: {'Yes' if app.config.get('AMADEUS_CLIENT_SECRET') else 'No'}")


    print("===============================\n")





    # Initialize Flask extensions


    db.init_app(app)


    login_manager.init_app(app)


    csrf.init_app(app)


    migrate = Migrate(app, db)


    # Initialize Amadeus client
    global amadeus_client
    amadeus_client = Client(
        client_id=app.config.get('AMADEUS_CLIENT_ID'),
        client_secret=app.config.get('AMADEUS_CLIENT_SECRET')
    )
    
    # Add Amadeus client to app context for access in routes
    app.config['AMADEUS_CLIENT'] = amadeus_client


    @app.template_filter('datetime')


    def format_datetime(value):


        if isinstance(value, str):


            try:


                value = datetime.fromisoformat(value.replace('Z', '+00:00'))


            except ValueError:


                return value


        return value.strftime('%Y-%m-%d %H:%M')





    with app.app_context():


        # Import all models to ensure they are registered with SQLAlchemy


        from app.models import User, Itinerary, SavedFlight, Transportation, Booking


        from app.models import Accommodation, Activity, Flight, HotelBooking, FlightBooking, UserSettings, Destination


        


        # Do not create tables here as we're using Flask-Migrate


        # db.create_all()  # <-- This line is removed





    # Register blueprints


    from app.routes.auth import auth_bp


    from app.routes.main import main_bp


    from app.routes.search import search_bp


    


    app.register_blueprint(auth_bp)


    app.register_blueprint(main_bp)


    app.register_blueprint(search_bp, url_prefix='/search')





    @login_manager.user_loader


    def load_user(id):


        return User.query.get(int(id))





    return app


