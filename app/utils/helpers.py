from functools import wraps

from flask import current_app, flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    """Decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                flash("You do not have permission to access this resource.", "danger")
                return redirect(url_for("auth.unauthorized"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def teacher_required(f):
    return role_required("teacher")(f)

def student_required(f):
    return role_required("student")(f)

def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config.get("ALLOWED_EXTENSIONS", {"pdf", "docx", "txt"})
