from flask import Flask
from app.config import Config
from app.extensions import db, migrate
from sqlalchemy import text
from app import models
from app.routes.organization_routes import organization_bp
from app.routes.user_routes import user_bp
from app.routes.document_routes import document_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(organization_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(document_bp)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/")
    def home():
        return "Document Management System API is running!"

    @app.route("/test-db")
    def test_db():
        try:
            db.session.execute(text("SELECT 1"))
            return "MySQL connection successful!"
        except Exception as e:
            return f"MySQL connection failed: {e}", 500

    return app