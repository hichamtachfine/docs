import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY","dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    from .models import User
    with app.app_context():
        from .routes import bp
        app.register_blueprint(bp)
        db.create_all()
        # Ensure at least one admin exists if env var ADMIN_EMAIL is set
        admin_email = os.environ.get("ADMIN_EMAIL")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        if admin_email and not User.query.filter_by(email=admin_email).first():
            User.create_user(name="Admin", email=admin_email, password=admin_password, role="admin")
            print(f"Created admin user: {admin_email} / {admin_password}")

    return app
