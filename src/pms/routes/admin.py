from hashlib import sha256

from flask import Blueprint, redirect, render_template, request, url_for

from pms.authorization import admin_required
from pms.db import get_cursor

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():
    try:
        cursor = get_cursor()

        cursor.execute("SELECT * FROM pms_user")
        users = cursor.fetchall()

        cursor.execute("SELECT * FROM swimming_session")
        sessions = cursor.fetchall()

        cursor.execute("SELECT * FROM benefit")
        benefits = cursor.fetchall()

        return render_template(
            "admin/dashboard.html",
            users=users,
            sessions=sessions,
            benefits=benefits,
        )
    except Exception as e:
        return render_template(
            "admin/dashboard.html",
            error=f"Failed to load dashboard: {str(e)}",
            users=[],
            sessions=[],
            benefits=[],
        )


@bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    role = request.args.get("role")
    try:
        cursor = get_cursor()

        # Base query
        query = """
            SELECT u.email, u.username, u.phone_no,
                   CASE
                       WHEN u.email IN (SELECT email FROM pms_admin) THEN 'admin'
                       WHEN u.email IN (SELECT email FROM coach) THEN 'coach'
                       WHEN u.email IN (SELECT email FROM swimmer) THEN 'swimmer'
                       WHEN u.email IN (SELECT email FROM lifeguard) THEN 'lifeguard'
                       ELSE 'unknown'
                   END AS role
            FROM pms_user u
        """
        conditions = []

        # Add conditions based on role
        if role == "admin":
            conditions.append("u.email IN (SELECT email FROM pms_admin)")
        elif role == "coach":
            conditions.append("u.email IN (SELECT email FROM coach)")
        elif role == "swimmer":
            conditions.append("u.email IN (SELECT email FROM swimmer)")
        elif role == "lifeguard":
            conditions.append("u.email IN (SELECT email FROM lifeguard)")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query)
        users = cursor.fetchall()

        return render_template("admin/users.html", users=users)
    except Exception as e:
        return render_template(
            "admin/users.html", error=f"Failed to load users: {str(e)}", users=[]
        )


@bp.route("/users/delete/<email>", methods=["POST"])
@admin_required
def delete_user(email):
    try:
        cursor = get_cursor()
        cursor.execute("DELETE FROM pms_user WHERE email = %s", (email,))
        cursor.connection.commit()
        return redirect(url_for("admin.list_users"))
    except Exception as e:
        return redirect(
            url_for("admin.list_users", error=f"Failed to delete user: {str(e)}")
        )


@bp.route("/sessions", methods=["GET"])
@admin_required
def list_sessions():
    session_type = request.args.get("type")
    try:
        cursor = get_cursor()

        # Define query based on session type
        if session_type == "class_session":
            query = """
                SELECT s.*
                FROM swimming_session s
                JOIN class_session cs
                ON s.session_name = cs.session_name
                AND s.session_date = cs.session_date
                AND s.start_hour = cs.start_hour
                AND s.end_hour = cs.end_hour
            """
        elif session_type == "individual_session":
            query = """
                SELECT s.*
                FROM swimming_session s
                JOIN individual_session isess
                ON s.session_name = isess.session_name
                AND s.session_date = isess.session_date
                AND s.start_hour = isess.start_hour
                AND s.end_hour = isess.end_hour
            """
        elif session_type == "one_to_one_session":
            query = """
                SELECT s.*
                FROM swimming_session s
                JOIN one_to_one_session osess
                ON s.session_name = osess.session_name
                AND s.session_date = osess.session_date
                AND s.start_hour = osess.start_hour
                AND s.end_hour = osess.end_hour
            """
        elif session_type == "race":
            query = """
                SELECT s.*
                FROM swimming_session s
                JOIN race r
                ON s.session_name = r.session_name
                AND s.session_date = r.session_date
                AND s.start_hour = r.start_hour
                AND s.end_hour = r.end_hour
            """
        else:
            # Base query to fetch all sessions
            query = "SELECT * FROM swimming_session"

        # Execute the query
        cursor.execute(query)
        sessions = cursor.fetchall()

        return render_template("admin/sessions.html", sessions=sessions)

    except Exception as e:
        return render_template(
            "admin/sessions.html",
            error=f"Failed to load sessions: {str(e)}",
            sessions=[],
        )


