from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from pms.db import get_cursor

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html", current_user=current_user)


@bp.route("/profile")
@login_required
def profile():
    cursor = get_cursor()
    cursor.execute("SELECT * FROM pms_user WHERE email = %s", (current_user.id,))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM benefit WHERE swimmer_email = %s", (current_user.id,))
    benefits = cursor.fetchall()
    return render_template("profile.html", user=user, benefits=benefits)


@bp.route("/sessions")
@login_required
def sessions():
    user_email = current_user.id  # Dynamically get the logged-in user's email
    cur = get_cursor()

    # # Retrieve attended sessions with additional details
    # attended_query = """
    #     SELECT ss.session_name, ss.session_date, ss.start_hour, ss.end_hour,
    #            cs.class_level, cs.age_group,
    #            pu.forename AS coach_forename, pu.surname AS coach_surname,
    #            c.rating,
    #            c.email AS coach_email
    #     FROM swimming_session ss
    #     JOIN swimmer_attend_session sas
    #       ON ss.session_name = sas.session_name
    #      AND ss.session_date = sas.session_date
    #      AND ss.start_hour = sas.start_hour
    #      AND ss.end_hour = sas.end_hour
    #     LEFT JOIN class_session cs
    #       ON ss.session_name = cs.session_name
    #      AND ss.session_date = cs.session_date
    #      AND ss.start_hour = cs.start_hour
    #      AND ss.end_hour = cs.end_hour
    #     LEFT JOIN coach c
    #       ON ss.coach_email = c.email
    #     LEFT JOIN pms_user pu
    #       ON c.email = pu.email
    #     WHERE sas.email = %s
    #     ORDER BY ss.session_date DESC, ss.start_hour DESC;
    # """
    # cur.execute(attended_query, (user_email,))
    # attended_sessions = cur.fetchall()

    # Retrieve available sessions with additional details
    # available_query = """
    #     SELECT ss.session_name, ss.session_date, ss.start_hour, ss.end_hour,
    #            cs.class_level, cs.age_group,
    #            pu.forename AS coach_forename, pu.surname AS coach_surname,
    #            c.rating,
    #            c.email AS coach_email
    #     FROM swimming_session ss
    #     LEFT JOIN swimmer_attend_session sas
    #       ON ss.session_name = sas.session_name
    #      AND ss.session_date = sas.session_date
    #      AND ss.start_hour = sas.start_hour
    #      AND ss.end_hour = sas.end_hour
    #      AND sas.email = %s
    #     LEFT JOIN class_session cs
    #       ON ss.session_name = cs.session_name
    #      AND ss.session_date = cs.session_date
    #      AND ss.start_hour = cs.start_hour
    #      AND ss.end_hour = cs.end_hour
    #     LEFT JOIN coach c
    #       ON ss.coach_email = c.email
    #     LEFT JOIN pms_user pu
    #       ON c.email = pu.email
    #     WHERE sas.email IS NULL
    #     ORDER BY ss.session_date ASC, ss.start_hour ASC;
    # """
    # cur.execute(available_query, (user_email,))
    # available_sessions = cur.fetchall()

    try:
        # **1. Past Sessions: Enrolled sessions that have already occurred**
        past_sessions_query = """
            SELECT ss.session_name, ss.session_date, ss.start_hour, ss.end_hour,
                   cs.class_level, CONCAT(cs.min_age, '-', cs.max_age) AS age_group,
                   pu.forename AS coach_forename, pu.surname AS coach_surname,
                   c.rating,
                   c.email AS coach_email
            FROM swimming_session ss
            JOIN swimmer_attend_session sas
              ON ss.session_name = sas.session_name
             AND ss.session_date = sas.session_date
             AND ss.start_hour = sas.start_hour
             AND ss.end_hour = sas.end_hour
            LEFT JOIN class_session cs
              ON ss.session_name = cs.session_name
             AND ss.session_date = cs.session_date
             AND ss.start_hour = cs.start_hour
             AND ss.end_hour = cs.end_hour
            LEFT JOIN coach c
              ON ss.coach_email = c.email
            LEFT JOIN pms_user pu
              ON c.email = pu.email
            WHERE sas.email = %s
              AND (ss.session_date < CURRENT_DATE
                   OR (ss.session_date = CURRENT_DATE AND ss.end_hour < CURRENT_TIME))
            ORDER BY ss.session_date DESC, ss.start_hour DESC;
        """
        cur.execute(past_sessions_query, (user_email,))
        past_sessions = cur.fetchall()

        # **2. Upcoming Sessions: Enrolled sessions that are in the future**
        upcoming_sessions_query = """
            SELECT ss.session_name, ss.session_date, ss.start_hour, ss.end_hour,
                   cs.class_level, CONCAT(cs.min_age, '-', cs.max_age) AS age_group,
                   pu.forename AS coach_forename, pu.surname AS coach_surname,
                   c.rating,
                   c.email AS coach_email
            FROM swimming_session ss
            JOIN swimmer_attend_session sas
              ON ss.session_name = sas.session_name
             AND ss.session_date = sas.session_date
             AND ss.start_hour = sas.start_hour
             AND ss.end_hour = sas.end_hour
            LEFT JOIN class_session cs
              ON ss.session_name = cs.session_name
             AND ss.session_date = cs.session_date
             AND ss.start_hour = cs.start_hour
             AND ss.end_hour = cs.end_hour
            LEFT JOIN coach c
              ON ss.coach_email = c.email
            LEFT JOIN pms_user pu
              ON c.email = pu.email
            WHERE sas.email = %s
              AND (ss.session_date > CURRENT_DATE
                OR (ss.session_date = CURRENT_DATE AND ss.start_hour >= CURRENT_TIME))
            ORDER BY ss.session_date ASC, ss.start_hour ASC;
        """
        cur.execute(upcoming_sessions_query, (user_email,))
        upcoming_sessions = cur.fetchall()

        # **3. Available Sessions: Future sessions not enrolled by the user**
        available_sessions_query = """
            SELECT ss.session_name, ss.session_date, ss.start_hour, ss.end_hour,
                   cs.class_level, CONCAT(cs.min_age, '-', cs.max_age) AS age_group,
                   pu.forename AS coach_forename, pu.surname AS coach_surname,
                   c.rating,
                   c.email AS coach_email
            FROM swimming_session ss
            LEFT JOIN swimmer_attend_session sas
              ON ss.session_name = sas.session_name
             AND ss.session_date = sas.session_date
             AND ss.start_hour = sas.start_hour
             AND ss.end_hour = sas.end_hour
             AND sas.email = %s
            LEFT JOIN class_session cs
              ON ss.session_name = cs.session_name
             AND ss.session_date = cs.session_date
             AND ss.start_hour = cs.start_hour
             AND ss.end_hour = cs.end_hour
            LEFT JOIN coach c
              ON ss.coach_email = c.email
            LEFT JOIN pms_user pu
              ON c.email = pu.email
            WHERE sas.email IS NULL
              AND (ss.session_date > CURRENT_DATE
                OR (ss.session_date = CURRENT_DATE AND ss.start_hour >= CURRENT_TIME))
            ORDER BY ss.session_date ASC, ss.start_hour ASC;
        """
        cur.execute(available_sessions_query, (user_email,))
        available_sessions = cur.fetchall()

    finally:
        cur.close()

    return render_template(
        "sessions.html",
        # attended_sessions=attended_sessions,
        past_sessions=past_sessions,
        upcoming_sessions=upcoming_sessions,
        available_sessions=available_sessions,
    )


