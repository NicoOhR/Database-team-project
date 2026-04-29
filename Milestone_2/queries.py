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


def airport_exists(airport_code: str) -> bool:
    """Return True if the airport code exists in AIRPORT."""
    row = _fetch_one("SELECT 1 AS found FROM AIRPORT WHERE Airport_code = %s", (airport_code,))
    return row is not None


def _normalize_airport_search_text(value: str) -> str:
    """Normalize city names enough to match hyphen/dash variants."""
    value = value.strip().lower()
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"\s+", " ", value)
    return value


def resolve_airport_search(value: str) -> list[dict[str, Any]]:
    """Resolve a three-letter airport code or city name to airport rows."""
    search_value = value.strip()
    if not search_value:
        return []

    code = search_value.upper()
    if len(code) == 3:
        rows = _fetch_all(
            """
            SELECT Airport_code, Name, City, State
            FROM AIRPORT
            WHERE Airport_code = %s
            """,
            (code,),
        )
        if rows:
            return rows

    normalized_search = _normalize_airport_search_text(search_value)
    airports = _fetch_all(
        """
        SELECT Airport_code, Name, City, State
        FROM AIRPORT
        ORDER BY Airport_code
        """
    )

    matches = []
    for airport in airports:
        normalized_city = _normalize_airport_search_text(airport["City"])
        city_parts = [part.strip() for part in normalized_city.split("-")]
        if normalized_city == normalized_search or normalized_search in city_parts:
            matches.append(airport)
    return matches


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


def get_flight_details(flight_number: str) -> dict[str, list[dict[str, Any]] | dict[str, Any] | int]:
    """Return the main details for one flight number."""
    flight = _fetch_one(
        """
        SELECT Number, Airline, Weekdays
        FROM FLIGHT
        WHERE Number = %s
        """,
        (flight_number,),
    )
    if flight is None:
        raise ValueError(f"Flight number {flight_number} does not exist.")

    instance_count_row = _fetch_one(
        """
        SELECT COUNT(*) AS instance_count
        FROM LEG_INSTANCE
        WHERE Flight_number = %s
        """,
        (flight_number,),
    )

    return {
        "flight": flight,
        "legs": get_flight_legs(flight_number),
        "fares": get_fares(flight_number),
        "instance_count": instance_count_row["instance_count"] if instance_count_row else 0,
    }


def search_direct_trips(origin: str, destination: str) -> list[dict[str, Any]]:
    """Return direct flight legs between two airports."""
    return _fetch_all(
        """
        SELECT
            fl.Flight_number,
            f.Airline,
            f.Weekdays,
            fl.Leg_no,
            fl.Dep_airport_code AS Origin,
            fl.Arr_airport_code AS Destination,
            fl.Scheduled_dep_time,
            fl.Scheduled_arr_time
        FROM FLIGHT_LEG fl
        JOIN FLIGHT f ON f.Number = fl.Flight_number
        WHERE fl.Dep_airport_code = %s
          AND fl.Arr_airport_code = %s
        ORDER BY fl.Scheduled_dep_time, fl.Flight_number, fl.Leg_no
        """,
        (origin, destination),
    )


def search_one_connection_trips(origin: str, destination: str) -> list[dict[str, Any]]:
    """Return trips that use exactly one connecting airport."""
    return _fetch_all(
        """
        SELECT
            first_leg.Flight_number AS First_flight,
            first_flight.Airline AS First_airline,
            first_leg.Leg_no AS First_leg,
            first_leg.Dep_airport_code AS Origin,
            first_leg.Arr_airport_code AS Connection,
            first_leg.Scheduled_dep_time AS First_dep_time,
            first_leg.Scheduled_arr_time AS First_arr_time,
            second_leg.Flight_number AS Second_flight,
            second_flight.Airline AS Second_airline,
            second_leg.Leg_no AS Second_leg,
            second_leg.Arr_airport_code AS Destination,
            second_leg.Scheduled_dep_time AS Second_dep_time,
            second_leg.Scheduled_arr_time AS Second_arr_time
        FROM FLIGHT_LEG first_leg
        JOIN FLIGHT first_flight ON first_flight.Number = first_leg.Flight_number
        JOIN FLIGHT_LEG second_leg
          ON second_leg.Dep_airport_code = first_leg.Arr_airport_code
        JOIN FLIGHT second_flight ON second_flight.Number = second_leg.Flight_number
        WHERE first_leg.Dep_airport_code = %s
          AND second_leg.Arr_airport_code = %s
          AND first_leg.Arr_airport_code <> first_leg.Dep_airport_code
          AND first_leg.Arr_airport_code <> second_leg.Arr_airport_code
          AND (first_leg.Flight_number <> second_leg.Flight_number OR first_leg.Leg_no <> second_leg.Leg_no)
          AND second_leg.Scheduled_dep_time > first_leg.Scheduled_arr_time
        ORDER BY first_leg.Scheduled_dep_time, second_leg.Scheduled_dep_time
        LIMIT 50
        """,
        (origin, destination),
    )


