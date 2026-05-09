from flask import Blueprint, render_template, request, session, redirect, url_for
import mysql.connector
from config import Config

teacher_bp = Blueprint("teacher", __name__)


@teacher_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("auth.login"))

    return render_template("teacher/teacher_dashboard.html")


@teacher_bp.route("/select-courses", methods=["GET", "POST"])
def select_courses():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM teachers WHERE user_id = %s",
        (session["user_id"],)
    )
    teacher = cursor.fetchone()

    if not teacher:
        cursor.close()
        conn.close()
        return "No teacher found"

    teacher_id = teacher["id"]

    if request.method == "POST":
        selected_courses = request.form.getlist("course_ids")

        cursor.execute(
            "DELETE FROM teacher_course_selection WHERE teacher_id = %s",
            (teacher_id,)
        )

        for course_id in selected_courses:
            cursor.execute(
                "INSERT INTO teacher_course_selection (teacher_id, course_id) VALUES (%s, %s)",
                (teacher_id, course_id)
            )

        conn.commit()

    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    cursor.execute(
        "SELECT course_id FROM teacher_course_selection WHERE teacher_id = %s",
        (teacher_id,)
    )
    selected = cursor.fetchall()

    selected_courses = [str(row["course_id"]) for row in selected]

    cursor.close()
    conn.close()

    return render_template(
        "teacher/select_courses.html",
        courses=courses,
        selected_courses=selected_courses
    )


@teacher_bp.route("/set-availability", methods=["GET", "POST"])
def set_availability():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM teachers WHERE user_id = %s",
        (session["user_id"],)
    )
    teacher = cursor.fetchone()

    if not teacher:
        cursor.close()
        conn.close()
        return "No teacher found"

    teacher_id = teacher[0]

    if request.method == "POST":
        monday_slots = request.form.getlist("monday_slots")
        thursday_slots = request.form.getlist("thursday_slots")

        cursor.execute(
            "DELETE FROM teacher_availability WHERE teacher_id = %s",
            (teacher_id,)
        )

        for slot in monday_slots:
            for day in ["Monday", "Tuesday", "Wednesday"]:
                cursor.execute(
                    "INSERT INTO teacher_availability (teacher_id, day, slot_number) VALUES (%s, %s, %s)",
                    (teacher_id, day, int(slot))
                )

        for slot in thursday_slots:
            for day in ["Thursday", "Friday", "Saturday"]:
                cursor.execute(
                    "INSERT INTO teacher_availability (teacher_id, day, slot_number) VALUES (%s, %s, %s)",
                    (teacher_id, day, int(slot))
                )

        conn.commit()

    cursor.execute(
        "SELECT day, slot_number FROM teacher_availability WHERE teacher_id = %s",
        (teacher_id,)
    )
    old_availability = cursor.fetchall()

    selected_slots = []
    for row in old_availability:
        selected_slots.append(f"{row[0]}-{row[1]}")

    cursor.close()
    conn.close()

    return render_template(
        "teacher/set_availability.html",
        selected_slots=selected_slots
    )


@teacher_bp.route("/view-availability")
def view_availability():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM teachers WHERE user_id = %s",
        (session["user_id"],)
    )
    teacher = cursor.fetchone()

    if not teacher:
        cursor.close()
        conn.close()
        return "No teacher found"

    teacher_id = teacher["id"]

    cursor.execute(
        "SELECT id, day, slot_number FROM teacher_availability WHERE teacher_id = %s",
        (teacher_id,)
    )
    availability = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("teacher/view_availability.html", availability=availability)


@teacher_bp.route("/delete-availability/<int:availability_id>")
def delete_availability(availability_id):
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM teacher_availability WHERE id = %s",
        (availability_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("teacher.view_availability"))


@teacher_bp.route("/view-selected-courses")
def view_selected_courses():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM teachers WHERE user_id = %s",
        (session["user_id"],)
    )
    teacher = cursor.fetchone()

    if not teacher:
        cursor.close()
        conn.close()
        return "No teacher found"

    teacher_id = teacher["id"]

    query = """
        SELECT courses.id, courses.course_name, courses.semester, courses.credit_hours, courses.course_type
        FROM teacher_course_selection
        JOIN courses ON teacher_course_selection.course_id = courses.id
        WHERE teacher_course_selection.teacher_id = %s
    """
    cursor.execute(query, (teacher_id,))
    selected_courses = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("teacher/view_selected_courses.html", selected_courses=selected_courses)


@teacher_bp.route("/delete-selected-course/<int:course_id>")
def delete_selected_course(course_id):
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM teachers WHERE user_id = %s",
        (session["user_id"],)
    )
    teacher = cursor.fetchone()

    if not teacher:
        cursor.close()
        conn.close()
        return "No teacher found"

    teacher_id = teacher["id"]

    cursor.execute(
        "DELETE FROM teacher_course_selection WHERE teacher_id = %s AND course_id = %s",
        (teacher_id, course_id)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("teacher.view_selected_courses"))


@teacher_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")

        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )

        cursor = conn.cursor()

        cursor.execute(
            "SELECT password FROM users WHERE id = %s",
            (session["user_id"],)
        )
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return "User not found"

        current_password = result[0]

        if old_password != current_password:
            cursor.close()
            conn.close()
            return "Old password is incorrect"

        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (new_password, session["user_id"])
        )
        conn.commit()

        cursor.close()
        conn.close()

        return "Password changed successfully"

    return render_template("teacher/change_password.html")