@bp.route("/benefits", methods=["GET"])
@admin_required
def list_benefits():
    try:
        cursor = get_cursor()
        cursor.execute("""
            SELECT
                b.benefit_id,
                b.swimmer_email,
                b.details,
                b.start_date,
                b.end_date,
                COALESCE(mb.bonus_amount, eb.bonus_amount) as bonus_amount,
                CASE
                    WHEN mb.benefit_id IS NOT NULL THEN 'Member'
                    WHEN eb.benefit_id IS NOT NULL THEN 'Enrollment'
                    ELSE 'General'
                END as benefit_type
            FROM benefit b
            LEFT JOIN benefit_member_bonus mb ON b.benefit_id = mb.benefit_id
            LEFT JOIN benefit_enrollment_bonus eb ON b.benefit_id = eb.benefit_id
            ORDER BY b.benefit_id DESC
        """)
        benefits = cursor.fetchall()
        return render_template("admin/benefits.html", benefits=benefits)
    except Exception as e:
        return render_template(
            "admin/benefits.html",
            error=f"Failed to load benefits: {str(e)}",
            benefits=[],
        )


@bp.route("/manage-benefits", methods=["GET", "POST"])
@admin_required
def manage_benefits():
    fetch_query = """
            SELECT
                b.benefit_id,
                b.swimmer_email,
                b.details,
                b.start_date,
                b.end_date,
                COALESCE(mb.bonus_amount, eb.bonus_amount) as bonus_amount,
                CASE
                    WHEN mb.benefit_id IS NOT NULL THEN 'Member'
                    WHEN eb.benefit_id IS NOT NULL THEN 'Enrollment'
                    ELSE 'General'
                END as benefit_type
            FROM benefit b
            LEFT JOIN benefit_member_bonus mb ON b.benefit_id = mb.benefit_id
            LEFT JOIN benefit_enrollment_bonus eb ON b.benefit_id = eb.benefit_id
            ORDER BY b.benefit_id DESC
        """
    if request.method == "POST":
        swimmer_email = request.form.get("swimmer_email")
        details = request.form.get("details")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        benefit_type = request.form.get("benefit_type")
        bonus_amount = request.form.get("bonus_amount")

        cursor = get_cursor()
        try:
            # Insert base benefit
            cursor.execute(
                "INSERT INTO benefit (swimmer_email, details, start_date, end_date) VALUES (%s, %s, %s, %s) RETURNING benefit_id",
                (swimmer_email, details, start_date, end_date),
            )
            benefit_id = cursor.fetchone()["benefit_id"]

            # Insert bonus if applicable
            if benefit_type in ["member", "enrollment"]:
                table = f"benefit_{benefit_type}_bonus"
                cursor.execute(
                    f"INSERT INTO {table} (benefit_id, bonus_amount) VALUES (%s, %s)",
                    (benefit_id, bonus_amount),
                )

            cursor.connection.commit()
            cursor.execute()
            benefits = cursor.fetchall()
            return render_template("admin/manage_benefits.html", benefits=benefits)
        except Exception as e:
            cursor.execute(fetch_query)
            benefits = cursor.fetchall()
            return render_template(
                "admin/manage_benefits.html",
                error=f"Failed to manage benefits: {str(e)}",
                benefits=benefits,
            )
    cursor = get_cursor()
    cursor.execute(fetch_query)
    benefits = cursor.fetchall()
    return render_template("admin/manage_benefits.html", benefits=benefits)


