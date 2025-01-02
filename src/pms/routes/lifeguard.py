from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from pms.db import get_cursor

bp = Blueprint("lifeguard", __name__, url_prefix="/lifeguard")


def is_lifeguard(email):
    """Helper function to check if user is a lifeguard"""
    cursor = get_cursor()
    cursor.execute(
        """
        SELECT 1 FROM lifeguard
        WHERE email = %s
        """,
        [email],
    )
    result = cursor.fetchone() is not None
    return result


@bp.route("/list")
@login_required
def lifeguard_list():
    if not is_lifeguard(current_user.id):
        flash("Access denied: You are not a lifeguard")
        return redirect(url_for("index"))

    cursor = get_cursor()
    # Get contracted work days
    cursor.execute(
        """
        SELECT work_day
        FROM work_days_of_the_week
        WHERE email = %s
        ORDER BY
            CASE
                WHEN work_day = 'Monday' THEN 1
                WHEN work_day = 'Tuesday' THEN 2
                WHEN work_day = 'Wednesday' THEN 3
                WHEN work_day = 'Thursday' THEN 4
                WHEN work_day = 'Friday' THEN 5
                WHEN work_day = 'Saturday' THEN 6
                WHEN work_day = 'Sunday' THEN 7
            END
        """,
        [current_user.id],
    )
    contracted_days = [row["work_day"] for row in cursor.fetchall()]

    # Get all watches with pool details
    cursor.execute(
        """
        SELECT
            lw.pool_id,
            p.pool_name,
            lw.watch_date,
            lw.start_hour,
            lw.end_hour
        FROM lifeguard_watch lw
        JOIN pool p ON lw.pool_id = p.pool_id
        WHERE lw.email = %s
        ORDER BY lw.watch_date DESC, lw.start_hour DESC
        """,
        [current_user.id],
    )
    watches = cursor.fetchall()
    return render_template(
        "lifeguard/list.html", contracted_days=contracted_days, watches=watches
    )


@bp.route("/enroll", methods=["GET", "POST"])
@login_required
def lifeguard_enroll():
    if not is_lifeguard(current_user.id):
        flash("Access denied: You are not a lifeguard")
        return redirect(url_for("index"))

    cursor = get_cursor()
    error = None

    if request.method == "POST":
        pool_id = request.form.get("pool_id")
        watch_date = request.form.get("watch_date")
        start_hour = request.form.get("start_hour")
        end_hour = request.form.get("end_hour")

        if start_hour >= end_hour:
            error = "Start hour must be less than end hour"
            return render_template("lifeguard/enroll.html", error=error)

        # Check for time overlap
        cursor.execute(
            """
            SELECT 1
            FROM lifeguard_watch
            WHERE email = %s
            AND watch_date = %s
            AND (
                (start_hour <= %s AND end_hour > %s)
                OR
                (start_hour < %s AND end_hour >= %s)
                OR
                (start_hour >= %s AND end_hour <= %s)
            )
            """,
            [
                current_user.id,
                watch_date,
                start_hour,
                start_hour,
                end_hour,
                end_hour,
                start_hour,
                end_hour,
            ],
        )

        if cursor.fetchone():
            error = "You already have a watch duty during these hours"
        else:
            try:
                cursor.execute(
                    """
                    INSERT INTO lifeguard_watch
                    (email, pool_id, watch_date, start_hour, end_hour)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [current_user.id, pool_id, watch_date, start_hour, end_hour],
                )
                cursor.connection.commit()
                flash("Watch duty added successfully")
                return redirect(url_for("lifeguard.lifeguard_list"))
            except Exception as e:
                cursor.connection.rollback()
                error = f"An error occurred: {str(e)}"

    # Get pools for the form
    cursor.execute("SELECT pool_id, pool_name FROM pool")
    pools = cursor.fetchall()
    return render_template("lifeguard/enroll.html", pools=pools, error=error)


# Change the delete_watch route definition:


@bp.route("/delete/<pool_id>/<watch_date>/<start_hour>/<end_hour>", methods=["POST"])
@login_required
def delete_watch(pool_id, watch_date, start_hour, end_hour):
    if not is_lifeguard(current_user.id):
        flash("Access denied: You are not a lifeguard")
        return redirect(url_for("index"))

    try:
        cursor = get_cursor()
        cursor.execute(
            """
            DELETE FROM lifeguard_watch
            WHERE email = %s
            AND pool_id = %s
            AND watch_date = %s
            AND start_hour = %s
            AND end_hour = %s
            """,
            [current_user.id, pool_id, watch_date, start_hour, end_hour],
        )
        cursor.connection.commit()
        flash("Watch duty deleted successfully")
    except Exception as e:
        flash(f"Error deleting watch duty: {str(e)}")
    finally:
        cursor.close()

    return redirect(url_for("lifeguard.lifeguard_list"))
