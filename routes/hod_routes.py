from flask import Blueprint, render_template, request, session, redirect, url_for
import mysql.connector
from config import Config

hod_bp = Blueprint("hod", __name__)


@hod_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    return render_template("hod/hod_dashboard.html")


@hod_bp.route("/add-course", methods=["GET", "POST"])
def add_course():
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        course_name = request.form.get("course_name")
        semester = request.form.get("semester")
        credit_hours = request.form.get("credit_hours")
        course_type = request.form.get("course_type")

        try:
            conn = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB
            )

            cursor = conn.cursor()

            query = """
                INSERT INTO courses (course_name, semester, credit_hours, course_type)
                VALUES (%s, %s, %s, %s)
            """
            values = (course_name, semester, credit_hours, course_type)

            cursor.execute(query, values)
            conn.commit()

            cursor.close()
            conn.close()

            return "Course saved in database successfully"

        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("hod/add_course.html")


@hod_bp.route("/add-teacher", methods=["GET", "POST"])
def add_teacher():
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        autocommit=False
    )

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT department_id FROM users WHERE id = %s",
            (session["user_id"],)
        )
        hod_user = cursor.fetchone()

        if not hod_user:
            return "HOD not found"

        department_id = hod_user["department_id"]

        cursor.execute(
            "SELECT name FROM departments WHERE id = %s",
            (department_id,)
        )
        dept = cursor.fetchone()

        if not dept:
            return "Department not found"

        department_name = dept["name"]

        if request.method == "POST":
            name = request.form.get("name")
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")

            cursor.execute(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (username, email)
            )
            existing_user = cursor.fetchone()

            if existing_user:
                return "Username or email already exists"

            cursor.execute(
                """
                INSERT INTO users (name, username, email, password, role, department_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (name, username, email, password, "teacher", department_id)
            )

            user_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO teachers (user_id, designation, department_name)
                VALUES (%s, %s, %s)
                """,
                (user_id, "Teacher", department_name)
            )

            conn.commit()
            return "Teacher saved successfully"

        return render_template("hod/add_teacher.html")

    except Exception as e:
        conn.rollback()
        return f"Error: {str(e)}"

    finally:
        cursor.close()
        conn.close()


@hod_bp.route("/view-courses")
def view_courses():
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("hod/view_courses.html", courses=courses)


@hod_bp.route("/delete-course/<int:course_id>")
def delete_course(course_id):
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return "Course deleted successfully"


@hod_bp.route("/view-teachers")
def view_teachers():
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT department_id FROM users WHERE id = %s",
        (session["user_id"],)
    )
    hod_user = cursor.fetchone()

    if not hod_user:
        cursor.close()
        conn.close()
        return "HOD not found"

    department_id = hod_user["department_id"]

    query = """
        SELECT teachers.id, users.name, users.username, users.email, teachers.designation, teachers.department_name
        FROM teachers
        JOIN users ON teachers.user_id = users.id
        WHERE users.department_id = %s
    """
    cursor.execute(query, (department_id,))
    teachers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("hod/view_teachers.html", teachers=teachers)


@hod_bp.route("/delete-teacher/<int:teacher_id>")
def delete_teacher(teacher_id):
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM teachers WHERE id = %s", (teacher_id,))
    result = cursor.fetchone()

    if result:
        user_id = result[0]

        cursor.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
        conn.commit()

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

    cursor.close()
    conn.close()

    return "Teacher deleted successfully"