def join_session_logic(session_name, session_date, start_hour, end_hour, user_email):
    """
    Handles the logic for a user joining a session.
    """
    cur = get_cursor()

    try:
        # Check if the session exists and retrieve capacity
        check_query = """
            SELECT cs.max_capacity, cs.number_of_participants
            FROM class_session cs
            JOIN swimming_session ss
              ON cs.session_name = ss.session_name
             AND cs.session_date = ss.session_date
             AND cs.start_hour = ss.start_hour
             AND cs.end_hour = ss.end_hour
            WHERE ss.session_name = %s AND ss.session_date = %s
              AND ss.start_hour = %s AND ss.end_hour = %s;
        """
        cur.execute(check_query, (session_name, session_date, start_hour, end_hour))
        class_session_data = cur.fetchone()

        check_query = """
            SELECT *
            FROM swimming_session
            WHERE session_name = %s AND session_date = %s
              AND start_hour = %s AND end_hour = %s;
        """
        cur.execute(check_query, (session_name, session_date, start_hour, end_hour))
        swimming_session_data = cur.fetchone()

        if not swimming_session_data:
            return "Session not found.", 404

        if not class_session_data:
            max_capacity = None
            current_participants = None
        else:
            max_capacity = class_session_data["max_capacity"]
            current_participants = class_session_data["number_of_participants"]

            if current_participants >= max_capacity:
                return "Session is full. You cannot join.", 400

        # Start transaction
        cur.execute("BEGIN;")

        # Insert into swimmer_attend_session
        insert_query = """
            INSERT INTO swimmer_attend_session (email, session_name, session_date,
                                                start_hour, end_hour)
            VALUES (%s, %s, %s, %s, %s);
        """
        cur.execute(
            insert_query, (user_email, session_name, session_date, start_hour, end_hour)
        )

        # Update number_of_participants in class_session
        update_query = """
            UPDATE class_session
            SET number_of_participants = number_of_participants + 1
            WHERE session_name = %s AND session_date = %s
              AND start_hour = %s AND end_hour = %s;
        """
        cur.execute(update_query, (session_name, session_date, start_hour, end_hour))

        # Update number_of_sessions_attended in swimmer table
        update_swimmer_query = """
            UPDATE swimmer
            SET number_of_sessions_attended = number_of_sessions_attended + 1
            WHERE email = %s;
        """
        cur.execute(update_swimmer_query, (user_email,))

        # Commit transaction
        cur.execute("COMMIT;")
        return "Successfully joined the session.", 200
    except Exception as e:
        cur.execute("ROLLBACK;")
        print(f"Error joining session: {e}")  # Log the error
        return "An error occurred while joining the session.", 500


