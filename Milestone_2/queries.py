"""Read-only query helpers for the Airport Management console app.

These functions do not modify the database. They only retrieve information and
return it in a Python-friendly form.

Note:
The final SQL schema follows the textbook version of Figure 3.21.
That means:
- there is no separate RESERVATION table
- AIRPLANE_SEAT stores the valid seat layout for each airplane
- SEAT stores booked seat assignments for a specific leg instance
- the app can show booked seats and remaining seats without exposing the full
  seat map in the console
"""

from __future__ import annotations

from typing import Any

from mysql.connector import Error

from db import get_cursor


def _fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with get_cursor() as (_conn, cursor):
        cursor.execute(query, params)
        return cursor.fetchall() or []


def _fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with get_cursor() as (_conn, cursor):
        cursor.execute(query, params)
        return cursor.fetchone()


def flight_exists(flight_number: str) -> bool:
    """Return True if the flight number exists in FLIGHT."""
    row = _fetch_one("SELECT 1 AS found FROM FLIGHT WHERE Number = %s", (flight_number,))
    return row is not None


def leg_exists(flight_number: str, leg_no: int) -> bool:
    """Return True if the given leg exists for the flight."""
    row = _fetch_one(
        "SELECT 1 AS found FROM FLIGHT_LEG WHERE Flight_number = %s AND Leg_no = %s",
        (flight_number, leg_no),
    )
    return row is not None


def leg_instance_exists(flight_number: str, leg_no: int, date_str: str) -> bool:
    """Return True if a specific leg instance exists."""
    row = _fetch_one(
        """
        SELECT 1 AS found
        FROM LEG_INSTANCE
        WHERE Flight_number = %s AND Leg_no = %s AND Date = %s
        """,
        (flight_number, leg_no, date_str),
    )
    return row is not None


def get_flights(limit: int = 10) -> list[dict[str, Any]]:
    """Return the first N flights sorted by flight number."""
    return _fetch_all(
        """
        SELECT Number, Airline, Weekdays
        FROM FLIGHT
        ORDER BY Number
        LIMIT %s
        """,
        (limit,),
    )


def get_flight_legs(flight_number: str) -> list[dict[str, Any]]:
    """Return every leg for a given flight number."""
    return _fetch_all(
        """
        SELECT
            Flight_number,
            Leg_no,
            Dep_airport_code,
            Arr_airport_code,
            Scheduled_dep_time,
            Scheduled_arr_time
        FROM FLIGHT_LEG
        WHERE Flight_number = %s
        ORDER BY Leg_no
        """,
        (flight_number,),
    )


def get_fares(flight_number: str) -> list[dict[str, Any]]:
    """Return all fare options for a flight."""
    return _fetch_all(
        """
        SELECT Flight_number, Code, Amount, Restrictions
        FROM FARE
        WHERE Flight_number = %s
        ORDER BY Amount
        """,
        (flight_number,),
    )


def get_leg_instances(flight_number: str, leg_no: int | None = None) -> list[dict[str, Any]]:
    """Return leg instances for a flight, optionally filtered to one leg."""
    if leg_no is None:
        return _fetch_all(
            """
            SELECT Flight_number, Leg_no, Date, No_of_avail_seats, Airplane_id, Dep_time, Arr_time
            FROM LEG_INSTANCE
            WHERE Flight_number = %s
            ORDER BY Leg_no, Date
            """,
            (flight_number,),
        )

    return _fetch_all(
        """
        SELECT Flight_number, Leg_no, Date, No_of_avail_seats, Airplane_id, Dep_time, Arr_time
        FROM LEG_INSTANCE
        WHERE Flight_number = %s AND Leg_no = %s
        ORDER BY Date
        """,
        (flight_number, leg_no),
    )


def get_leg_instance_detail(flight_number: str, leg_no: int, date_str: str) -> dict[str, Any] | None:
    """Return one specific leg instance row."""
    return _fetch_one(
        """
        SELECT Flight_number, Leg_no, Date, No_of_avail_seats, Airplane_id, Dep_time, Arr_time
        FROM LEG_INSTANCE
        WHERE Flight_number = %s AND Leg_no = %s AND Date = %s
        """,
        (flight_number, leg_no, date_str),
    )


