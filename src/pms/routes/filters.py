from flask import Blueprint, render_template, request

from pms.db import get_cursor  # TODO: Implement database connection
from flask_login import current_user, login_required

bp = Blueprint("filters", __name__)


@bp.route("/filter_sessions", methods=["GET", "POST"])
@login_required
def filter_sessions():
    results = ["a", "b", "c", "d"]
    status = "get_result"
    cur = get_cursor()
    cur.execute("SELECT username FROM pms_user NATURAL JOIN coach", ())
    coach_results = cur.fetchall()
    cur.execute("SELECT DISTINCT pool_city FROM pool")
    location_results = cur.fetchall()
    if request.method == "POST":
        data = request.form
        class_type_dict = {
            "Individual": "individual_session",
            "One-to-One": "one_to_one_session",
            "Class": "class_session",
            "Race": "race",
        }
        query_attributes = ["pool_city", "session_date", "start_hour", "end_hour"]
        secondary_attributes = [
            "class_type",
            "instructor",
        ]
        selected_values = {}
        status = "filter_result"
        nonempty_params = []
        session_params = []
        class_type_mapping = {
            "Individual": ["number_of_months"],
            "Class": ["class_level", "signup_date"],
            "Race": ["stroke_style"],
        }
        user_class_params = []
        init_filter_params(
            data,
            query_attributes,
            secondary_attributes,
            nonempty_params,
            selected_values,
            class_type_mapping,
            session_params,
            user_class_params,
        )
        cur = get_cursor()
        age_query = """SELECT EXTRACT(YEAR FROM AGE(birth_date)) AS age
                        FROM pms_user
                        WHERE email = %s;
        """
        cur.execute(age_query, (current_user.id,))
        age_result = cur.fetchone()["age"]
        print(age_result)
        session_query = ""
        session_params_operators = {
            "signup_date": ">=",
            "class_level": "=",
            "age_group": "=",
            "stroke_style": "=",
            "number_of_months": "=",
        }
        for i in range(0, len(session_params)):
            selected_values[session_params[i]] = data[session_params[i]]
            session_query += "{session_params} {operator} %s AND ".format(
                session_params=session_params[i],
                operator=session_params_operators[session_params[i]],
            )
        user_params_operators = {"min_age": "<=", "max_age": ">="}
        for i in user_class_params:
            session_query += "{user_param} {operator} %s AND ".format(
                user_param=i,
                operator=user_params_operators[i],
            )
        session_query = session_query[:-5]

        query = """WITH first_filter AS (
                    SELECT session_name, session_date, start_hour, end_hour, price
                    FROM swimming_session
                    JOIN coach ON swimming_session.coach_email=coach.email
                    NATURAL JOIN booking NATURAL JOIN pool
                """
        if len(nonempty_params) > 0:
            query += "WHERE "
        else:
            query += ")"
        query_operators = {
            "pool_city": "=",
            "session_date": "=",
            "start_hour": ">=",
            "end_hour": "<=",
        }
        for i in range(0, len(nonempty_params)):
            selected_values.update({nonempty_params[i]: data[nonempty_params[i]]})
            subq = "{x} {operator} %s AND ".format(
                x=nonempty_params[i], operator=query_operators[nonempty_params[i]]
            )
            query += subq
        query = query[:-5] + ")"
        query += (
            "\nSELECT DISTINCT * FROM {dict_entry} NATURAL JOIN first_filter\n".format(
                dict_entry=class_type_dict[data["class_type"]]
            )
        )
        if len(session_query) + len(user_class_params) > 0:
            query += "WHERE "
        query += session_query
        print(query)
        total_list = []
        for i in nonempty_params:
            total_list.append(data[i])
        for i in session_params:
            total_list.append(data[i])
        if len(user_class_params) > 0:
            total_list.append(age_result)
            total_list.append(age_result)
        total_tuple = tuple(total_list)
        print(total_tuple)
        cur.execute(query, total_tuple)
        results = cur.fetchall()
        return render_template(
            "filter/filter.html",
            selected_values=selected_values,
            results=results,
            len=len(results),
            status=status,
            coach_results=coach_results,
            coach_len=len(coach_results),
            location_results=location_results,
            location_results_len=len(location_results),
        )
    return render_template(
        "filter/filter.html",
        results=results,
        len=len(results),
        status=status,
        coach_results=coach_results,
        coach_len=len(coach_results),
        location_results=location_results,
        location_results_len=len(location_results),
    )


