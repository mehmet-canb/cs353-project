import psycopg2
import psycopg2.extras
from flask import Flask, g, render_template
from flask_login import LoginManager

from pms.config import env_settings

# Initialize extensions
login_manager = LoginManager()


@login_manager.request_loader
def request_loader(request):
    return None  # TODO: Implement request loader
    # user_id = request.args.get("user_id")
    # return User.get(user_id)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID"""
    return None  # TODO: Implement user loader
    # return User.get(user_id)


def get_db():
    """Get database connection"""
    if "db" not in g:
        g.db = psycopg2.connect(
            dbname=env_settings.db_name,
            user=env_settings.postgres_user,
            password=env_settings.postgres_password,
            host=env_settings.db_host,
            port=env_settings.db_port,
        )
    return g.db


def get_cursor():
    """Get database cursor with dictionary support"""
    if "cursor" not in g:
        g.cursor = get_db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return g.cursor


def close_db(e=None):
    """Close database connection"""
    cursor = g.pop("cursor", None)
    if cursor is not None:
        cursor.close()

    db = g.pop("db", None)
    if db is not None:
        db.close()


def create_app(config_class=env_settings):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Register database functions
    app.teardown_appcontext(close_db)

    # Register blueprints
    from pms.routes import main

    app.register_blueprint(main.bp)

    # Optional: Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    from pms import db

    db.init_app(app)

    return app
