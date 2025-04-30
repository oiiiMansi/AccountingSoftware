from functools import wraps
from flask import abort, current_app
from flask_login import current_user

# Role definitions
ROLES = {
    'admin': 3,
    'accountant': 2,
    'viewer': 1
}

def role_required(role):
    """
    Decorator to check if user has required role
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            
            # Admin has access to everything
            if current_user.role == 'admin':
                return f(*args, **kwargs)
            
            # Check if user's role has sufficient permissions
            if ROLES.get(current_user.role, 0) < ROLES.get(role, 0):
                abort(403)  # Forbidden
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_permission(required_role):
    """
    Helper function to check permissions in templates
    """
    if not current_user.is_authenticated:
        return False
    
    if current_user.role == 'admin':
        return True
        
    return ROLES.get(current_user.role, 0) >= ROLES.get(required_role, 0)

# Specific role decorators for convenience
def admin_required(f):
    return role_required('admin')(f)

def accountant_required(f):
    return role_required('accountant')(f)

def viewer_required(f):
    return role_required('viewer')(f) 