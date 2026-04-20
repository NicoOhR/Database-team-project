"""Console host application for CS 4347 Milestone 2.

This script is intentionally simple and heavily commented so it is easy to
learn from, demo, and modify as a team.

Menu layout:
1. Test database connection
2. Show first 10 flights
3. Show flight legs for a flight
4. Show fares for a flight
5. Show leg instances for a flight
6. Show available seats for a leg instance
7. Make reservation
8. Cancel reservation
9. Exit
"""

from __future__ import annotations
from db import prompt_for_password, test_connection
from datetime import datetime
from queries import (
    safe_get_fares,
    safe_get_flight_legs,
    safe_get_flights,
    safe_get_leg_instances,
    safe_show_available_seats_summary,
)
from reservations import cancel_reservation, make_reservation


def prompt_valid_date() -> str:
    """
    Prompt the user until they enter a valid date in YYYY-MM-DD format.

    This prevents confusing MySQL errors by validating the date before
    sending it to the database layer.
    """
    while True:
        date_str = input("Date (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            print("Invalid date format. Please enter the date as YYYY-MM-DD.")

def print_header() -> None:
    """Display the main menu."""
    print("\nAirport Management System (Milestone 2)")
    print("--------------------------------------")
    print("1. Test database connection")
    print("2. Show first 10 flights")
    print("3. Show flight legs for a flight")
    print("4. Show fares for a flight")
    print("5. Show leg instances for a flight")
    print("6. Show available seats for a leg instance")
    print("7. Make reservation")
    print("8. Cancel reservation")
    print("9. Exit")


def print_rows(title: str, rows: list[dict]) -> None:
    """
    Print a list of dictionary rows in a readable format.
    """
    print(f"\n{title}")
    if not rows:
        print("No rows found.")
        return

    for index, row in enumerate(rows, start=1):
        print(f"\n[{index}]")
        for key, value in row.items():
            print(f"{key}: {value}")


def handle_test_connection() -> None:
    """Run a quick DB connection check."""
    ok, message = test_connection()
    print(message)


def handle_show_flights() -> None:
    """Show the first 10 flights."""
    ok, result = safe_get_flights(10)
    if not ok:
        print(result)
        return
    print_rows("Showing up to 10 flights:", result)


def handle_show_flight_legs() -> None:
    """Show all legs for a specific flight."""
    flight_number = input("Flight number: ").strip()
    ok, result = safe_get_flight_legs(flight_number)
    if not ok:
        print(result)
        return
    print_rows(f"Flight legs for flight {flight_number}:", result)


def handle_show_fares() -> None:
    """Show fare options for a specific flight."""
    flight_number = input("Flight number: ").strip()
    ok, result = safe_get_fares(flight_number)
    if not ok:
        print(result)
        return
    print_rows(f"Fares for flight {flight_number}:", result)


def handle_show_leg_instances() -> None:
    """Show leg instances for a flight, optionally filtered by leg number."""
    flight_number = input("Flight number: ").strip()
    leg_raw = input("Optional leg number (press Enter to skip): ").strip()

    leg_no = None
    if leg_raw:
        if not leg_raw.isdigit():
            print("Leg number must be a whole number.")
            return
        leg_no = int(leg_raw)

    ok, result = safe_get_leg_instances(flight_number, leg_no)
    if not ok:
        print(result)
        return

    if leg_no is None:
        print_rows(f"Leg instances for flight {flight_number}:", result)
    else:
        print_rows(f"Leg instances for leg {leg_no} of flight {flight_number}:", result)


def handle_show_available_seats() -> None:
    """
    Show the selected leg instance plus booked seat records.

    In the schema, SEAT stores booked seats for a leg instance,
    not the full airplane seat map.
    """
    flight_number = input("Flight number: ").strip()
    leg_raw = input("Leg number: ").strip()
    date_str = prompt_valid_date()

    if not leg_raw.isdigit():
        print("Leg number must be a whole number.")
        return
    leg_no = int(leg_raw)

    ok, result = safe_show_available_seats_summary(flight_number, leg_no, date_str)
    if not ok:
        print(result)
        return

    leg_instance = result["leg_instance"]
    booked_seats = result["booked_seats"]

    print("\nLeg instance:")
    for key, value in leg_instance.items():
        print(f"{key}: {value}")

    print(f"\nRemaining available seats (from LEG_INSTANCE): {result['available_count']}")
    print(f"Currently booked seat records in SEAT: {result['booked_count']}")

    if booked_seats:
        print_rows("Booked seats:", booked_seats)
    else:
        print("No booked seats recorded yet for this leg instance.")

    print(
        "note: in the schema, SEAT stores booked seat "
        "records for a leg instance. It does not store the full airplane seat map."
    )


def handle_make_reservation() -> None:
    """
    Create a reservation by inserting a booked seat row into SEAT.

    """
    flight_number = input("Flight number: ").strip()
    leg_raw = input("Leg number: ").strip()
    date_str = prompt_valid_date()
    seat_no = input("Seat number: ").strip()
    customer_name = input("Customer name: ").strip()
    cphone = input("Customer phone: ").strip()

    if not leg_raw.isdigit():
        print("Leg number must be a whole number.")
        return
    leg_no = int(leg_raw)

    ok, message = make_reservation(
        flight_number, leg_no, date_str, seat_no, customer_name, cphone
    )
    print(message)


def handle_cancel_reservation() -> None:
    """
    Cancel a reservation by deleting a booked seat row from SEAT.
    """
    flight_number = input("Flight number: ").strip()
    leg_raw = input("Leg number: ").strip()
    date_str = prompt_valid_date()
    seat_no = input("Seat number: ").strip()

    if not leg_raw.isdigit():
        print("Leg number must be a whole number.")
        return
    leg_no = int(leg_raw)

    ok, message = cancel_reservation(flight_number, leg_no, date_str, seat_no)
    print(message)


def main() -> None:
    """Main console loop."""
    while True:
        print("Enter your MySQL password to start the application.")
        try:
            prompt_for_password()
        except KeyboardInterrupt:
            print("\nStartup cancelled.")
            return

        ok, message = test_connection()
        print(message)

        if ok:
            break

        print("Please try again.\n")

    while True:
        print_header()
        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            handle_test_connection()
        elif choice == "2":
            handle_show_flights()
        elif choice == "3":
            handle_show_flight_legs()
        elif choice == "4":
            handle_show_fares()
        elif choice == "5":
            handle_show_leg_instances()
        elif choice == "6":
            handle_show_available_seats()
        elif choice == "7":
            handle_make_reservation()
        elif choice == "8":
            handle_cancel_reservation()
        elif choice == "9":
            print("Goodbye.")
            break
        else:
            print("Invalid option. Please choose a number from 1 to 9.")


if __name__ == "__main__":
    main()