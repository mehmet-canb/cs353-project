from functools import wraps
from hashlib import sha256

from flask import current_app, redirect, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user

from pms.db import get_cursor

# Initialize extensions
login_manager = LoginManager()


# Note: id is email for our purposes
class User(UserMixin):
    def __init__(self, id, is_coach=False):
        self.id = id
        self.is_coach = is_coach


@login_manager.user_loader
def user_loader(email) -> User | None:
    cursor = get_cursor()
    cursor.execute("SELECT * FROM pms_user WHERE email = %s", (email,))
    user = cursor.fetchone()
    if user:
        is_coach = is_user_coach(email)
        user = User(id=email, is_coach=is_coach)
        login_user(user)
        return user
    return None


@login_manager.request_loader
def request_loader(request) -> User | None:
    if request.form.get("email") is None or request.form.get("password") is None:
        return None

    password_hash = sha256(request.form.get("password").encode()).hexdigest()
    cursor = get_cursor()
    cursor.execute(
        "SELECT * FROM pms_user WHERE email = %s AND password_hash = %s",
        (request.form["email"], password_hash),
    )
    user = cursor.fetchone()
    if user:
        user = User(
            id=request.form["email"], is_coach=is_user_coach(request.form["email"])
        )
        login_user(user, remember=request.form.get("remember", False))
        return user
    return None


# a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3
def does_user_exist(email: str) -> bool:
    cursor = get_cursor()
    cursor.execute("SELECT * FROM pms_user WHERE email = %s", (email,))
    return cursor.fetchone() is not None


def get_user_by_email(email: str) -> dict | None:
    cursor = get_cursor()
    cursor.execute("SELECT * FROM pms_user WHERE email = %s", (email,))
    return cursor.fetchone()


def is_user_coach(email: str) -> bool:
    cursor = get_cursor()
    cursor.execute("SELECT * FROM coach WHERE email = %s", (email,))
    return cursor.fetchone() is not None


def create_user(
    email: str,
    password: str,
    username: str,
    phone_no: str,
    forename: str,
    middlename: str,
    surname: str,
) -> None:
    password_hash = sha256(password.encode()).hexdigest()
    cursor = get_cursor()
    cursor.execute(
        """
        INSERT INTO pms_user (email, password_hash, username, phone_no, forename, middlename, surname)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,  # noqa: E501
        (email, password_hash, username, phone_no, forename, middlename, surname),
    )
    cursor.connection.commit()


def coach_required(func):
    """
    Use this decorator in place of @login_required to restrict access to logged-in coaches only!

    Usage:
    @bp.route("/dashboard")
    @coach_required
    def dashboard():
        return render_template("dashboard.html")
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not current_user.is_coach:
            return redirect(url_for("main.index"))

        if callable(getattr(current_app, "ensure_sync", None)):
            return current_app.ensure_sync(func)(*args, **kwargs)
        return func(*args, **kwargs)

    return decorated_view