@bp.route("/sessions/join", methods=["POST"])
@login_required
def join_session():
    data = request.json  # Receive JSON payload from the fetch request
    session_name = data.get("session_name")
    session_date = data.get("session_date")
    start_hour = data.get("start_hour")
    end_hour = data.get("end_hour")

    print("Received data:")
    print(data)
    print(f"Session name: {session_name}")

    if not all([session_name, session_date, start_hour, end_hour]):
        return "Invalid session data.", 400

    user_email = current_user.id  # Dynamically get the logged-in user's email
    result, status_code = join_session_logic(
        session_name, session_date, start_hour, end_hour, user_email
    )
    return result, status_code


@bp.route("/sessions/disenroll", methods=["POST"])
@login_required
def disenroll_session():
    data = request.json
    session_name = data.get("session_name")
    session_date = data.get("session_date")
    start_hour = data.get("start_hour")
    end_hour = data.get("end_hour")
    user_email = current_user.id  # Using dynamic email

    if not all([session_name, session_date, start_hour, end_hour]):
        return "Invalid session data.", 400

    cur = get_cursor()

    try:
        # Start transaction
        cur.execute("BEGIN;")

        # Check if the user is enrolled in the session
        check_query = """
            SELECT * FROM swimmer_attend_session
            WHERE email = %s AND session_name = %s AND session_date = %s
              AND start_hour = %s AND end_hour = %s;
        """
        cur.execute(
            check_query, (user_email, session_name, session_date, start_hour, end_hour)
        )
        if not cur.fetchone():
            return "You are not enrolled in this session.", 404

        # Remove from swimmer_attend_session
        delete_query = """
            DELETE FROM swimmer_attend_session
            WHERE email = %s AND session_name = %s AND session_date = %s
              AND start_hour = %s AND end_hour = %s;
        """
        cur.execute(
            delete_query, (user_email, session_name, session_date, start_hour, end_hour)
        )

        # Decrement number_of_participants in class_session
        update_query = """
            UPDATE class_session
            SET number_of_participants = number_of_participants - 1
            WHERE session_name = %s AND session_date = %s
              AND start_hour = %s AND end_hour = %s;
        """
        cur.execute(update_query, (session_name, session_date, start_hour, end_hour))

        # Decrement number_of_sessions_attended in swimmer table
        update_swimmer_query = """
            UPDATE swimmer
            SET number_of_sessions_attended = number_of_sessions_attended - 1
            WHERE email = %s;
        """
        cur.execute(update_swimmer_query, (user_email,))

        # Commit transaction
        cur.execute("COMMIT;")
        return "Successfully disenrolled from the session.", 200
    except Exception as e:
        cur.execute("ROLLBACK;")
        print(f"Error disenrolling from session: {e}")  # Log the error
        return "An error occurred while disenrolling from the session.", 500


