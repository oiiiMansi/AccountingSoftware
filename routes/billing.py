from flask import redirect, url_for, session, request, render_template
from functools import wraps

# Optional: Reusable login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):  # Adjust based on your session auth
            next_url = request.url
            return redirect(url_for("auth.login", next=next_url))
        return f(*args, **kwargs)
    return decorated_function

# Billing route
@billing.route('/billing')
@login_required
def billing_page():
    bills = get_all_bills()  # however you fetch the data
    return render_template('billing.html', bills=bills)