def init_filter_params(
    data,
    query_attributes,
    secondary_attributes,
    nonempty_params,
    selected_values,
    class_type_mapping,
    session_params,
    user_class_params,
):
    for key, value in data.items():
        if value and (key in query_attributes):
            nonempty_params.append(key)
        elif value and (key in secondary_attributes):
            selected_values[key] = value
        elif (
            value
            and data["class_type"]
            and key in class_type_mapping[data["class_type"]]
        ):
            session_params.append(key)
    if data["class_type"] == "Class" or data["class_type"] == "Race":
        user_class_params.append("min_age")
        user_class_params.append("max_age")


@bp.route("/sessions", methods=["POST"])
@login_required
def session_info():
    results = ["a", "b", "c", "d"]
    cur = get_cursor()
    if request.method == "POST":
        data = request.form
        reason = ""

        existence_query = """SELECT *
                    FROM swimmer_attend_session S
                    WHERE S.email = %s AND
                    S.session_date = %s AND
                    (S.start_hour <= %s OR S.end_hour >= %s);"""
        cur.execute(
            existence_query,
            (
                current_user.id,
                data["session_date"],
                data["start_hour"],
                data["end_hour"],
            ),
        )
        isExists = cur.fetchone()
        if isExists:
            reason = "Course conflict"
        cost_query = """ SELECT balance, price
                    FROM pms_user P, swimming_session S
                    WHERE P.email = %s AND
                    S.session_name = %s AND
                    S.session_date = %s AND
                    S.start_hour = %s AND
                    S.end_hour = %s;
                    """
        cur.execute(
            cost_query,
            (
                current_user.id,
                data["session_name"],
                data["session_date"],
                data["start_hour"],
                data["end_hour"],
            ),
        )
        cost_json = cur.fetchone()
        balance = cost_json["balance"]
        price = cost_json["price"]
        if balance < price:
            reason = "Balance not enough"

        date_query = """SELECT * FROM swimming_session S
                        WHERE S.session_name = %s AND
                        S.session_date = %s AND S.start_hour = %s
                        AND S.end_hour = %s AND
                        S.session_date < CURRENT_DATE OR
                        (S.session_date = CURRENT_DATE AND S.start_hour < CURRENT_TIME);
        """
        cur.execute(
            date_query,
            (
                data["session_name"],
                data["session_date"],
                data["start_hour"],
                data["end_hour"],
            ),
        )
        date_result = cur.fetchone()
        if date_result:
            reason = "Session no longer available"

        signup_date_query = """SELECT * FROM swimming_session S
                        NATURAL JOIN class_session C
                        WHERE S.session_name = %s AND
                        S.session_date = %s AND S.start_hour = %s
                        AND S.end_hour = %s AND
                        C.signup_date < CURRENT_DATE;
        """
        cur.execute(
            signup_date_query,
            (
                data["session_name"],
                data["session_date"],
                data["start_hour"],
                data["end_hour"],
            ),
        )
        signup_date_result = cur.fetchone()
        if signup_date_result:
            reason = "Signup deadline is passed"

        class_type_dict = {
            "Individual": "individual_session",
            "One-to-One": "one_to_one_session",
            "Class": "class_session",
            "Race": "race",
        }

        query = """SELECT *
                    FROM swimming_session S
                    NATURAL JOIN {dict_entry}
                    WHERE S.session_name = %s AND
                    S.session_date = %s AND S.start_hour = %s
                    AND S.end_hour = %s;""".format(
            dict_entry=class_type_dict[data["class_type"]]
        )
        cur.execute(
            query,
            (
                data["session_name"],
                data["session_date"],
                data["start_hour"],
                data["end_hour"],
            ),
        )
        results = cur.fetchone()
        if (
            results["max_capacity"]
            and results["number_of_participants"]
            and results["max_capacity"] == results["number_of_participants"]
        ):
            reason = "Class full"

        results["duration"] = (
            (results["end_hour"].hour - results["start_hour"].hour) * 60
            + results["end_hour"].minute
            - results["start_hour"].minute
        )
        label_converter = {}
        l1 = {}
        ignore_list = ["end_hour"]
        for key, value in results.items():
            if value and key not in ignore_list:
                l1[key] = value
        results = l1
        results["price"] = "$" + str(results["price"])
        results["duration"] = str(results["duration"]) + " minutes"
        for key, value in results.items():
            label_converter[key] = key.replace("_", " ").title()
        return render_template(
            "filter/session.html",
            results=results,
            len=len(results),
            label_converter=label_converter,
            label_converter_len=len(label_converter),
            reason=reason,
            canBeTaken=(len(reason) == 0),
        )
    return render_template(
        "filter/session.html",
        results=results,
        len=len(results),
    )
