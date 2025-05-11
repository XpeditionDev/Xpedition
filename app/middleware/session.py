from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from datetime import datetime, timedelta

def check_session_expired():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated:
                # Update last seen timestamp
                current_user.update_last_seen()
            return f(*args, **kwargs)
        return decorated_function
    return decorator 