"""Reservation logic for the Milestone 2 schema.

Important schema note:
The final database follows the textbook structure more closely, so there is no
separate RESERVATION table. Instead:
- AIRPLANE_SEAT stores the valid seat layout for each airplane
- SEAT stores one booked seat per (Flight_number, Leg_no, Date, Seat_no)

That means:
- making a reservation inserts into SEAT
- canceling a reservation deletes from SEAT
- remaining capacity is tracked in LEG_INSTANCE.No_of_avail_seats
"""

from __future__ import annotations

import re

from mysql.connector import Error

from db import get_cursor
from queries import flight_exists, leg_exists

CUSTOMER_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'-]*[A-Za-z]$")


def _get_locked_leg_instance(cursor, flight_number: str, leg_no: int, date_str: str):
    """Return the leg instance row and lock it for the current transaction."""
    cursor.execute(
        """
        SELECT No_of_avail_seats, Airplane_id
        FROM LEG_INSTANCE
        WHERE Flight_number = %s AND Leg_no = %s AND Date = %s
        FOR UPDATE
        """,
        (flight_number, leg_no, date_str),
    )
    return cursor.fetchone()


def _seat_exists_on_airplane(cursor, airplane_id: str, seat_no: str) -> bool:
    """Return True if the seat number exists on the assigned airplane."""
    cursor.execute(
        """
        SELECT 1 AS found
        FROM AIRPLANE_SEAT
        WHERE Airplane_id = %s AND Seat_no = %s
        """,
        (airplane_id, seat_no),
    )
    return cursor.fetchone() is not None


def _sync_available_seat_count(
    cursor,
    flight_number: str,
    leg_no: int,
    date_str: str,
    airplane_id: str,
) -> int:
    """Recalculate remaining seats from layout seats minus booked seats."""
    cursor.execute(
        """
        SELECT COUNT(*) AS total_seats
        FROM AIRPLANE_SEAT
        WHERE Airplane_id = %s
        """,
        (airplane_id,),
    )
    total_seats = cursor.fetchone()["total_seats"]

    cursor.execute(
        """
        SELECT COUNT(*) AS booked_count
        FROM SEAT
        WHERE Flight_number = %s AND Leg_no = %s AND Date = %s
        """,
        (flight_number, leg_no, date_str),
    )
    booked_count = cursor.fetchone()["booked_count"]
    remaining = total_seats - booked_count

    cursor.execute(
        """
        UPDATE LEG_INSTANCE
        SET No_of_avail_seats = %s
        WHERE Flight_number = %s AND Leg_no = %s AND Date = %s
        """,
        (remaining, flight_number, leg_no, date_str),
    )
    return remaining


def _phone_is_valid(cphone: str) -> bool:
    """Return True when the phone number is exactly 10 digits."""
    return cphone.isdigit() and len(cphone) == 10


def validate_customer_phone(cphone: str) -> tuple[bool, str]:
    """Validate and normalize the customer phone number."""
    cphone = cphone.strip()
    if not cphone:
        return False, "Phone number cannot be empty."
    if not _phone_is_valid(cphone):
        return False, "Phone number must be exactly 10 digits."
    return True, cphone


def validate_customer_name(customer_name: str) -> tuple[bool, str]:
    """Validate and normalize the customer name."""
    customer_name = customer_name.strip()
    if not customer_name:
        return False, "Customer name cannot be empty."
    if len(customer_name) > 60:
        return False, "Customer name must be 60 characters or fewer."
    if any(char.isdigit() for char in customer_name):
        return False, "Customer name cannot contain numbers."
    if not CUSTOMER_NAME_PATTERN.fullmatch(customer_name):
        return False, "Customer name can only contain letters, spaces, periods, apostrophes, and hyphens."
    return True, customer_name


def validate_seat_for_reservation(
    flight_number: str,
    leg_no: int,
    date_str: str,
    seat_no: str,
) -> tuple[bool, str]:
    """Validate and normalize a seat number before reservation details continue."""
    seat_no = seat_no.strip().upper()
    if not seat_no:
        return False, "Seat number cannot be empty."

    try:
        with get_cursor() as (_conn, cursor):
            cursor.execute(
                """
                SELECT Airplane_id
                FROM LEG_INSTANCE
                WHERE Flight_number = %s AND Leg_no = %s AND Date = %s
                """,
                (flight_number, leg_no, date_str),
            )
            leg_instance = cursor.fetchone()
            if leg_instance is None:
                return False, (
                    f"No leg instance found for flight {flight_number}, "
                    f"leg {leg_no}, date {date_str}."
                )

            if not _seat_exists_on_airplane(cursor, leg_instance["Airplane_id"], seat_no):
                return False, (
                    f"Seat {seat_no} does not exist on airplane "
                    f"{leg_instance['Airplane_id']} for that leg instance."
                )

            cursor.execute(
                """
                SELECT 1 AS found
                FROM SEAT
                WHERE Flight_number = %s AND Leg_no = %s AND Date = %s AND Seat_no = %s
                """,
                (flight_number, leg_no, date_str, seat_no),
            )
            if cursor.fetchone() is not None:
                return False, f"Seat {seat_no} is already booked for that leg instance."
    except Error as exc:
        return False, f"Error validating seat number: {exc}"

    return True, seat_no