@bp.route("/add_user", methods=["POST"])
@admin_required
def add_user():
    try:
        cursor = get_cursor()

        # Get form data
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        phone_no = request.form.get("phone_no", None)
        forename = request.form["forename"]
        middlename = request.form.get("middlename", "")
        surname = request.form["surname"]
        balance = request.form.get("balance", 0)
        role = request.form["role"]

        # Hash the password using sha256
        password_hash = sha256(password.encode()).hexdigest()

        # Insert into pms_user
        cursor.execute(
            """
            INSERT INTO pms_user (email, password_hash, username, phone_no, forename,
            middlename, surname, balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                email,
                password_hash,
                username,
                phone_no,
                forename,
                middlename,
                surname,
                balance,
            ),
        )

        # Insert into role-specific table
        if role == "admin":
            cursor.execute("INSERT INTO pms_admin (email) VALUES (%s)", (email,))
        elif role == "coach":
            cursor.execute("INSERT INTO coach (email) VALUES (%s)", (email,))
        elif role == "swimmer":
            cursor.execute("INSERT INTO swimmer (email) VALUES (%s)", (email,))

        cursor.connection.commit()
        return redirect(url_for("admin.list_users"))

    except Exception as e:
        return redirect(
            url_for("admin.list_users", error=f"Failed to add user: {str(e)}")
        )


@bp.route("/add_session", methods=["POST"])
@admin_required
def add_session():
    try:
        cursor = get_cursor()

        # Get form data
        session_name = request.form["session_name"]
        session_date = request.form["session_date"]
        start_hour = request.form["start_hour"]
        end_hour = request.form["end_hour"]
        price = request.form.get("price", 0)
        coach_email = request.form["coach_email"]

        # Validate coach email
        cursor.execute("SELECT email FROM coach WHERE email = %s", (coach_email,))
        if not cursor.fetchone():
            raise ValueError("The provided coach email does not exist.")

        # Insert into swimming_session
        cursor.execute(
            """
            INSERT INTO swimming_session (session_name, session_date, start_hour,
            end_hour, price, coach_email)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (session_name, session_date, start_hour, end_hour, price, coach_email),
        )

        cursor.connection.commit()
        return redirect(url_for("admin.list_sessions"))

    except Exception as e:
        return redirect(
            url_for("admin.list_sessions", error=f"Failed to add session: {str(e)}")
        )


@bp.route(
    "/delete/<session_name>/<session_date>/<start_hour>/<end_hour>", methods=["POST"]
)
@admin_required
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
            AND start_hour = %s AND end_hour = %s
            """,
            (session_name, session_date, start_hour, end_hour),
        )

        cursor.connection.commit()
        return redirect(url_for("admin.list_sessions"))

    except Exception as e:
        cursor.connection.rollback()
        return redirect(
            url_for("admin.list_sessions", error=f"Session deletion failed: {str(e)}")
        )


@bp.route("/reports", methods=["GET", "POST"])
@admin_required
def reports():
    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        report_type = request.form.get("report_type")

        try:
            cursor = get_cursor()
            if report_type == "session":
                cursor.execute(
                    """
                    SELECT COUNT(*) AS total_sessions,
                           SUM(CASE WHEN session_name IN (SELECT session_name FROM one_to_one_session) THEN 1 ELSE 0 END) AS one_to_one_count,
                           SUM(CASE WHEN session_name IN (SELECT session_name FROM class_session) THEN 1 ELSE 0 END) AS class_count,
                           SUM(CASE WHEN session_name IN (SELECT session_name FROM race) THEN 1 ELSE 0 END) AS race_count
                    FROM swimming_session
                    WHERE session_date BETWEEN %s AND %s
                    """,  # noqa: E501
                    (start_date, end_date),
                )
                report_data = cursor.fetchone()
                report_title = "Session Report"

            elif report_type == "competition":
                # Fetch summary statistics
                cursor.execute(
                    """
                   SELECT
    COUNT(r.session_name) AS total_races,
    COALESCE(SUM(rr.no_of_participants), 0) AS total_participants
FROM
    race r
LEFT JOIN
    race_report rr ON r.report_id = rr.report_id
WHERE
    r.session_date BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE);

                    """,
                    (start_date, end_date),
                )
                summary_data = cursor.fetchone()

                # Fetch list of individual competitions
                cursor.execute(
                    """
                    SELECT
    r.session_name AS competition_name,
    r.session_date AS competition_date,
    r.start_hour,
    r.end_hour,
    r.stroke_style,
    COALESCE(rr.no_of_participants, 0) AS no_of_participants
FROM
    race r
LEFT JOIN
    race_report rr ON r.report_id = rr.report_id
WHERE
    r.session_date BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE)
