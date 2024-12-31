from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user

from pms.authorization import coach_required
from pms.db import get_cursor

bp = Blueprint("session", __name__, url_prefix="/session")


@bp.route("/create", methods=["GET"])
@coach_required
def create_page():
    return render_template("session/create.html")


@bp.route("/create", methods=["POST"])
@coach_required
def create_session():
    session_name = request.form["session_name"]
    session_date = request.form["session_date"]
    start_hour = request.form["start_hour"]
    end_hour = request.form["end_hour"]
    price = request.form.get("price", 0)
    session_type = request.form["session_type"]

    if (
        not session_name
        or not session_date
        or not start_hour
        or not end_hour
        or not session_type
    ):
        return redirect(
            url_for("session.create_page", error="Please enter the required fields.")
        )

    try:
        cursor = get_cursor()

        # Insert base session
        cursor.execute(
            """
            INSERT INTO swimming_session (session_name, session_date, start_hour, end_hour, price, coach_email)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (session_name, session_date, start_hour, end_hour, price, current_user.id),
        )

        # Also insert for its sessions type table
        if session_type == "one_to_one_session":
            special_request = request.form.get("special_request", "")
            cursor.execute(
                """
                INSERT INTO one_to_one_session (session_name, session_date, start_hour, end_hour, special_request_comment)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_name, session_date, start_hour, end_hour, special_request),
            )

        elif session_type == "class_session":
            age_group = request.form["age_group"]
            max_capacity = request.form["max_capacity"]
            class_level = request.form["class_level"]
            signup_date = request.form["signup_date"]

            cursor.execute(
                """
                INSERT INTO class_session (session_name, session_date, start_hour, end_hour, age_group,
                                            number_of_participants, max_capacity, class_level, signup_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                    age_group,
                    0,
                    max_capacity,
                    class_level,
                    signup_date,
                ),
            )

        elif session_type == "race":
            age_group = request.form["comp_age_group"]
            stroke_style = request.form["stroke_style"]

            cursor.execute(
                """
                INSERT INTO race (session_name, session_date, start_hour, end_hour, age_group, stroke_style)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                    age_group,
                    stroke_style,
                ),
            )

        elif session_type == "individual_session":
            # Assuming number of months start at 1 if not specified otherwise
            number_of_months = request.form["number_of_months"] or 1
            cursor.execute(
                """
                INSERT INTO individual_session (session_name, session_date, start_hour, end_hour, number_of_months)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_name, session_date, start_hour, end_hour, number_of_months),
            )
        else:
            cursor.connection.rollback()
            return redirect(
                url_for(
                    "session.create_page", error="Please select a valid session type."
                )
            )

        cursor.connection.commit()
        return redirect(url_for("session.create_page"))

    except Exception as e:
        cursor.connection.rollback()
        return redirect(
            url_for("session.create_page", error=f"Session creation failed: {str(e)}")
        )


@bp.route("/", methods=["GET"])
@coach_required
def list_sessions():
    cursor = get_cursor()

    # One-to-One Sessions
    cursor.execute(
        """
        SELECT s.*, o.special_request_comment
        FROM swimming_session s
        JOIN one_to_one_session o ON s.session_name = o.session_name
            AND s.session_date = o.session_date
            AND s.start_hour = o.start_hour
            AND s.end_hour = o.end_hour
        WHERE s.coach_email = %s
        ORDER BY s.session_date DESC, s.start_hour ASC
    """,
        (current_user.id,),
    )
    one_to_one_sessions = cursor.fetchall()

    # Class Sessions
    cursor.execute(
        """
        SELECT s.*, c.*
        FROM swimming_session s
        JOIN class_session c ON s.session_name = c.session_name
            AND s.session_date = c.session_date
            AND s.start_hour = c.start_hour
            AND s.end_hour = c.end_hour
        WHERE s.coach_email = %s
        ORDER BY s.session_date DESC, s.start_hour ASC
    """,
        (current_user.id,),
    )
    class_sessions = cursor.fetchall()

    # Race Sessions
    cursor.execute(
        """
        SELECT s.*, r.*
        FROM swimming_session s
        JOIN race r ON s.session_name = r.session_name
            AND s.session_date = r.session_date
            AND s.start_hour = r.start_hour
            AND s.end_hour = r.end_hour
        WHERE s.coach_email = %s
        ORDER BY s.session_date DESC, s.start_hour ASC
    """,
        (current_user.id,),
    )
    race_sessions = cursor.fetchall()

    # Individual Sessions
    cursor.execute(
        """
        SELECT s.*, i.*
        FROM swimming_session s
        JOIN individual_session i ON s.session_name = i.session_name
            AND s.session_date = i.session_date
            AND s.start_hour = i.start_hour
            AND s.end_hour = i.end_hour
        WHERE s.coach_email = %s
        ORDER BY s.session_date DESC, s.start_hour ASC
    """,
        (current_user.id,),
    )
    individual_sessions = cursor.fetchall()

    return render_template(
        "session/list.html",
        one_to_one=one_to_one_sessions,
        classes=class_sessions,
        races=race_sessions,
        individual=individual_sessions,
    )
