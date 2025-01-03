import datetime

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from pms.authorization import is_user_coach
from pms.db import get_cursor

bp = Blueprint("calendar", __name__, url_prefix="/calendar")


@bp.route("/", methods=["GET"])
@login_required
def view_calendar():
    try:
        cursor = get_cursor()

        current_date = str(datetime.datetime.now())[0:10]
        current_time = str(datetime.datetime.now())[11:19]
        # Get all upcoming sessions of user
        # For coaches
        if is_user_coach(current_user.id):
            cursor.execute(
                """
                WITH session_details AS (
                    -- One-to-One Sessions
                    SELECT
                        s.*,
                        'one_to_one' as session_type,
                        oto.special_request_comment as extra_info,
                        NULL as max_capacity,
                        NULL as min_age,
                        NULL as max_age,
                        NULL as class_level,
                        NULL as stroke_style
                    FROM swimming_session s
                    JOIN one_to_one_session oto ON s.session_name = oto.session_name
                        AND s.session_date = oto.session_date
                        AND s.start_hour = oto.start_hour
                        AND s.end_hour = oto.end_hour
                    WHERE s.coach_email = %s

                    UNION ALL

                    -- Class Sessions
                    SELECT
                        s.*,
                        'class' as session_type,
                        NULL as extra_info,
                        c.max_capacity,
                        c.min_age,
                        c.max_age,
                        c.class_level,
                        NULL as stroke_style
                    FROM swimming_session s
                    JOIN class_session c ON s.session_name = c.session_name
                        AND s.session_date = c.session_date
                        AND s.start_hour = c.start_hour
                        AND s.end_hour = c.end_hour
                    WHERE s.coach_email = %s

                    UNION ALL

                    -- Race Sessions
                    SELECT
                        s.*,
                        'race' as session_type,
                        NULL as extra_info,
                        NULL as max_capacity,
                        r.min_age,
                        r.max_age,
                        NULL as class_level,
                        r.stroke_style
                    FROM swimming_session s
                    JOIN race r ON s.session_name = r.session_name
                        AND s.session_date = r.session_date
                        AND s.start_hour = r.start_hour
                        AND s.end_hour = r.end_hour
                    WHERE s.coach_email = %s

                    UNION ALL

                    -- Individual Sessions
                    SELECT
                        s.*,
                        'individual' as session_type,
                        CONCAT(i.number_of_months, ' months') as extra_info,
                        NULL as max_capacity,
                        NULL as min_age,
                        NULL as max_age,
                        NULL as class_level,
                        NULL as stroke_style
                    FROM swimming_session s
                    JOIN individual_session i ON s.session_name = i.session_name
                        AND s.session_date = i.session_date
                        AND s.start_hour = i.start_hour
                        AND s.end_hour = i.end_hour
                    WHERE s.coach_email = %s
                )
                SELECT * FROM session_details
                WHERE (session_date > %s) OR (session_date = %s AND end_hour > %s)
                ORDER BY session_date DESC, start_hour DESC
            """,
                (
                    current_user.id,
                    current_user.id,
                    current_user.id,
                    current_user.id,
                    current_date,
                    current_date,
                    current_time,
                ),
            )
        # For swimmers
        else:
            cursor.execute(
                """
                WITH session_details AS (
                    SELECT
                        s.*,
                        CASE
                            WHEN oto.session_name IS NOT NULL THEN 'one_to_one'
                            WHEN c.session_name IS NOT NULL THEN 'class'
                            WHEN r.session_name IS NOT NULL THEN 'race'
                            WHEN i.session_name IS NOT NULL THEN 'individual'
                        END as session_type,
                        CASE
                            WHEN oto.special_request_comment IS NOT NULL THEN oto.special_request_comment
                            WHEN i.number_of_months IS NOT NULL THEN CONCAT(i.number_of_months, ' months')
                            ELSE NULL
                        END as extra_info,
                        c.max_capacity,
                        COALESCE(c.min_age, r.min_age) as min_age,
                        COALESCE(c.max_age, r.max_age) as max_age,
                        c.class_level,
                        r.stroke_style
                    FROM swimmer_attend_session sas
                    JOIN swimming_session s ON sas.session_name = s.session_name
                        AND sas.session_date = s.session_date
                        AND sas.start_hour = s.start_hour
                        AND sas.end_hour = s.end_hour
                    LEFT JOIN one_to_one_session oto ON s.session_name = oto.session_name
                        AND s.session_date = oto.session_date
                        AND s.start_hour = oto.start_hour
                        AND s.end_hour = oto.end_hour
                    LEFT JOIN class_session c ON s.session_name = c.session_name
                        AND s.session_date = c.session_date
                        AND s.start_hour = c.start_hour
                        AND s.end_hour = c.end_hour
                    LEFT JOIN race r ON s.session_name = r.session_name
                        AND s.session_date = r.session_date
                        AND s.start_hour = r.start_hour
                        AND s.end_hour = r.end_hour
                    LEFT JOIN individual_session i ON s.session_name = i.session_name
                        AND s.session_date = i.session_date
                        AND s.start_hour = i.start_hour
                        AND s.end_hour = i.end_hour
                    WHERE sas.email = %s
                )
                SELECT * FROM session_details
                WHERE (session_date > %s) OR (session_date = %s AND end_hour > %s)
                ORDER BY session_date DESC, start_hour DESC
            """,
                (current_user.id, current_date, current_date, current_time),
            )

        sessions = cursor.fetchall()
        return render_template("calendar.html", sessions=sessions)

    except Exception as e:
        return redirect(
            url_for("main.index", error=f"Could not load calendar: {str(e)}")
        )
