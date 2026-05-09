from flask import Blueprint, render_template, session, redirect, url_for, request
import mysql.connector
from config import Config

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    return render_template("admin/admin_dashboard.html")


@admin_bp.route("/add-department", methods=["GET", "POST"])
def add_department():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        name = request.form.get("name")

        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )

        cursor = conn.cursor()
        cursor.execute("INSERT INTO departments (name) VALUES (%s)", (name,))
        conn.commit()

        cursor.close()
        conn.close()

        return "Department added successfully"

    return render_template("admin/add_department.html")


@admin_bp.route("/view-departments")
def view_departments():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin/view_departments.html", departments=departments)


@admin_bp.route("/add-hod", methods=["GET", "POST"])
def add_hod():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        department_id = request.form.get("department_id")

        cursor.execute(
            "INSERT INTO users (name, username, email, password, role, department_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, username, email, password, "hod", department_id)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return "HOD added successfully"

    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin/add_hod.html", departments=departments)


@admin_bp.route("/view-hods")
def view_hods():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT users.id, users.name, users.username, users.email, departments.name AS department
        FROM users
        LEFT JOIN departments ON users.department_id = departments.id
        WHERE users.role = 'hod'
    """
    cursor.execute(query)
    hods = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin/view_hods.html", hods=hods)

@admin_bp.route("/delete-department/<int:department_id>")
def delete_department(department_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor()
    cursor.execute("DELETE FROM departments WHERE id = %s", (department_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("admin.view_departments"))

@admin_bp.route("/delete-hod/<int:hod_id>")
def delete_hod(hod_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s AND role = 'hod'", (hod_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("admin.view_hods"))