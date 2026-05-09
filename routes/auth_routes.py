from flask import Blueprint, render_template, request, redirect, session
import mysql.connector
from config import Config

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user:
            error = "Username is incorrect"
        elif user["password"] != password:
            error = "Password is incorrect"
        else:
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin/dashboard")
            elif user["role"] == "hod":
                return redirect("/hod/dashboard")
            else:
                return redirect("/teacher/dashboard")

    return render_template("login.html", error=error)