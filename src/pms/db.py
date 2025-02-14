import click
import psycopg2
import psycopg2.extras
from flask import g
from flask.cli import with_appcontext

from pms.config import env_settings


def init_db():
    """Initialize the database with schema"""
    return
    conn = psycopg2.connect(
        dbname=env_settings.db_name,
        user=env_settings.postgres_user,
        password=env_settings.postgres_password,
        host=env_settings.db_host,
        port=env_settings.db_port,
    )

    cur = conn.cursor()

    # TODO: Implement init_db

    conn.commit()
    cur.close()
    conn.close()


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


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    """Register database functions with the Flask app"""
    app.cli.add_command(init_db_command)
