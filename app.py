from flask import Flask, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return None

    from routes.auth_routes import auth_bp
    from routes.hod_routes import hod_bp
    from routes.teacher_routes import teacher_bp
    from routes.timetable_routes import timetable_bp
    from routes.admin_routes import admin_bp   # ✅ added

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")   # ✅ added
    app.register_blueprint(hod_bp, url_prefix="/hod")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(timetable_bp, url_prefix="/timetable")

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)