def search_trips_for_airports(
    origin_airports: list[dict[str, Any]],
    destination_airports: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Search direct and one-connection trips across resolved airport rows."""
    direct: list[dict[str, Any]] = []
    one_connection: list[dict[str, Any]] = []
    seen_direct: set[tuple[Any, ...]] = set()
    seen_connection: set[tuple[Any, ...]] = set()

    for origin in origin_airports:
        for destination in destination_airports:
            origin_code = origin["Airport_code"]
            destination_code = destination["Airport_code"]
            if origin_code == destination_code:
                continue

            for trip in search_direct_trips(origin_code, destination_code):
                key = (trip["Flight_number"], trip["Leg_no"])
                if key not in seen_direct:
                    seen_direct.add(key)
                    direct.append(trip)

            for trip in search_one_connection_trips(origin_code, destination_code):
                key = (
                    trip["First_flight"],
                    trip["First_leg"],
                    trip["Second_flight"],
                    trip["Second_leg"],
                )
                if key not in seen_connection:
                    seen_connection.add(key)
                    one_connection.append(trip)

    return {"direct": direct, "one_connection": one_connection}


def get_aircraft_utilization(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Return aircraft usage counts and scheduled flight hours for a date range."""
    return _fetch_all(
        """
        SELECT
            li.Airplane_id,
            a.Type_name,
            COUNT(*) AS Leg_instance_count,
            ROUND(
                SUM(
                    TIMESTAMPDIFF(
                        MINUTE,
                        TIMESTAMP(li.Date, li.Dep_time),
                        TIMESTAMP(
                            DATE_ADD(li.Date, INTERVAL (li.Arr_time < li.Dep_time) DAY),
                            li.Arr_time
                        )
                    )
                ) / 60,
                2
            ) AS Scheduled_hours,
            MIN(li.Date) AS First_service_date,
            MAX(li.Date) AS Last_service_date
        FROM LEG_INSTANCE li
        JOIN AIRPLANE a ON a.Airplane_id = li.Airplane_id
        WHERE li.Date BETWEEN %s AND %s
        GROUP BY li.Airplane_id, a.Type_name
        ORDER BY Scheduled_hours DESC, Leg_instance_count DESC, li.Airplane_id
        """,
        (start_date, end_date),
    )


def get_passenger_itinerary(customer_name: str) -> list[dict[str, Any]]:
    """Return booked legs and seats for a passenger name."""
    return _fetch_all(
        """
        SELECT
            s.Customer_name,
            s.Cphone,
            s.Flight_number,
            f.Airline,
            s.Leg_no,
            s.Date,
            fl.Dep_airport_code,
            fl.Arr_airport_code,
            li.Dep_time,
            li.Arr_time,
            s.Seat_no
        FROM SEAT s
        JOIN FLIGHT f ON f.Number = s.Flight_number
        JOIN FLIGHT_LEG fl
          ON fl.Flight_number = s.Flight_number
         AND fl.Leg_no = s.Leg_no
        JOIN LEG_INSTANCE li
          ON li.Flight_number = s.Flight_number
         AND li.Leg_no = s.Leg_no
         AND li.Date = s.Date
        WHERE LOWER(s.Customer_name) = LOWER(%s)
        ORDER BY s.Date, li.Dep_time, s.Flight_number, s.Leg_no
        """,
        (customer_name,),
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


def safe_get_flight_details(
    flight_number: str,
) -> tuple[bool, dict[str, list[dict[str, Any]] | dict[str, Any] | int] | str]:
    try:
        return True, get_flight_details(flight_number)
    except (Error, ValueError) as exc:
        return False, f"Error fetching flight details: {exc}"


def safe_search_trips(origin: str, destination: str) -> tuple[bool, dict[str, list[dict[str, Any]]] | str]:
    try:
        origin_airports = resolve_airport_search(origin)
        destination_airports = resolve_airport_search(destination)

        if not origin_airports:
            return False, f"No airport found for origin {origin}."
        if not destination_airports:
            return False, f"No airport found for destination {destination}."

        distinct_pairs = [
            (origin_airport, destination_airport)
            for origin_airport in origin_airports
            for destination_airport in destination_airports
            if origin_airport["Airport_code"] != destination_airport["Airport_code"]
        ]
        if not distinct_pairs:
            return False, "Origin and destination must resolve to different airports."

        result = search_trips_for_airports(origin_airports, destination_airports)
        result["origin_airports"] = origin_airports
        result["destination_airports"] = destination_airports
        return True, result
    except Error as exc:
        return False, f"Error searching trips: {exc}"


def safe_get_aircraft_utilization(
    start_date: str, end_date: str
) -> tuple[bool, list[dict[str, Any]] | str]:
    try:
        return True, get_aircraft_utilization(start_date, end_date)
    except Error as exc:
        return False, f"Error fetching aircraft utilization: {exc}"


def safe_get_passenger_itinerary(customer_name: str) -> tuple[bool, list[dict[str, Any]] | str]:
    try:
        customer_name = customer_name.strip()
        if not customer_name:
            return False, "Customer name cannot be empty."
        return True, get_passenger_itinerary(customer_name)
    except Error as exc:
        return False, f"Error fetching passenger itinerary: {exc}"


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
