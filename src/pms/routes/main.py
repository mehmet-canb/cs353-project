from flask import Blueprint, redirect, render_template, url_for, request

from pms import get_cursor  # TODO: Implement database connection

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # Example of executing a raw SQL query
    # cur = get_cursor()
    # cur.execute("SELECT * FROM your_table WHERE condition = %s", ("value",))
    # results = cur.fetchall()
    results = []

    return render_template("index.html", results=results)


@bp.route("/add_item", methods=["POST"])
def add_item():
    # db = get_db()
    # cur = get_cursor()

    # cur.execute(
    #     "INSERT INTO your_table (column1, column2) VALUES (%s, %s)",
    #     ("value1", "value2"),
    # )
    # db.commit()  # Don't forget to commit for INSERT/UPDATE/DELETE operations

    return redirect(url_for("main.index"))


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
            "one-to-one": "one_to_one_session",
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
        query += "\nSELECT * FROM {dict_entry} NATURAL JOIN first_filter\n".format(
            dict_entry=class_type_dict[data["class_type"]]
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
            "filter.html",
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
        "filter.html",
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
