from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from pms.authorization import is_user_admin
from pms.db import get_cursor

bp = Blueprint("benefit", __name__, url_prefix="/benefit")


@bp.route("/")
@login_required
def index():
    if not is_user_admin(current_user.id):
        return redirect(
            url_for("main.index", error="You are not authorized to view this page.")
        )

    cursor = get_cursor()
    cursor.execute("""
        SELECT b.*,
            COALESCE(mb.bonus_amount, eb.bonus_amount) as bonus_amount,
            CASE
                WHEN mb.benefit_id IS NOT NULL THEN 'member'
                WHEN eb.benefit_id IS NOT NULL THEN 'enrollment'
                ELSE 'general'
            END as benefit_type
        FROM benefit b
        LEFT JOIN benefit_member_bonus mb ON b.benefit_id = mb.benefit_id
        LEFT JOIN benefit_enrollment_bonus eb ON b.benefit_id = eb.benefit_id
    """)
    benefits = cursor.fetchall()
    return render_template("benefit/benefits.html", benefits=benefits)


def get_benefit_type(benefit_id: int) -> str:
    cursor = get_cursor()
    # Check member bonus
    cursor.execute(
        "SELECT bonus_amount FROM benefit_member_bonus WHERE benefit_id = %s",
        (benefit_id,),
    )
    if cursor.fetchone():
        return "member"
    # Check enrollment bonus
    cursor.execute(
        "SELECT bonus_amount FROM benefit_enrollment_bonus WHERE benefit_id = %s",
        (benefit_id,),
    )
    if cursor.fetchone():
        return "enrollment"
    return "general"


def get_bonus_amount(benefit_id: int, benefit_type: str) -> float:
    if benefit_type == "general":
        return 0.0
    cursor = get_cursor()
    table = f"benefit_{benefit_type}_bonus"
    cursor.execute(
        f"SELECT bonus_amount FROM {table} WHERE benefit_id = %s", (benefit_id,)
    )
    result = cursor.fetchone()
    return result["bonus_amount"] if result else 0.0


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if not is_user_admin(current_user.id):
        return redirect(
            url_for("main.index", error="You are not authorized to view this page.")
        )

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

            flash("Benefit created successfully!", "success")
            return redirect(url_for("benefit.index"))
        except Exception as e:
            flash(f"Error creating benefit: {str(e)}", "error")
            return redirect(url_for("benefit.create"))

    return render_template("benefit/benefit_create.html")


@bp.route("/edit/<id>", methods=["GET", "POST"])
@login_required
def edit(id: int):
    if not is_user_admin(current_user.id):
        return redirect(
            url_for("main.index", error="You are not authorized to view this page.")
        )

    cursor = get_cursor()
    benefit_type = get_benefit_type(id)

    if request.method == "POST":
        # Get

        swimmer_email = request.form.get("swimmer_email")
        details = request.form.get("details")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        bonus_amount = request.form.get("bonus_amount")

        try:
            cursor.execute(
                "UPDATE benefit SET swimmer_email = %s, details = %s, start_date = %s, end_date = %s WHERE benefit_id = %s",
                (swimmer_email, details, start_date, end_date, id),
            )

            if benefit_type != "general":
                table = f"benefit_{benefit_type}_bonus"
                cursor.execute(
                    f"UPDATE {table} SET bonus_amount = %s WHERE benefit_id = %s",
                    (bonus_amount, id),
                )

            flash("Benefit updated successfully!", "success")
            return redirect(url_for("admin.manage_benefits"))
        except Exception as e:
            flash(f"Error updating benefit: {str(e)}", "error")
            return redirect(url_for("admin.manage_benefits", id=id))

    cursor.execute("SELECT * FROM benefit WHERE benefit_id = %s", (id,))
    benefit = cursor.fetchone()

    if not benefit:
        flash("Benefit not found!", "error")
        return redirect(url_for("admin.manage_benefit"))

    bonus_amount = get_bonus_amount(id, benefit_type)
    return render_template(
        "benefit/edit.html",
        benefit=benefit,
        benefit_type=benefit_type,
        bonus_amount=bonus_amount,
    )


@bp.route("/delete/<id>", methods=["POST"])
@login_required
def delete(id: int):
    if not is_user_admin(current_user.id):
        return redirect(
            url_for("main.index", error="You are not authorized to view this page.")
        )

    cursor = get_cursor()
    try:
        cursor.execute("DELETE FROM benefit WHERE benefit_id = %s", (id,))
        flash("Benefit deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting benefit: {str(e)}", "error")

    return redirect(url_for("benefit.index"))
