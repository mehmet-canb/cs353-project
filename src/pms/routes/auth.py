from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user

from pms.authorization import create_user, does_user_exist

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET"], defaults={"error": None})
@bp.route("/login/<error>", methods=["GET"])
def login_page(error: str | None):
    logout_user()
    return render_template("auth/login.html", error=error)


@bp.route("/register", methods=["GET"])
def register_page():
    logout_user()
    return render_template("auth/register.html")


@bp.route("/register", methods=["POST"])
def register():
    if (
        not request.form.get("email")
        or not request.form.get("password")
        or not request.form.get("username")
        or not request.form.get("phone_no")
        or not request.form.get("forename")
        # or not request.form.get("middlename")
        or not request.form.get("surname")
        or not request.form.get("confirm_password")
        or request.form.get("password") != request.form.get("confirm_password")
    ):
        return redirect(
            url_for("auth.register_page", error="Passwords do not match")
            # Other error messages cannot occur as the form is validated by the browser
        )
    if does_user_exist(request.form["email"]):
        return redirect(url_for("auth.register_page", error="User already exists"))
    create_user(
        email=request.form["email"],
        password=request.form["password"],
        username=request.form["username"],
        phone_no=request.form["phone_no"],
        forename=request.form["forename"],
        middlename=request.form["middlename"],
        surname=request.form["surname"],
    )
    return redirect(url_for("auth.login_page"))


@bp.route("/login", methods=["POST"])
@login_required
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    else:
        return redirect(url_for("login.login_page", error="Invalid email or password"))


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
