from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user

from pms.authorization import coach_required
from pms.db import get_cursor

bp = Blueprint("session", __name__, url_prefix="/session")


@bp.route("/create", methods=["GET"])
@coach_required
def create_page():
    return render_template("session/coach/create.html")


@bp.route("/create", methods=["POST"])
@coach_required
def store_session_details():
    session_name = request.form["session_name"]
    session_date = request.form["session_date"]
    start_hour = request.form["start_hour"]
    end_hour = request.form["end_hour"]
    price = request.form.get("price", 0) or 0
    details = request.form.get("details", "")
    session_type = request.form["session_type"]

    # Specialized data
    # For One-to-One:
    special_request = request.form.get("special_request", "")

    # For Class:
    min_age = request.form.get("min_age", "")
    max_age = request.form.get("max_age", "")
    max_capacity = request.form.get("max_capacity", "")
    class_level = request.form.get("class_level", "")
    signup_date = request.form.get("signup_date", "")

    # For Race:
    min_age = request.form.get("min_age", "")
    max_age = request.form.get("max_age", "")
    stroke_style = request.form.get("stroke_style", "")

    # For Individual:
    number_of_months = request.form.get("number_of_months", 1)

    if not (session_name and session_date and start_hour and end_hour and session_type):
        return redirect(
            url_for("session.create_page", error="Please enter the required fields.")
        )

    return redirect(
        url_for(
            "session.select_lanes_page",
            session_name=session_name,
            session_date=session_date,
            start_hour=start_hour,
            end_hour=end_hour,
            price=price,
            details=details,
            session_type=session_type,
            special_request=special_request,
            max_capacity=max_capacity,
            class_level=class_level,
            signup_date=signup_date,
            min_age=min_age,
            max_age=max_age,
            stroke_style=stroke_style,
            number_of_months=number_of_months,
        )
    )


@bp.route("/create/select-lanes", methods=["GET"])
@coach_required
def select_lanes_page():
    session_name = request.args.get("session_name")
    session_date = request.args.get("session_date")
    start_hour = request.args.get("start_hour")
    end_hour = request.args.get("end_hour")
    price = request.args.get("price", 0)
    details = request.args.get("details", "")
    session_type = request.args.get("session_type")

    # Additional fields:
    special_request = request.args.get("special_request", "")
    min_age = request.args.get("min_age", "")
    max_age = request.args.get("max_age", "")
    max_capacity = request.args.get("max_capacity", "")
    class_level = request.args.get("class_level", "")
    signup_date = request.args.get("signup_date", "")
    min_age = request.args.get("min_age", "")
    max_age = request.args.get("max_age", "")
    stroke_style = request.args.get("stroke_style", "")
    number_of_months = request.args.get("number_of_months", 1)

    if not (session_name and session_date and start_hour and end_hour and session_type):
        return redirect(
            url_for("session.create_page", error="Invalid session data. Please retry.")
        )

    cursor = get_cursor()

    # 1) Retrieve all pools & lanes that are
    #    NOT booked during [session_date, start_hour, end_hour].
    cursor.execute(
        """
        SELECT lane.pool_id, lane.lane_id
        FROM lane
        WHERE NOT EXISTS (
            SELECT 1
            FROM booking b
            JOIN swimming_session s ON b.session_name = s.session_name
                AND b.session_date = s.session_date
                AND b.start_hour = s.start_hour
                AND b.end_hour = s.end_hour
            WHERE lane.pool_id = b.pool_id
            AND lane.lane_id = b.lane_id
            AND s.session_date = %s
            AND (
                (s.start_hour, s.end_hour) OVERLAPS (%s::time, %s::time)
            )
        )
        ORDER BY lane.pool_id, lane.lane_id
        """,
        (session_date, start_hour, end_hour),
    )
    available_lanes = cursor.fetchall()

    # Grouping langes by pool for UI
    pool_lane_map = {}
    for lane_row in available_lanes:
        pool_id = lane_row["pool_id"]
        lane_id = lane_row["lane_id"]
        pool_lane_map.setdefault(pool_id, []).append(lane_id)

    return render_template(
        "session/coach/select_lanes.html",
        session_name=session_name,
        session_date=session_date,
        start_hour=start_hour,
        end_hour=end_hour,
        price=price,
        details=details,
        session_type=session_type,
        special_request=special_request,
        max_capacity=max_capacity,
        class_level=class_level,
        signup_date=signup_date,
        min_age=min_age,
        max_age=max_age,
        stroke_style=stroke_style,
        pool_lane_map=pool_lane_map,
        number_of_months=number_of_months,
    )


