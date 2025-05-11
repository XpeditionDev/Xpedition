from flask import Blueprint
from functools import wraps
from app.extensions import csrf

def csrf_exempt(view):
    """Mark a view as exempt from CSRF protection using Flask-WTF's native method."""
    return csrf.exempt(view)

def csrf_exempt_blueprint(blueprint):
    """Mark all routes in a blueprint as exempt from CSRF protection."""
    for endpoint, view_func in blueprint.deferred_functions:
        csrf.exempt(view_func)
    return blueprint 