def get_booked_seats(flight_number: str, leg_no: int, date_str: str) -> list[dict[str, Any]]:
    """Return booked seats for a specific leg instance.

    In the schema, AIRPLANE_SEAT stores valid seat numbers and SEAT stores
    actual bookings.
    """
    return _fetch_all(
        """
        SELECT Seat_no, Customer_name, Cphone
        FROM SEAT
        WHERE Flight_number = %s AND Leg_no = %s AND Date = %s
        ORDER BY Seat_no
        """,
        (flight_number, leg_no, date_str),
    )


def seat_is_booked(flight_number: str, leg_no: int, date_str: str, seat_no: str) -> bool:
    """Return True if the given seat is already booked for that leg instance."""
    row = _fetch_one(
        """
        SELECT 1 AS found
        FROM SEAT
        WHERE Flight_number = %s AND Leg_no = %s AND Date = %s AND Seat_no = %s
        """,
        (flight_number, leg_no, date_str, seat_no),
    )
    return row is not None


def show_available_seats_summary(flight_number: str, leg_no: int, date_str: str) -> dict[str, Any]:
    """Return a summary for the requested leg instance.

    AIRPLANE_SEAT stores the valid seat layout for the assigned airplane.
    This function reports:
    - the LEG_INSTANCE row
    - how many seats are still available (from No_of_avail_seats)
    - which seat numbers are already booked in SEAT
    """
    detail = get_leg_instance_detail(flight_number, leg_no, date_str)
    if detail is None:
        raise ValueError("Leg instance not found.")

    booked = get_booked_seats(flight_number, leg_no, date_str)
    return {
        "leg_instance": detail,
        "booked_seats": booked,
        "booked_count": len(booked),
        "available_count": detail["No_of_avail_seats"],
    }


def safe_get_flights(limit: int = 10) -> tuple[bool, list[dict[str, Any]] | str]:
    try:
        return True, get_flights(limit)
    except Error as exc:
        return False, f"Error fetching flights: {exc}"


def safe_get_flight_legs(flight_number: str) -> tuple[bool, list[dict[str, Any]] | str]:
    try:
        if not flight_exists(flight_number):
            return False, f"Flight number {flight_number} does not exist."
        return True, get_flight_legs(flight_number)
    except Error as exc:
        return False, f"Error fetching flight legs: {exc}"


def safe_get_fares(flight_number: str) -> tuple[bool, list[dict[str, Any]] | str]:
    try:
        if not flight_exists(flight_number):
            return False, f"Flight number {flight_number} does not exist."
        return True, get_fares(flight_number)
    except Error as exc:
        return False, f"Error fetching fares: {exc}"


def safe_get_leg_instances(flight_number: str, leg_no: int | None = None) -> tuple[bool, list[dict[str, Any]] | str]:
    try:
        if not flight_exists(flight_number):
            return False, f"Flight number {flight_number} does not exist."
        if leg_no is not None and not leg_exists(flight_number, leg_no):
            return False, f"Leg number {leg_no} does not exist for flight {flight_number}."
        return True, get_leg_instances(flight_number, leg_no)
    except Error as exc:
        return False, f"Error fetching leg instances: {exc}"


def safe_show_available_seats_summary(
    flight_number: str, leg_no: int, date_str: str
) -> tuple[bool, dict[str, Any] | str]:
    try:
        if not flight_exists(flight_number):
            return False, f"Flight number {flight_number} does not exist."
        if not leg_exists(flight_number, leg_no):
            return False, f"Leg number {leg_no} does not exist for flight {flight_number}."
        if not leg_instance_exists(flight_number, leg_no, date_str):
            return False, f"No leg instance found for flight {flight_number}, leg {leg_no}, date {date_str}."
        return True, show_available_seats_summary(flight_number, leg_no, date_str)
    except (Error, ValueError) as exc:
        return False, f"Error showing available seats: {exc}"
