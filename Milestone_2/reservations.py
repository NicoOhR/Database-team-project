"""Reservation logic for the Milestone 2 schema.

Important schema note:
The final database follows the textbook structure more closely, so there is no
separate RESERVATION table. Instead, SEAT stores one booked seat per
(Flight_number, Leg_no, Date, Seat_no).

That means:
- making a reservation inserts into SEAT
- canceling a reservation deletes from SEAT
- remaining capacity is tracked in LEG_INSTANCE.No_of_avail_seats
"""

from __future__ import annotations

from mysql.connector import Error

from db import get_cursor
from queries import flight_exists, leg_exists, leg_instance_exists, seat_is_booked


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
    4. No_of_avail_seats must be greater than zero
    5. the requested seat number must not already be booked for that leg instance

    Educational note:
    Because the schema no longer includes airplane seat inventory,
    this function only validates duplicate seat booking for the same leg instance.
    It does not validate whether a seat number belongs to a specific airplane layout.
    """
    if not customer_name.strip():
        return False, "Customer name cannot be empty."
    if not cphone.strip():
        return False, "Phone number cannot be empty."
    if not seat_no.strip():
        return False, "Seat number cannot be empty."

    try:
        if not flight_exists(flight_number):
            return False, f"Flight number {flight_number} does not exist."
        if not leg_exists(flight_number, leg_no):
            return False, f"Leg number {leg_no} does not exist for flight {flight_number}."
        if not leg_instance_exists(flight_number, leg_no, date_str):
            return False, f"No leg instance found for flight {flight_number}, leg {leg_no}, date {date_str}."
        if seat_is_booked(flight_number, leg_no, date_str, seat_no):
            return False, f"Seat {seat_no} is already booked for that leg instance."

        with get_cursor() as (conn, cursor):
            # Lock the leg instance row before updating available seats.
            cursor.execute(
                """
                SELECT No_of_avail_seats
                FROM LEG_INSTANCE
                WHERE Flight_number = %s AND Leg_no = %s AND Date = %s
                FOR UPDATE
                """,
                (flight_number, leg_no, date_str),
            )
            row = cursor.fetchone()
            if row is None:
                conn.rollback()
                return False, "Leg instance no longer exists."

            remaining = row["No_of_avail_seats"]
            if remaining is None or remaining <= 0:
                conn.rollback()
                return False, "No seats are currently available for this leg instance."

            cursor.execute(
                """
                INSERT INTO SEAT (Flight_number, Leg_no, Date, Seat_no, Customer_name, Cphone)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (flight_number, leg_no, date_str, seat_no, customer_name.strip(), cphone.strip()),
            )

            cursor.execute(
                """
                UPDATE LEG_INSTANCE
                SET No_of_avail_seats = No_of_avail_seats - 1
                WHERE Flight_number = %s AND Leg_no = %s AND Date = %s
                """,
                (flight_number, leg_no, date_str),
            )
            conn.commit()

        return True, (
            f"Reservation created successfully for {customer_name.strip()} "
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
    if not seat_no.strip():
        return False, "Seat number cannot be empty."

    try:
        if not flight_exists(flight_number):
            return False, f"Flight number {flight_number} does not exist."
        if not leg_exists(flight_number, leg_no):
            return False, f"Leg number {leg_no} does not exist for flight {flight_number}."
        if not leg_instance_exists(flight_number, leg_no, date_str):
            return False, f"No leg instance found for flight {flight_number}, leg {leg_no}, date {date_str}."
        if not seat_is_booked(flight_number, leg_no, date_str, seat_no):
            return False, f"Seat {seat_no} is not currently booked for that leg instance."

        with get_cursor() as (conn, cursor):
            cursor.execute(
                """
                DELETE FROM SEAT
                WHERE Flight_number = %s AND Leg_no = %s AND Date = %s AND Seat_no = %s
                """,
                (flight_number, leg_no, date_str, seat_no),
            )

            cursor.execute(
                """
                UPDATE LEG_INSTANCE
                SET No_of_avail_seats = No_of_avail_seats + 1
                WHERE Flight_number = %s AND Leg_no = %s AND Date = %s
                """,
                (flight_number, leg_no, date_str),
            )
            conn.commit()

        return True, (
            f"Reservation for seat {seat_no} on flight {flight_number}, leg {leg_no}, "
            f"date {date_str} was canceled successfully."
        )
    except Error as exc:
        return False, f"Error canceling reservation: {exc}"
