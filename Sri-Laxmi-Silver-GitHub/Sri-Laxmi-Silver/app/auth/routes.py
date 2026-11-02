from flask import render_template, request, redirect, url_for
from urllib.parse import urlsplit

from flask_login import login_user, logout_user

from . import auth_bp
from .forms import validate_email, validate_password
from ..extensions import db
from ..models import User


def _safe_next_url():
    target = request.form.get("next") or request.args.get("next", "")
    parsed = urlsplit(target)
    if (
        target.startswith("/")
        and not target.startswith("//")
        and not parsed.scheme
        and not parsed.netloc
        and "\\" not in target
    ):
        return target
    return url_for("home")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html", next_url=request.args.get("next", ""))

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    name = request.form.get("name", "").strip()

    if not validate_email(email):
        return "Invalid email", 400

    if not validate_password(password):
        return "Password must be at least 8 characters", 400

    existing_user = db.session.scalar(
        db.select(User).where(User.email == email)
    )

    if existing_user:
        return "Email already registered", 409

    user = User(
        email=email,
        name=name or None,
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    login_user(user)

    return redirect(_safe_next_url())


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html", next_url=request.args.get("next", ""))

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = db.session.scalar(
        db.select(User).where(User.email == email)
    )

    if user is None or not user.check_password(password):
        return "Invalid email or password", 401

    if not user.is_active:
        return "Account disabled", 403

    login_user(user)

    return redirect(_safe_next_url())


@auth_bp.route("/logout")
def logout():
    logout_user()

    return redirect(url_for("home"))