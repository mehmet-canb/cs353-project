from hashlib import sha256

from flask_login import LoginManager, UserMixin, login_user

from pms.db import get_cursor

# Initialize extensions
login_manager = LoginManager()


class User(UserMixin):
    pass


@login_manager.user_loader
def user_loader(email) -> User | None:
    cursor = get_cursor()
    cursor.execute("SELECT * FROM pms_user WHERE email = %s", (email,))
    user = cursor.fetchone()
    if user:
        user = User()
        user.id = email
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
        user = User()
        user.id = request.form["email"]
        login_user(user, remember=request.form.get("remember", False))
        return user
    return None


def does_user_exist(email: str) -> bool:
    cursor = get_cursor()
    cursor.execute("SELECT * FROM pms_user WHERE email = %s", (email,))
    return cursor.fetchone() is not None


def get_user_by_email(email: str) -> dict | None:
    cursor = get_cursor()
    cursor.execute("SELECT * FROM pms_user WHERE email = %s", (email,))
    return cursor.fetchone()


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