@bp.route("/create/final", methods=["POST"])
@coach_required
def create_session_final():
    session_name = request.form["session_name"]
    session_date = request.form["session_date"]
    start_hour = request.form["start_hour"]
    end_hour = request.form["end_hour"]
    price = request.form.get("price", 0)
    details = request.form.get("details", "")
    session_type = request.form["session_type"]

    chosen_pool_id = request.form.get("pool_id")
    chosen_lanes = request.form.getlist("lane_id")

    # Additional fields
    special_request = request.form.get("special_request", "")
    min_age = request.form.get("min_age", "")
    max_age = request.form.get("max_age", "")
    max_capacity = request.form.get("max_capacity", "")
    class_level = request.form.get("class_level", "")
    signup_date = request.form.get("signup_date", "")
    min_age = request.form.get("min_age", None)
    max_age = request.form.get("max_age", None)
    stroke_style = request.form.get("stroke_style", "")
    number_of_months = request.form.get("number_of_months", 1)

    if not chosen_pool_id or not chosen_lanes:
        return redirect(
            url_for(
                "session.select_lanes_page",
                session_name=session_name,
                session_date=session_date,
                start_hour=start_hour,
                end_hour=end_hour,
                price=price,
                details=details,
                session_type=session_type,
                error="No pool or lanes selected. Please choose a pool and lanes.",
            )
        )

    try:
        cursor = get_cursor()

        # 1) Insert the base session
        cursor.execute(
            """
            INSERT INTO swimming_session (session_name, session_date, start_hour,
                                            end_hour, price, coach_email, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session_name,
                session_date,
                start_hour,
                end_hour,
                price,
                current_user.id,
                details,
            ),
        )

        # 2) Insert the specialized record
        if session_type == "one_to_one_session":
            cursor.execute(
                """
                INSERT INTO one_to_one_session
                (session_name, session_date, start_hour,
                end_hour, special_request_comment)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_name, session_date, start_hour, end_hour, special_request),
            )
        elif session_type == "class_session":
            cursor.execute(
                """
                INSERT INTO class_session (session_name, session_date, start_hour,
                                            end_hour, min_age, max_age,
                                            number_of_participants, max_capacity,
                                            class_level, signup_date)
                VALUES (%s, %s, %s, %s, %s, %s, 0, %s, %s, %s)
                """,
                (
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                    min_age,
                    max_age,
                    max_capacity,
                    class_level,
                    signup_date,
                ),
            )
        elif session_type == "race":
            # If you need min_age and max_age (like the original code suggests)
            cursor.execute(
                """
                INSERT INTO race (session_name, session_date, start_hour, end_hour,
                                    min_age, max_age, stroke_style)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                    min_age,
                    max_age,
                    stroke_style,
                ),
            )
        elif session_type == "individual_session":
            cursor.execute(
                """
                INSERT INTO individual_session
                (session_name, session_date, start_hour, end_hour, number_of_months)
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

        # 3) Insert the bookings for the chosen pool & lanes
        for lane_id in chosen_lanes:
            cursor.execute(
                """
                INSERT INTO booking
                (pool_id, lane_id, session_name, session_date, start_hour, end_hour)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    chosen_pool_id,
                    lane_id,
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                ),
            )

        cursor.connection.commit()
        return redirect(url_for("session.list_sessions"))

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
        SELECT s.session_name, s.session_date, s.start_hour, s.end_hour,
               s.price, s.coach_email, s.details, o.special_request_comment,
               string_agg(DISTINCT b.pool_id, ', ') as pool_id,
               string_agg(b.lane_id, ', ' ORDER BY b.lane_id) as pool_lanes
        FROM swimming_session s
        JOIN one_to_one_session o ON s.session_name = o.session_name
            AND s.session_date = o.session_date
            AND s.start_hour = o.start_hour
            AND s.end_hour = o.end_hour
        LEFT JOIN booking b ON s.session_name = b.session_name
            AND s.session_date = b.session_date
            AND s.start_hour = b.start_hour
            AND s.end_hour = b.end_hour
        WHERE s.coach_email = %s
        GROUP BY s.session_name, s.session_date, s.start_hour, s.end_hour,
                 s.price, s.coach_email, o.special_request_comment
        ORDER BY s.session_date DESC, s.start_hour ASC
        """,
        (current_user.id,),
    )
    one_to_one_sessions = cursor.fetchall()

    # Class Sessions
    cursor.execute(
        """
        SELECT s.session_name, s.session_date, s.start_hour, s.end_hour,
               s.price, s.coach_email, s.details, c.min_age, c.max_age,
               c.number_of_participants, c.max_capacity, c.class_level, c.signup_date,
               string_agg(DISTINCT b.pool_id, ', ') as pool_id,
               string_agg(b.lane_id, ', ' ORDER BY b.lane_id) as pool_lanes
        FROM swimming_session s
        JOIN class_session c ON s.session_name = c.session_name
            AND s.session_date = c.session_date
            AND s.start_hour = c.start_hour
            AND s.end_hour = c.end_hour
        LEFT JOIN booking b ON s.session_name = b.session_name
            AND s.session_date = b.session_date
            AND s.start_hour = b.start_hour
            AND s.end_hour = b.end_hour
        WHERE s.coach_email = %s
        GROUP BY s.session_name, s.session_date, s.start_hour, s.end_hour,
                 s.price, s.coach_email, c.min_age, c.max_age, c.number_of_participants,
                 c.max_capacity, c.class_level, c.signup_date
        ORDER BY s.session_date DESC, s.start_hour ASC
        """,
        (current_user.id,),
    )
    class_sessions = cursor.fetchall()

    # Race Sessions
    cursor.execute(
        """
        SELECT s.session_name, s.session_date, s.start_hour, s.end_hour,
               s.price, s.coach_email, s.details, r.min_age, r.max_age, r.stroke_style,
               string_agg(DISTINCT b.pool_id, ', ') as pool_id,
               string_agg(b.lane_id, ', ' ORDER BY b.lane_id) as pool_lanes
        FROM swimming_session s
        JOIN race r ON s.session_name = r.session_name
            AND s.session_date = r.session_date
            AND s.start_hour = r.start_hour
            AND s.end_hour = r.end_hour
        LEFT JOIN booking b ON s.session_name = b.session_name
            AND s.session_date = b.session_date
            AND s.start_hour = b.start_hour
            AND s.end_hour = b.end_hour
        WHERE s.coach_email = %s
        GROUP BY s.session_name, s.session_date, s.start_hour, s.end_hour,
                 s.price, s.coach_email, r.min_age, r.max_age, r.stroke_style
        ORDER BY s.session_date DESC, s.start_hour ASC
        """,
        (current_user.id,),
    )
    race_sessions = cursor.fetchall()

    # Individual Sessions
    cursor.execute(
        """
        SELECT s.session_name, s.session_date, s.start_hour, s.end_hour,
               s.price, s.coach_email, s.details, i.number_of_months,
               string_agg(DISTINCT b.pool_id, ', ') as pool_id,
               string_agg(b.lane_id, ', ' ORDER BY b.lane_id) as pool_lanes
        FROM swimming_session s
        JOIN individual_session i ON s.session_name = i.session_name
            AND s.session_date = i.session_date
            AND s.start_hour = i.start_hour
            AND s.end_hour = i.end_hour
        LEFT JOIN booking b ON s.session_name = b.session_name
            AND s.session_date = b.session_date
            AND s.start_hour = b.start_hour
            AND s.end_hour = b.end_hour
        WHERE s.coach_email = %s
        GROUP BY s.session_name, s.session_date, s.start_hour, s.end_hour,
                 s.price, s.coach_email, i.number_of_months
        ORDER BY s.session_date DESC, s.start_hour ASC
        """,
        (current_user.id,),
    )
    individual_sessions = cursor.fetchall()

    return render_template(
        "session/coach/list.html",
        one_to_one=one_to_one_sessions,
        classes=class_sessions,
        races=race_sessions,
        individual=individual_sessions,
    )


@bp.route(
    "/update/<session_name>/<session_date>/<start_hour>/<end_hour>", methods=["GET"]
)
@coach_required
def update_page(session_name, session_date, start_hour, end_hour):
    cursor = get_cursor()

    # Get base session data
    cursor.execute(
        """
        SELECT * FROM swimming_session
        WHERE session_name = %s AND session_date = %s
        AND start_hour = %s AND end_hour = %s
        AND coach_email = %s
        """,
        (session_name, session_date, start_hour, end_hour, current_user.id),
    )
    session = cursor.fetchone()

    if not session:
        return redirect(url_for("session.list_sessions"))

    # Determine session type and get specific data
    session_types = [
        "one_to_one_session",
        "class_session",
        "race",
        "individual_session",
    ]
    session_type = None

    for type_name in session_types:
        cursor.execute(
            f"""
            SELECT * FROM {type_name}
            WHERE session_name = %s AND session_date = %s
            AND start_hour = %s AND end_hour = %s
            """,
            (session_name, session_date, start_hour, end_hour),
        )
        specific_data = cursor.fetchone()
        if specific_data:
            session_type = type_name
            # Merge the two dictionaries:
            session = {**session, **specific_data}
            break

    return render_template(
        "session/coach/update.html", session=session, session_type=session_type
    )


@bp.route(
    "/update/<session_name>/<session_date>/<start_hour>/<end_hour>", methods=["POST"]
)
@coach_required
def update_session(session_name, session_date, start_hour, end_hour):
    try:
        cursor = get_cursor()

        new_name = request.form["session_name"]
        new_date = request.form["session_date"]
        new_start = request.form["start_hour"]
        new_end = request.form["end_hour"]
        new_price = request.form.get("price", 0) or 0
        new_details = request.form.get("details", "")
        session_type = request.form["session_type"]

        if session_type == "one_to_one_session":
            special_request = request.form.get("special_request", "")
            cursor.execute(
                """
                WITH swimming_update AS (
                    UPDATE swimming_session
                    SET session_name = %s,
                        session_date = %s,
                        start_hour = %s,
                        end_hour = %s,
                        price = %s,
                        details = %s
                    WHERE session_name = %s
                    AND session_date = %s
                    AND start_hour = %s
                    AND end_hour = %s
                    RETURNING session_name, session_date, start_hour, end_hour
                )
                UPDATE one_to_one_session o
                SET session_name = s.session_name,
                    session_date = s.session_date,
                    start_hour = s.start_hour,
                    end_hour = s.end_hour,
                    special_request_comment = %s
                FROM swimming_update s
                WHERE o.session_name = %s AND o.session_date = %s
                AND o.start_hour = %s AND o.end_hour = %s
                """,
                (
                    new_name,
                    new_date,
                    new_start,
                    new_end,
                    new_price,
                    new_details,
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                    special_request,
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                ),
            )
        elif session_type == "class_session":
            cursor.execute(
                """
                WITH swimming_update AS (
                    UPDATE swimming_session
                    SET session_name = %s,
                        session_date = %s,
                        start_hour = %s,
                        end_hour = %s,
                        price = %s,
                        details = %s
                    WHERE session_name = %s
                    AND session_date = %s
                    AND start_hour = %s
                    AND end_hour = %s
                    RETURNING session_name, session_date, start_hour, end_hour
                )
                UPDATE class_session c
                SET session_name = s.session_name,
                    session_date = s.session_date,
                    start_hour = s.start_hour,
                    end_hour = s.end_hour,
                    min_age = %s,
                    max_age = %s,
                    max_capacity = %s,
                    class_level = %s,
                    signup_date = %s
                FROM swimming_update s
                WHERE c.session_name = %s
                AND c.session_date = %s
                AND c.start_hour = %s
                AND c.end_hour = %s
                """,
                (
                    new_name,
                    new_date,
                    new_start,
                    new_end,
                    new_price,
                    new_details,
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                    request.form["min_age"],
                    request.form["max_age"],
                    request.form["max_capacity"],
                    request.form["class_level"],
                    request.form["signup_date"],
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                ),
            )
        elif session_type == "race":
            cursor.execute(
                """
                WITH swimming_update AS (
                    UPDATE swimming_session
                    SET session_name = %s,
                        session_date = %s,
                        start_hour = %s,
                        end_hour = %s,
                        price = %s,
                        details = %s
                    WHERE session_name = %s
                    AND session_date = %s
                    AND start_hour = %s
                    AND end_hour = %s
                    RETURNING session_name, session_date, start_hour, end_hour
                )
                UPDATE race r
                SET session_name = s.session_name,
                    session_date = s.session_date,
                    start_hour = s.start_hour,
                    end_hour = s.end_hour,
                    min_age = %s,
                    max_age = %s,
                    stroke_style = %s
                FROM swimming_update s
                WHERE r.session_name = %s
                AND r.session_date = %s
                AND r.start_hour = %s
                AND r.end_hour = %s
                """,
                (
                    new_name,
                    new_date,
                    new_start,
                    new_end,
                    new_price,
                    new_details,
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                    request.form["min_age"],
                    request.form["max_age"],
                    request.form["stroke_style"],
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                ),
            )
        elif session_type == "individual_session":
            cursor.execute(
                """
                WITH swimming_update AS (
                    UPDATE swimming_session
                    SET session_name = %s,
                        session_date = %s,
                        start_hour = %s,
                        end_hour = %s,
                        price = %s,
                        details = %s
                    WHERE session_name = %s
                    AND session_date = %s
                    AND start_hour = %s
                    AND end_hour = %s
                    RETURNING session_name, session_date, start_hour, end_hour
                )
                UPDATE individual_session i
                SET session_name = s.session_name,
                    session_date = s.session_date,
                    start_hour = s.start_hour,
                    end_hour = s.end_hour,
                    number_of_months = %s
                FROM swimming_update s
                WHERE i.session_name = %s
                AND i.session_date = %s
                AND i.start_hour = %s
                AND i.end_hour = %s
                """,
                (
                    new_name,
                    new_date,
                    new_start,
                    new_end,
                    new_price,
                    new_details,
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                    request.form.get("number_of_months", 1),
                    session_name,
                    session_date,
                    start_hour,
                    end_hour,
                ),
            )
        else:
            cursor.connection.rollback()
            return redirect(
                url_for("session.list_sessions", error="Unsupported session type")
            )

        cursor.connection.commit()
        return redirect(url_for("session.list_sessions"))

    except Exception as e:
        cursor.connection.rollback()
        return redirect(
            url_for(
                "session.update_page",
                session_name=session_name,
                session_date=session_date,
                start_hour=start_hour,
                end_hour=end_hour,
                error=f"Session update failed: {str(e)}",
            )
        )


@bp.route(
    "/delete/<session_name>/<session_date>/<start_hour>/<end_hour>", methods=["POST"]
)
@coach_required
def delete_session(session_name, session_date, start_hour, end_hour):
    try:
        cursor = get_cursor()

        # Delete specific session type data
        session_types = [
            "one_to_one_session",
            "class_session",
            "race",
            "individual_session",
        ]
        for type_name in session_types:
            cursor.execute(
                f"""
                DELETE FROM {type_name}
                WHERE session_name = %s AND session_date = %s
                AND start_hour = %s AND end_hour = %s
                """,
                (session_name, session_date, start_hour, end_hour),
            )

        # Delete base session
        cursor.execute(
            """
            DELETE FROM swimming_session
            WHERE session_name = %s AND session_date = %s
            AND start_hour = %s AND end_hour = %s AND coach_email = %s
            """,
            (session_name, session_date, start_hour, end_hour, current_user.id),
        )

        cursor.connection.commit()
        return redirect(url_for("session.list_sessions"))

    except Exception as e:
        cursor.connection.rollback()
        return redirect(
            url_for("session.list_sessions", error=f"Session deletion failed: {str(e)}")
        )


@bp.route("/coach_comments/view", methods=["POST"])
@coach_required
def read_coach_comments():
    try:
        cursor = get_cursor()
        data = request.form
        session_name = data["session_name"]
        session_date = data["session_date"]
        start_hour = data["start_hour"]
        end_hour = data["end_hour"]
        coach_email = current_user.id

        query = """
            SELECT swimmer_email, rating, comment FROM coach_rating
            WHERE session_name = %s
            AND session_date = %s
            AND start_hour = %s
            AND end_hour = %s
            AND coach_email = %s
        """

        cursor.execute(
            query, (session_name, session_date, start_hour, end_hour, coach_email)
        )
        results = cursor.fetchall()
        print(results)
        return render_template(
            "session/coach/list_comments.html",
            results=results,
            session_name=session_name,
        )

    except Exception as e:
        return redirect(
            url_for("session.list_sessions", error=f"Read comments failed: {str(e)}")
        )