@hod_bp.route("/generate-timetable", methods=["GET", "POST"])
def generate_timetable():
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor(dictionary=True, buffered=True)

        try:
            # Remove old timetable completely
            cursor.execute("DELETE FROM timetable")

            # Get all selected courses with teacher info
            cursor.execute("""
                SELECT
                    teacher_course_selection.id AS selection_id,
                    teacher_course_selection.course_id,
                    teacher_course_selection.teacher_id,
                    courses.course_name,
                    courses.semester,
                    courses.course_type
                FROM teacher_course_selection
                JOIN courses ON teacher_course_selection.course_id = courses.id
                ORDER BY
                    FIELD(courses.semester, '2nd', '4th', '6th', '8th'),
                    teacher_course_selection.id
            """)
            selections = cursor.fetchall()

            if not selections:
                return "No teacher course selections found"

            # Get all rooms
            cursor.execute("SELECT id, room_type FROM rooms ORDER BY id")
            rooms = cursor.fetchall()

            if not rooms:
                return "No rooms found"

            # Fixed 3-day blocks
            block_days = {
                "monday": ["Monday", "Tuesday", "Wednesday"],
                "thursday": ["Thursday", "Friday", "Saturday"]
            }

            # Group selected courses by semester
            semester_courses = {}
            for row in selections:
                semester = row["semester"]
                if semester not in semester_courses:
                    semester_courses[semester] = []
                semester_courses[semester].append(row)

            # Generate semester-wise, but respect teacher selected slots
            for semester, courses_list in semester_courses.items():
                for item in courses_list:
                    teacher_id = item["teacher_id"]
                    course_id = item["course_id"]
                    course_type = item["course_type"]

                    if course_type == "lab":
                        valid_rooms = [r for r in rooms if r["room_type"] == "lab"]
                    else:
                        valid_rooms = [r for r in rooms if r["room_type"] == "classroom"]

                    if not valid_rooms:
                        continue

                    # Read only the anchor-day selected slots:
                    # Monday means Mon/Tue/Wed block
                    # Thursday means Thu/Fri/Sat block
                    cursor.execute("""
                        SELECT day, slot_number
                        FROM teacher_availability
                        WHERE teacher_id = %s
                          AND day IN ('Monday', 'Thursday')
                        ORDER BY FIELD(day, 'Monday', 'Thursday'), slot_number
                    """, (teacher_id,))
                    anchor_slots = cursor.fetchall()

                    monday_slots = []
                    thursday_slots = []

                    for row in anchor_slots:
                        if row["day"] == "Monday":
                            monday_slots.append(row["slot_number"])
                        elif row["day"] == "Thursday":
                            thursday_slots.append(row["slot_number"])

                    # Remove duplicates and keep order
                    monday_slots = sorted(list(set(monday_slots)))
                    thursday_slots = sorted(list(set(thursday_slots)))

                    placed = False

                    # Try Monday block first, but only on selected slots
                    for slot_number in monday_slots:
                        days = block_days["monday"]

                        # Check if this semester already uses this slot in this block
                        cursor.execute("""
                            SELECT id
                            FROM timetable
                            WHERE semester = %s
                              AND slot_number = %s
                              AND day IN ('Monday', 'Tuesday', 'Wednesday')
                        """, (semester, slot_number))
                        if cursor.fetchone():
                            continue

                        # Find one room free for all 3 block days
                        chosen_room_id = None
                        for room in valid_rooms:
                            cursor.execute("""
                                SELECT id
                                FROM timetable
                                WHERE room_id = %s
                                  AND slot_number = %s
                                  AND day IN ('Monday', 'Tuesday', 'Wednesday')
                            """, (room["id"], slot_number))
                            if not cursor.fetchone():
                                chosen_room_id = room["id"]
                                break

                        if chosen_room_id is None:
                            continue

                        # Insert all 3 days for the block
                        for day in days:
                            cursor.execute("""
                                INSERT INTO timetable
                                (semester, day, slot_number, course_id, teacher_id, room_id)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                semester,
                                day,
                                slot_number,
                                course_id,
                                teacher_id,
                                chosen_room_id
                            ))

                        placed = True
                        break

                    if placed:
                        continue

                    # If not placed, try Thursday block on selected slots
                    for slot_number in thursday_slots:
                        days = block_days["thursday"]

                        # Check if this semester already uses this slot in this block
                        cursor.execute("""
                            SELECT id
                            FROM timetable
                            WHERE semester = %s
                              AND slot_number = %s
                              AND day IN ('Thursday', 'Friday', 'Saturday')
                        """, (semester, slot_number))
                        if cursor.fetchone():
                            continue

                        # Find one room free for all 3 block days
                        chosen_room_id = None
                        for room in valid_rooms:
                            cursor.execute("""
                                SELECT id
                                FROM timetable
                                WHERE room_id = %s
                                  AND slot_number = %s
                                  AND day IN ('Thursday', 'Friday', 'Saturday')
                            """, (room["id"], slot_number))
                            if not cursor.fetchone():
                                chosen_room_id = room["id"]
                                break

                        if chosen_room_id is None:
                            continue

                        # Insert all 3 days for the block
                        for day in days:
                            cursor.execute("""
                                INSERT INTO timetable
                                (semester, day, slot_number, course_id, teacher_id, room_id)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                semester,
                                day,
                                slot_number,
                                course_id,
                                teacher_id,
                                chosen_room_id
                            ))

                        placed = True
                        break

            conn.commit()
            return "Timetable generated successfully"

        except Exception as e:
            conn.rollback()
            return f"Error: {str(e)}"

        finally:
            cursor.close()
            conn.close()

    return render_template("hod/generate_timetable.html")


@hod_bp.route("/view-teacher-selections")
def view_teacher_selections():
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        teacher_course_selection.id AS selection_id,
        users.name AS teacher_name,
        courses.course_name,
        courses.semester
    FROM teacher_course_selection
    JOIN teachers ON teacher_course_selection.teacher_id = teachers.id
    JOIN users ON teachers.user_id = users.id
    JOIN courses ON teacher_course_selection.course_id = courses.id
"""
    cursor.execute(query)
    data = cursor.fetchall()

    course_count = {}
    for item in data:
        key = (item["course_name"], item["semester"])
        course_count[key] = course_count.get(key, 0) + 1

    for item in data:
        key = (item["course_name"], item["semester"])
        item["is_conflict"] = course_count[key] > 1

    cursor.close()
    conn.close()

    return render_template("hod/view_teacher_selections.html", data=data)

@hod_bp.route("/delete-teacher-selection/<int:selection_id>")
def delete_teacher_selection(selection_id):
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM teacher_course_selection WHERE id = %s",
        (selection_id,)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("hod.view_teacher_selections"))

@hod_bp.route("/reset-password/<int:teacher_id>")
def reset_password(teacher_id):
    if "user_id" not in session or session.get("role") != "hod":
        return redirect(url_for("auth.login"))

    import random
    import string

    new_password = "temp" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM teachers WHERE id = %s", (teacher_id,))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        conn.close()
        return "Teacher not found"

    user_id = result[0]

    cursor.execute(
        "UPDATE users SET password = %s WHERE id = %s",
        (new_password, user_id)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return render_template("hod/reset_result.html", password=new_password)