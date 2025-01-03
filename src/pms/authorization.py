from functools import wraps
from hashlib import sha256

from flask import current_app, redirect, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user

from pms.db import get_cursor

# Initialize extensions
login_manager = LoginManager()


# Note: id is email for our purposes
class User(UserMixin):
    def __init__(self, id, is_coach=False, is_admin=False, is_lifeguard=False):
        self.id = id
        self.is_coach = is_coach
        self.is_admin = is_admin
        self.is_lifeguard = is_lifeguard


@login_manager.user_loader
def user_loader(email) -> User | None:
    cursor = get_cursor()
    cursor.execute("SELECT * FROM pms_user WHERE email = %s", (email,))
    user = cursor.fetchone()
    if user:
        is_coach = is_user_coach(email)
        is_admin = is_user_admin(email)
        is_lifeguard = is_user_lifeguard(email)
        user = User(id=email, is_coach=is_coach, is_admin=is_admin, is_lifeguard=is_lifeguard)
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
            id=request.form["email"],
            is_coach=is_user_coach(request.form["email"]),
            is_admin=is_user_admin(request.form["email"]),
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



def is_user_admin(email: str) -> bool:
    cursor = get_cursor()
    cursor.execute("SELECT * FROM pms_admin WHERE email = %s", (email,))
    return cursor.fetchone() is not None


def is_user_lifeguard(email: str) -> bool:
    cursor = get_cursor()
    cursor.execute("SELECT * FROM lifeguard WHERE email = %s", (email,))
    return cursor.fetchone() is not None


def create_swimmer(
    email: str,
    password: str,
    username: str,
    phone_no: str,
    forename: str,
    middlename: str,
    surname: str,
    date_of_birth: str,
    team_name: str,
) -> None:
    create_user(
        email,
        password,
        username,
        phone_no,
        forename,
        middlename,
        surname,
        date_of_birth,
    )
    cursor = get_cursor()
    cursor.execute(
        """
        INSERT INTO swimmer (email, member_of_team)
        VALUES (%s, %s)
    """,
        (email, team_name),
    )
    cursor.execute(
        """
        INSERT INTO team
        VALUES (%s)
        ON CONFLICT DO NOTHING
        """,
        (team_name,),
    )
    cursor.connection.commit()



def create_user(
    email: str,
    password: str,
    username: str,
    phone_no: str,
    forename: str,
    middlename: str,
    surname: str,
    date_of_birth: str,
) -> None:
    password_hash = sha256(password.encode()).hexdigest()
    cursor = get_cursor()
    cursor.execute(
        """
        INSERT INTO pms_user (email, password_hash, username, phone_no, forename, middlename, surname, birth_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,  # noqa: E501
        (
            email,
            password_hash,
            username,
            phone_no,
            forename,
            middlename,
            surname,
            date_of_birth,
        ),
    )
    cursor.connection.commit()


def coach_required(func):
    """
    Usage:
    @bp.route("/dashboard")
    @coach_required
    def dashboard():
        return render_template("dashboard.html")
    """  # noqa: E501

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


def admin_required(func):
    """
    Restrict access to admin users only.
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not current_user.is_admin:
            return redirect(url_for("main.index"))

        if callable(getattr(current_app, "ensure_sync", None)):
            return current_app.ensure_sync(func)(*args, **kwargs)
        return func(*args, **kwargs)

    return decorated_view