def make_reservation(
    flight_number: str,
    leg_no: int,
    date_str: str,
    seat_no: str,
    customer_name: str,
    cphone: str,
) -> tuple[bool, str]:
    """Create a reservation by inserting a row into SEAT.

    Validation performed:
    1. flight must exist
    2. leg must exist for the flight
    3. leg instance must exist for that date
    4. customer phone must be exactly 10 digits
    5. seat number must exist on the airplane assigned to that leg instance
    6. No_of_avail_seats must be greater than zero
    7. the requested seat number must not already be booked for that leg instance
    """
    seat_no = seat_no.strip().upper()
    customer_name = customer_name.strip()
    cphone = cphone.strip()

    name_ok, name_result = validate_customer_name(customer_name)
    if not name_ok:
        return False, name_result
    customer_name = name_result
    phone_ok, phone_result = validate_customer_phone(cphone)
    if not phone_ok:
        return False, phone_result
    cphone = phone_result
    if not seat_no:
        return False, "Seat number cannot be empty."

    try:
        if not flight_exists(flight_number):
            return False, f"Flight number {flight_number} does not exist."
        if not leg_exists(flight_number, leg_no):
            return False, f"Leg number {leg_no} does not exist for flight {flight_number}."

        with get_cursor() as (conn, cursor):
            leg_instance = _get_locked_leg_instance(cursor, flight_number, leg_no, date_str)
            if leg_instance is None:
                conn.rollback()
                return False, (
                    f"No leg instance found for flight {flight_number}, "
                    f"leg {leg_no}, date {date_str}."
                )

            if not _seat_exists_on_airplane(cursor, leg_instance["Airplane_id"], seat_no):
                conn.rollback()
                return False, (
                    f"Seat {seat_no} does not exist on airplane "
                    f"{leg_instance['Airplane_id']} for that leg instance."
                )

            remaining = _sync_available_seat_count(
                cursor,
                flight_number,
                leg_no,
                date_str,
                leg_instance["Airplane_id"],
            )
            if remaining <= 0:
                conn.rollback()
                return False, "No seats are currently available for this leg instance."

            cursor.execute(
                """
                SELECT 1 AS found
                FROM SEAT
                WHERE Flight_number = %s AND Leg_no = %s AND Date = %s AND Seat_no = %s
                """,
                (flight_number, leg_no, date_str, seat_no),
            )
            if cursor.fetchone() is not None:
                conn.rollback()
                return False, f"Seat {seat_no} is already booked for that leg instance."

            cursor.execute(
                """
                INSERT INTO SEAT (Flight_number, Leg_no, Date, Seat_no, Customer_name, Cphone)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (flight_number, leg_no, date_str, seat_no, customer_name, cphone),
            )

            _sync_available_seat_count(
                cursor,
                flight_number,
                leg_no,
                date_str,
                leg_instance["Airplane_id"],
            )
            conn.commit()

        return True, (
            f"Reservation created successfully for {customer_name} "
            f"on flight {flight_number}, leg {leg_no}, date {date_str}, seat {seat_no}."
        )
    except Error as exc:
        return False, f"Error making reservation: {exc}"


def cancel_reservation(
    flight_number: str,
    leg_no: int,
    date_str: str,
    seat_no: str,
) -> tuple[bool, str]:
    """Cancel a reservation by deleting a row from SEAT and restoring one seat."""
    seat_no = seat_no.strip().upper()

    if not seat_no:
        return False, "Seat number cannot be empty."

    try:
        if not flight_exists(flight_number):
            return False, f"Flight number {flight_number} does not exist."
        if not leg_exists(flight_number, leg_no):
            return False, f"Leg number {leg_no} does not exist for flight {flight_number}."

        with get_cursor() as (conn, cursor):
            leg_instance = _get_locked_leg_instance(cursor, flight_number, leg_no, date_str)
            if leg_instance is None:
                conn.rollback()
                return False, (
                    f"No leg instance found for flight {flight_number}, "
                    f"leg {leg_no}, date {date_str}."
                )

            cursor.execute(
                """
                DELETE FROM SEAT
                WHERE Flight_number = %s AND Leg_no = %s AND Date = %s AND Seat_no = %s
                """,
                (flight_number, leg_no, date_str, seat_no),
            )
            if cursor.rowcount != 1:
                conn.rollback()
                return False, f"Seat {seat_no} is not currently booked for that leg instance."

            _sync_available_seat_count(
                cursor,
                flight_number,
                leg_no,
                date_str,
                leg_instance["Airplane_id"],
            )
            conn.commit()

        return True, (
            f"Reservation for seat {seat_no} on flight {flight_number}, leg {leg_no}, "
            f"date {date_str} was canceled successfully."
        )
    except Error as exc:
        return False, f"Error canceling reservation: {exc}"
