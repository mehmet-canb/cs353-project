from flask import Flask, render_template

from pms.authorization import login_manager
from pms.config import env_settings
from pms.db import close_db
from pms.routes import auth, calendar, session


def create_app(config_class=env_settings):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.secret_key = config_class.secret_key

    # Initialize Flask extensions
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"

    # Register database functions
    app.teardown_appcontext(close_db)

    # Register blueprints
    from pms.routes import main

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(session.bp)
    app.register_blueprint(calendar.bp)

    # Optional: Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    from pms import db

    db.init_app(app)

    return app
