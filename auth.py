"""
auth.py
───────
Flask Blueprint containing all authentication routes:
  GET/POST  /register
  GET/POST  /login
  GET       /logout
  GET/POST  /forgot-password
  GET/POST  /profile        (login required)
  GET       /dashboard      (login required)
"""

import sqlite3
from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from models import (
    create_user,
    email_exists,
    get_reports_by_user,
    get_user_by_email,
    get_user_by_id,
    update_user_name,
    update_user_password,
)

auth = Blueprint("auth", __name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

def login_required(f):
    """Decorator: redirect to login if the user is not in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated


def current_user():
    """Return the logged-in user row, or None."""
    uid = session.get("user_id")
    if uid is None:
        return None
    return get_user_by_id(uid)


# ── Register ─────────────────────────────────────────────────────────────────

@auth.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        full_name        = request.form.get("full_name", "").strip()
        email            = request.form.get("email", "").strip().lower()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = {}

        if not full_name:
            errors["full_name"] = "Full name is required."
        if not email or "@" not in email:
            errors["email"] = "A valid email is required."
        if len(password) < 8:
            errors["password"] = "Password must be at least 8 characters."
        if password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if not errors and email_exists(email):
            errors["email"] = "An account with this email already exists."

        if errors:
            return render_template(
                "register.html",
                errors=errors,
                form_data=request.form,
            )

        password_hash = generate_password_hash(password)
        try:
            user_id = create_user(full_name, email, password_hash)
        except sqlite3.IntegrityError:
            errors["email"] = "An account with this email already exists."
            return render_template(
                "register.html",
                errors=errors,
                form_data=request.form,
            )

        session["user_id"]   = user_id
        session["user_name"] = full_name
        flash("Account created! Welcome to VenturePilot AI.", "success")
        return redirect(url_for("auth.dashboard"))

    return render_template("register.html", errors={}, form_data={})


# ── Login ────────────────────────────────────────────────────────────────────

@auth.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_url = request.form.get("next", "")

        user = get_user_by_email(email)

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template(
                "login.html",
                error="Invalid email or password.",
                email=email,
                next=next_url,
            )

        session["user_id"]   = user["id"]
        session["user_name"] = user["full_name"]
        flash(f"Welcome back, {user['full_name']}!", "success")

        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("auth.dashboard"))

    return render_template(
        "login.html",
        error=None,
        email="",
        next=request.args.get("next", ""),
    )


# ── Logout ───────────────────────────────────────────────────────────────────

@auth.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ── Forgot Password ──────────────────────────────────────────────────────────

@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Simple self-service password reset: the user provides their email and
    a new password.  No email-token flow is used (no mail server required).
    """
    if request.method == "POST":
        email            = request.form.get("email", "").strip().lower()
        new_password     = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = {}

        if not email or "@" not in email:
            errors["email"] = "A valid email is required."
        if len(new_password) < 8:
            errors["new_password"] = "Password must be at least 8 characters."
        if new_password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if not errors:
            user = get_user_by_email(email)
            if user is None:
                errors["email"] = "No account found with that email."

        if errors:
            return render_template(
                "forgot_password.html",
                errors=errors,
                email=email,
            )

        update_user_password(user["id"], generate_password_hash(new_password))
        flash("Password updated. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html", errors={}, email="")


# ── Dashboard ────────────────────────────────────────────────────────────────

@auth.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    return render_template("dashboard.html", user=user)


# ── Profile ──────────────────────────────────────────────────────────────────

@auth.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()

    if request.method == "POST":
        action = request.form.get("action")
        errors = {}

        if action == "update_name":
            full_name = request.form.get("full_name", "").strip()
            if not full_name:
                errors["full_name"] = "Name cannot be empty."
            else:
                update_user_name(user["id"], full_name)
                session["user_name"] = full_name
                flash("Name updated successfully.", "success")
                return redirect(url_for("auth.profile"))

        elif action == "update_password":
            current_pw  = request.form.get("current_password", "")
            new_pw      = request.form.get("new_password", "")
            confirm_pw  = request.form.get("confirm_password", "")

            if not check_password_hash(user["password_hash"], current_pw):
                errors["current_password"] = "Current password is incorrect."
            elif len(new_pw) < 8:
                errors["new_password"] = "New password must be at least 8 characters."
            elif new_pw != confirm_pw:
                errors["confirm_password"] = "Passwords do not match."
            else:
                update_user_password(user["id"], generate_password_hash(new_pw))
                flash("Password changed successfully.", "success")
                return redirect(url_for("auth.profile"))

        user = current_user()
        report_count = len(get_reports_by_user(user["id"]))
        return render_template("profile.html", user=user, errors=errors,
                               report_count=report_count)

    report_count = len(get_reports_by_user(user["id"]))
    return render_template("profile.html", user=user, errors={},
                           report_count=report_count)