@bp.route("/sessions/rate", methods=["POST"])
@login_required
def rate_coach():
    data = request.json
    session_name = data.get("session_name")
    session_date = data.get("session_date")
    start_hour = data.get("start_hour")
    end_hour = data.get("end_hour")
    rating = data.get("rating")
    comment = data.get("comment")
    user_email = current_user.id  # Using dynamic email
    print(comment)
    print(type(comment))
    # Validate input data
    if not all([session_name, session_date, start_hour, end_hour, rating]):
        return "Invalid rating data.", 400

    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return "Rating must be an integer between 1 and 5.", 400

    if len(comment) > 255:
        return "Comment must be smaller than 256 characters", 400

    cur = get_cursor()

    try:
        # Start transaction
        cur.execute("BEGIN;")

        # Retrieve coach_email for the session
        coach_query = """
            SELECT coach_email
            FROM swimming_session
            WHERE session_name = %s AND session_date = %s
              AND start_hour = %s AND end_hour = %s;
        """
        cur.execute(coach_query, (session_name, session_date, start_hour, end_hour))
        coach_data = cur.fetchone()

        if not coach_data:
            cur.execute("ROLLBACK;")
            return "Session not found.", 404

        coach_email = coach_data["coach_email"]

        # Check if the user is enrolled in the session
        check_enrollment_query = """
            SELECT *
            FROM swimmer_attend_session
            WHERE email = %s AND session_name = %s AND session_date = %s
              AND start_hour = %s AND end_hour = %s;
        """
        cur.execute(
            check_enrollment_query,
            (user_email, session_name, session_date, start_hour, end_hour),
        )
        enrollment = cur.fetchone()

        if not enrollment:
            cur.execute("ROLLBACK;")
            return "You are not enrolled in this session.", 403

        # Check if the user has already rated this session
        check_rating_query = """
            SELECT *
            FROM coach_rating
            WHERE swimmer_email = %s AND coach_email = %s
              AND session_name = %s AND session_date = %s
              AND start_hour = %s AND end_hour = %s;
        """
        cur.execute(
            check_rating_query,
            (user_email, coach_email, session_name, session_date, start_hour, end_hour),
        )
        existing_rating = cur.fetchone()

        if existing_rating:
            # Update existing rating
            update_rating_query = """
                UPDATE coach_rating
                SET rating = %s, comment = %s
                WHERE swimmer_email = %s AND coach_email = %s
                  AND session_name = %s AND session_date = %s
                  AND start_hour = %s AND end_hour = %s;
            """
            cur.execute(
                update_rating_query,
                (
                    rating,
                    comment,
                    user_email,
                    coach_email,
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                ),
            )
            message = "Rating updated!"
        else:
            # Insert the new rating
            insert_rating_query = """
                INSERT INTO coach_rating
                (coach_email, swimmer_email, session_name,
                session_date, start_hour, end_hour, rating, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """
            cur.execute(
                insert_rating_query,
                (
                    coach_email,
                    user_email,
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                    rating,
                    comment,
                ),
            )
            message = "Successfully rated the coach."

        # Commit transaction (trigger will handle updating the coach's average rating)
        cur.execute("COMMIT;")
        return message, 200

    except Exception as e:
        cur.execute("ROLLBACK;")
        print(f"Error rating coach: {e}")  # Log the error
        return "An error occurred while rating the coach.", 500


@bp.route("/sessions/get-rate", methods=["POST"])
@login_required
def get_rate_coach():
    data = request.json
    session_name = data.get("session_name")
    session_date = data.get("session_date")
    start_hour = data.get("start_hour")
    end_hour = data.get("end_hour")
    user_email = current_user.id  # Using dynamic email
    query = """
        SELECT rating, comment FROM coach_rating
        WHERE swimmer_email = %s
        AND session_name = %s
        AND session_date = %s
        AND start_hour = %s
        AND end_hour = %s;
    """
    cur = get_cursor()
    cur.execute(
        query,
        (
            user_email,
            session_name,
            session_date,
            start_hour,
            end_hour,
        ),
    )
    result = cur.fetchone()
    if result:
        return result
    return {"rating": "", "comment": ""}