ORDER BY
    r.session_date, r.start_hour;

                    """,
                    (start_date, end_date),
                )
                competition_list = cursor.fetchall()

                report_data = {
                    "summary": summary_data,
                    "competitions": competition_list,
                }
                report_title = "Competition Report"

            elif report_type == "employee":
                # Lifeguard scheduled workdays
                cursor.execute(
                    """
                    SELECT
                        l.email AS lifeguard_email,
                        COUNT(DISTINCT d::DATE) AS scheduled_work_days
                    FROM
                        work_days_of_the_week w
                    JOIN
                        GENERATE_SERIES(%s::DATE, %s::DATE, '1 day'::INTERVAL) d
                        ON w.work_day = TO_CHAR(d, 'Day')
                    JOIN
                        lifeguard l ON l.email = w.email
                    GROUP BY
                        l.email
                    """,
                    (start_date, end_date),
                )
                lifeguard_scheduled_data = cursor.fetchall()

                # Lifeguard actual workdays (attendance)
                cursor.execute(
                    """
                    SELECT
                        lw.email AS lifeguard_email,
                        COUNT(DISTINCT lw.watch_date) AS attended_work_days
                    FROM
                        lifeguard_watch lw
                    WHERE
                        lw.watch_date BETWEEN %s AND %s
                    GROUP BY
                        lw.email
                    """,
                    (start_date, end_date),
                )
                lifeguard_attendance_data = cursor.fetchall()

                # Combine lifeguard data
                lifeguard_data = {}
                for record in lifeguard_scheduled_data:
                    lifeguard_data[record["lifeguard_email"]] = {
                        "scheduled_work_days": record["scheduled_work_days"],
                        "attended_work_days": 0,
                    }
                for record in lifeguard_attendance_data:
                    if record["lifeguard_email"] in lifeguard_data:
                        lifeguard_data[record["lifeguard_email"]][
                            "attended_work_days"
                        ] = record["attended_work_days"]
                    else:
                        lifeguard_data[record["lifeguard_email"]] = {
                            "scheduled_work_days": 0,
                            "attended_work_days": record["attended_work_days"],
                        }

                # Coach workdays
                cursor.execute(
                    """
                    SELECT
                        c.email AS coach_email,
                        COUNT(DISTINCT s.session_date) AS work_days
                    FROM
                        coach c
                    JOIN
                        swimming_session s ON c.email = s.coach_email
                    WHERE
                        s.session_date BETWEEN %s AND %s
                    GROUP BY
                        c.email
                    """,
                    (start_date, end_date),
                )
                coach_data = cursor.fetchall()

                report_data = {
                    "lifeguards": lifeguard_data,
                    "coaches": coach_data,
                }
                report_title = "Employee Report"
            else:
                return redirect(url_for("admin.reports", error="Invalid report type."))

            return render_template(
                "admin/reports.html",
                report_data=report_data,
                report_title=report_title,
                start_date=start_date,
                end_date=end_date,
                report_type=report_type,
            )
        except Exception as e:
            return redirect(
                url_for("admin.reports", error=f"Failed to generate report: {str(e)}")
            )
    return render_template("admin/reports.html")


@bp.route("/users/update_role/<email>", methods=["POST"])
@admin_required
def update_user_role(email):
    try:
        cursor = get_cursor()

        # Get the new role from the form
        new_role = request.form["role"]

        # Remove the user from all role-specific tables first
        cursor.execute("DELETE FROM pms_admin WHERE email = %s", (email,))
        cursor.execute("DELETE FROM coach WHERE email = %s", (email,))
        cursor.execute("DELETE FROM swimmer WHERE email = %s", (email,))
        cursor.execute("DELETE FROM lifeguard WHERE email = %s", (email,))

        # Add the user to the corresponding role-specific table
        if new_role == "admin":
            cursor.execute("INSERT INTO pms_admin (email) VALUES (%s)", (email,))
        elif new_role == "coach":
            cursor.execute("INSERT INTO coach (email) VALUES (%s)", (email,))
        elif new_role == "swimmer":
            cursor.execute("INSERT INTO swimmer (email) VALUES (%s)", (email,))
        elif new_role == "lifeguard":
            cursor.execute("INSERT INTO lifeguard (email) VALUES (%s)", (email,))

        cursor.connection.commit()
        return redirect(url_for("admin.list_users"))
    except Exception as e:
        return redirect(
            url_for(
                "admin.list_users",
                error=f"Failed to update user role for {email}: {str(e)}",
            )
        )
