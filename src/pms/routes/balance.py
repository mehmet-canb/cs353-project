import json

from flask import Blueprint, Response, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from pms.authorization import get_user_by_email
from pms.db import get_cursor
from pms.routes.main import join_session_logic

bp = Blueprint("balance", __name__)


def get_transactions_by_user_id(user_id: str) -> list[dict]:
    cursor = get_cursor()
    cursor.execute(
        """
        SELECT *
        FROM pms_transaction
        WHERE user_id = %s
        """,
        (user_id,),
    )
    transactions = cursor.fetchall()
    return transactions


@bp.route("/balance", methods=["GET"])
@bp.route("/balance/<error>", methods=["GET"])
@login_required
def balance(error: str | None = None, swimming_session: dict | None = None):
    user_info = get_user_by_email(current_user.id)

    transactions = get_transactions_by_user_id(current_user.id)

    return render_template(
        "balance.html",
        balance=user_info["balance"] if user_info else 0,
        error=error,
        swimming_session=swimming_session,
        transactions=transactions,
    )


@bp.route(
    "/balance/cart",
    methods=["POST"],
)
@login_required
def cart():
    req = json.loads(request.data) if request.data else request.form
    session_name = req.get("session_name", "")
    session_date = req.get("session_date", "")
    session_start_hour = req.get("start_hour", "")
    session_end_hour = req.get("end_hour", "")

    user_info = get_user_by_email(current_user.id)

    cursor = get_cursor()
    cursor.execute(
        """
        SELECT *
        FROM swimming_session
        WHERE session_name = %s
            AND session_date = %s
            AND start_hour = %s
            AND end_hour = %s
        """,
        (session_name, session_date, session_start_hour, session_end_hour),
    )
    swimming_session = cursor.fetchone()

    transactions = get_transactions_by_user_id(current_user.id)

    return render_template(
        "balance.html",
        balance=user_info["balance"],
        swimming_session=swimming_session,
        transactions=transactions,
    )


@bp.route("/balance/buy", methods=["POST"])
@login_required
def buy():
    req = request.form
    session_name = req.get("session_name", "")
    session_date = req.get("session_date", "")
    session_start_hour = req.get("start_hour", "")
    session_end_hour = req.get("end_hour", "")

    cursor = get_cursor()
    cursor.execute(
        """
        INSERT INTO pms_transaction (
            user_id,
            session_name,
            session_date,
            start_hour,
            end_hour
        ) VALUES (%s, %s, %s, %s, %s)
        """,
        (
            current_user.id,
            session_name,
            session_date,
            session_start_hour,
            session_end_hour,
        ),
    )
    cursor.connection.commit()

    ret = join_session_logic(
        session_name,
        session_date,
        session_start_hour,
        session_end_hour,
        current_user.id,
    )

    if len(ret) > 1:
        print(ret[0])
        return redirect(url_for("balance.balance", error=ret[0]))
    else:
        return Response(status=200)


@bp.route("/balance/add", methods=["POST"])
@login_required
def add_balance():
    amount = 0
    try:
        if not request.form.get("amount"):
            raise ValueError("Amount is required")
        amount = float(request.form["amount"])
    except ValueError:
        return redirect(url_for("balance.balance", error="Added amount is not valid"))

    user_info = get_user_by_email(current_user.id)

    cursor = get_cursor()
    cursor.execute(
        "UPDATE pms_user SET balance = %s + %s WHERE email = %s",
        (amount, user_info["balance"], current_user.id),
    )
    cursor.connection.commit()  # Do not forget to commit updates

    return redirect(url_for("balance.balance"))
