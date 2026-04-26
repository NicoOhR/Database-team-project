"""Read-only query helpers for the Airport Management console app.

These functions do not modify the database. They only retrieve information and
return it in a Python-friendly form.

Design note:
- the core schema follows Figure 3.21 from the textbook
- AIRPLANE_SEAT is an auxiliary support table used to validate seat numbers
- SEAT stores one booked seat assignment for one leg instance, including the
  reservation details needed by the Milestone 2 host application
"""

from __future__ import annotations

import re
from typing import Any

from mysql.connector import Error

from db import get_cursor

SEAT_NO_PATTERN = re.compile(r"^(\d+)([A-Za-z]+)$")


def _fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with get_cursor() as (_conn, cursor):
        cursor.execute(query, params)
        return cursor.fetchall() or []


def _fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with get_cursor() as (_conn, cursor):
        cursor.execute(query, params)
        return cursor.fetchone()


def _parse_seat_no(seat_no: str) -> tuple[int | None, str]:
    """Split a seat like 12C into its row number and letter portion."""
    match = SEAT_NO_PATTERN.fullmatch(seat_no)
    if match is None:
        return None, seat_no
    return int(match.group(1)), match.group(2).upper()


def _seat_sort_key(seat_no: str) -> tuple[int, str]:
    row_no, letters = _parse_seat_no(seat_no)
    if row_no is None:
        return 10**9, seat_no
    return row_no, letters


def _get_available_seat_numbers(airplane_id: str, booked_seat_numbers: set[str]) -> list[str]:
    seats = _fetch_all(
        """
        SELECT Seat_no
        FROM AIRPLANE_SEAT
        WHERE Airplane_id = %s
        """,
        (airplane_id,),
    )
    available = [row["Seat_no"] for row in seats if row["Seat_no"] not in booked_seat_numbers]
    available.sort(key=_seat_sort_key)
    return available


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
    - how many seats are still available (total airplane seats minus booked seats)
    - a compact summary of which seats are still available
    - which seat numbers are already booked in SEAT
    """
    detail = get_leg_instance_detail(flight_number, leg_no, date_str)
    if detail is None:
        raise ValueError("Leg instance not found.")

    booked = get_booked_seats(flight_number, leg_no, date_str)
    booked_seat_numbers = sorted((row["Seat_no"] for row in booked), key=_seat_sort_key)
    available_seat_numbers = _get_available_seat_numbers(
        detail["Airplane_id"],
        set(booked_seat_numbers),
    )
    total_seat_count = len(available_seat_numbers) + len(booked_seat_numbers)

    available_rows: list[int] = []
    available_letters: set[str] = set()
    for seat_no in available_seat_numbers:
        row_no, letters = _parse_seat_no(seat_no)
        if row_no is not None:
            available_rows.append(row_no)
            available_letters.add(letters)

    return {
        "leg_instance": detail,
        "booked_seats": booked,
        "booked_count": len(booked),
        "booked_seat_numbers": booked_seat_numbers,
        "available_count": len(available_seat_numbers),
        "stored_available_count": detail["No_of_avail_seats"],
        "total_seat_count": total_seat_count,
        "available_row_min": min(available_rows) if available_rows else None,
        "available_row_max": max(available_rows) if available_rows else None,
        "available_letters": sorted(available_letters),
        "available_sample_seats": available_seat_numbers[:5],
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
