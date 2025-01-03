from flask import Blueprint, render_template, request

from pms.db import get_cursor  # TODO: Implement database connection

bp = Blueprint("filters", __name__)


@bp.route("/filter_sessions", methods=["GET", "POST"])
def filter_sessions():
    results = ["a", "b", "c", "d"]
    status = "get_result"
    cur = get_cursor()
    cur.execute("SELECT username FROM pms_user NATURAL JOIN coach", ())
    coach_results = cur.fetchall()
    cur.execute("SELECT pool_city FROM pool")
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
            "Class": ["age_group", "class_level", "signup_date"],
            "Race": ["age_group", "stroke_style"],
        }
        init_filter_params(
            data,
            query_attributes,
            secondary_attributes,
            nonempty_params,
            selected_values,
            class_type_mapping,
            session_params,
        )
        cur = get_cursor()
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
            if i == len(session_params) - 1:
                session_query += "{session_params} {operator} %s".format(
                    session_params=session_params[i],
                    operator=session_params_operators[session_params[i]],
                )
            else:
                session_query += "{session_params} {operator} %s AND ".format(
                    session_params=session_params[i],
                    operator=session_params_operators[session_params[i]],
                )
        query = """WITH first_filter AS (
                    SELECT session_name, session_date, start_hour, end_hour, price
                    FROM swimming_session
                    JOIN coach ON swimming_session.coach_email=coach.email
                    NATURAL JOIN lane NATURAL JOIN pool
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
            if i == len(nonempty_params) - 1:
                subq = "{x} {operator} %s)".format(
                    x=nonempty_params[i], operator=query_operators[nonempty_params[i]]
                )
                query += subq
            else:
                subq = "{x} {operator} %s AND ".format(
                    x=nonempty_params[i], operator=query_operators[nonempty_params[i]]
                )
                query += subq
        query += (
            "\nSELECT DISTINCT * FROM {dict_entry} NATURAL JOIN first_filter\n".format(
                dict_entry=class_type_dict[data["class_type"]]
            )
        )
        if len(session_query) > 0:
            query += "WHERE "
        query += session_query
        print(query)
        total_list = []
        for i in nonempty_params:
            total_list.append(data[i])
        for i in session_params:
            total_list.append(data[i])
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


@bp.route("/sessions", methods=["POST"])
def session_info():
    results = ["a", "b", "c", "d"]
    status = "get_result"
    cur = get_cursor()
    if request.method == "POST":
        data = request.form
        query = """SELECT *
                    FROM swimming_session S NATURAL LEFT OUTER JOIN race NATURAL LEFT
                    OUTER JOIN class_session NATURAL LEFT OUTER JOIN individual_session
                    NATURAL LEFT OUTER JOIN one_to_one_session
                    WHERE S.session_name = %s AND
                    S.session_date = %s AND S.start_hour = %s
                    AND S.end_hour = %s;"""
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
        print(
            (results["end_hour"].hour - results["start_hour"].hour) * 60
            + results["end_hour"].minute
            - results["start_hour"].minute
        )
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
            status=status,
            label_converter=label_converter,
            label_converter_len=len(label_converter),
        )
    return render_template(
        "filter/session.html",
        results=results,
        len=len(results),
        status=status,
    )
