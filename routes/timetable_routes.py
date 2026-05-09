from flask import Blueprint, render_template
import mysql.connector
from config import Config

timetable_bp = Blueprint("timetable", __name__)


@timetable_bp.route("/view")
def view_timetable():
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT timetable.semester, timetable.day, timetable.slot_number,
               courses.course_name,
               users.name AS teacher_name
        FROM timetable
        JOIN courses ON timetable.course_id = courses.id
        JOIN teachers ON timetable.teacher_id = teachers.id
        JOIN users ON teachers.user_id = users.id
        ORDER BY timetable.semester,
                 FIELD(timetable.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'),
                 timetable.slot_number
    """
    cursor.execute(query)
    raw_data = cursor.fetchall()

    cursor.close()
    conn.close()

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    semesters = sorted(list(set(item["semester"] for item in raw_data)))

    timetable_data = {}

    for semester in semesters:
        timetable_data[semester] = {}

        # initialize empty cells
        for day in day_order:
            timetable_data[semester][day] = {}
            for slot in [1, 2, 3, 4]:
                timetable_data[semester][day][slot] = ""

        # first, place actual data
        for item in raw_data:
            if item["semester"] != semester:
                continue

            timetable_data[semester][item["day"]][item["slot_number"]] = {
                "course_name": item["course_name"],
                "teacher_name": item["teacher_name"]
            }

        # now force Do logic based only on Monday and Thursday
        for slot in [1, 2, 3, 4]:
            monday_item = timetable_data[semester]["Monday"][slot]
            if monday_item:
                timetable_data[semester]["Tuesday"][slot] = "Do"
                timetable_data[semester]["Wednesday"][slot] = "Do"

            thursday_item = timetable_data[semester]["Thursday"][slot]
            if thursday_item:
                timetable_data[semester]["Friday"][slot] = "Do"
                timetable_data[semester]["Saturday"][slot] = "Do"

    return render_template(
        "hod/view_timetable.html",
        timetable_data=timetable_data,
        day_order=day_order
    )