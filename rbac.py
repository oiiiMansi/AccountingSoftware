from functools import wraps
from flask import abort, current_app
from flask_login import current_user

# Role definitions mapped to permission levels (higher number = more privileges)
ROLES = {
    'admin': 3,
    'accountant': 2,
    'viewer': 1
}

def role_required(role):
    """
    Decorator to enforce role-based access control on views.
    
    Usage:
    @role_required('accountant')
    def some_view(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if not current_user.is_authenticated:
                # Redirect to login if not authenticated
                return current_app.login_manager.unauthorized()
            
            # Admin has full access regardless of required role
            if current_user.role == 'admin':
                return f(*args, **kwargs)
            
            # Check if current user's role level is sufficient
            if ROLES.get(current_user.role, 0) < ROLES.get(role, 0):
                # Insufficient permission, return 403 Forbidden
                abort(403)
                
            # Role is valid and has sufficient permission
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_permission(required_role):
    """
    Helper function to be used in templates (e.g., to show/hide buttons)
    Returns True if current user has permission for the given role.
    
    Usage in template:
    {% if has_permission('accountant') %}
        <a href="/some-feature">Access</a>
    {% endif %}
    """
    if not current_user.is_authenticated:
        return False
    
    # Admins have all permissions
    if current_user.role == 'admin':
        return True

    # Check if current user's role level is sufficient
    return ROLES.get(current_user.role, 0) >= ROLES.get(required_role, 0)



def admin_required(f):
    """
    Decorator for routes that require admin role.
    """
    return role_required('admin')(f)

def accountant_required(f):
    """
    Decorator for routes that require accountant or higher role.
    """
    return role_required('accountant')(f)

def viewer_required(f):
    """
    Decorator for routes that require viewer or higher role.
    """
    return role_required('viewer')(f)
