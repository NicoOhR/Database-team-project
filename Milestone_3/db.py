"""Database connection helpers for the CS 4347 Milestone 3 application.

This module does one job: create and manage connections/cursors for MySQL.
The rest of the application imports this module instead of opening raw
connections everywhere.

Why this matters:
- it keeps connection logic in one place
- it makes the rest of the code easier to read
- it is easier to update host/user/password/database later
"""

from __future__ import annotations


from contextlib import contextmanager
from typing import Generator, Tuple
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursorDict
import mysql.connector
from getpass import getpass

# These values are fixed for this project.
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_NAME = "project_4347"

# Store the password currently being used by the app.
_db_password = None


def prompt_for_password() -> None:
    """
    Ask the user for a MySQL password and store it.

    This function always asks again, so it is useful when the previous
    password was incorrect and the user needs another attempt.
    """
    global _db_password
    _db_password = getpass("Enter MySQL password: ")


def get_db_password() -> str:
    """
    Return the currently stored password.

    If no password has been entered yet, return an empty string.
    The application should normally call prompt_for_password() first.
    """
    return _db_password if _db_password is not None else ""


def set_db_password(password: str) -> None:
    """Set the database password used by new connections."""
    global _db_password
    _db_password = password


def get_connection():
    """
    Create and return a new connection to the MySQL database.
    """
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=get_db_password(),
        database=DB_NAME
    )


@contextmanager
def get_cursor(dictionary: bool = True) -> Generator[Tuple[MySQLConnection, MySQLCursorDict], None, None]:
    """Yield ``(connection, cursor)`` and close both safely.

    Parameters
    ----------
    dictionary:
        When True, each fetched row acts like a dict, which makes the rest of
        the code more readable than tuple indexing.
    """
    conn: MySQLConnection | None = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=dictionary)
        yield conn, cursor
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def test_connection() -> tuple[bool, str]:
    """Return a success flag and a user-friendly status message."""
    try:
        with get_cursor() as (_conn, cursor):
            cursor.execute("SELECT DATABASE() AS db_name")
            row = cursor.fetchone()
            return True, f"Connected successfully to database: {row['db_name']}"
    except Error as exc:
        return False, f"Connection failed: {exc}"
