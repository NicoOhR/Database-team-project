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

from datetime import datetime

from db import prompt_for_password, test_connection
from queries import (
    flight_exists,
    leg_exists,
    leg_instance_exists,
    safe_get_fares,
    safe_get_flight_legs,
    safe_get_flights,
    safe_get_leg_instances,
    safe_show_available_seats_summary,
)
from reservations import (
    cancel_reservation,
    make_reservation,
    validate_customer_name,
    validate_customer_phone,
    validate_seat_for_reservation,
)

RETURN_TO_MENU = object()


def _is_main_menu_request(value: str) -> bool:
    """Return True when the user wants to return to the main menu."""
    return value.lower() == "m"


def prompt_text_or_menu(label: str):
    """Prompt for text input while allowing a main-menu return."""
    value = input(f"{label} or m for main menu: ").strip()
    if _is_main_menu_request(value):
        return RETURN_TO_MENU
    return value


def prompt_valid_customer_phone():
    """Prompt until the customer phone is valid or the user returns to menu."""
    while True:
        cphone = prompt_text_or_menu("Customer phone")
        if cphone is RETURN_TO_MENU:
            return RETURN_TO_MENU

        ok, result = validate_customer_phone(cphone)
        if ok:
            return result

        print(f"{result} Try again or press m for main menu.")


def prompt_valid_customer_name():
    """Prompt until the customer name is valid or the user returns to menu."""
    while True:
        customer_name = prompt_text_or_menu("Customer name")
        if customer_name is RETURN_TO_MENU:
            return RETURN_TO_MENU

        ok, result = validate_customer_name(customer_name)
        if ok:
            return result

        print(f"{result} Try again or press m for main menu.")


def prompt_valid_reservation_seat(flight_number: str, leg_no: int, date_str: str):
    """Prompt until the seat is valid for this leg instance or user returns."""
    while True:
        seat_no = prompt_text_or_menu("Seat number")
        if seat_no is RETURN_TO_MENU:
            return RETURN_TO_MENU

        ok, result = validate_seat_for_reservation(flight_number, leg_no, date_str, seat_no)
        if ok:
            return result

        print(f"{result} Try again or press m for main menu.")


def prompt_valid_flight_number():
    """Prompt until the user enters a valid flight number or returns to menu."""
    while True:
        flight_number = input("Flight number or m for main menu: ").strip()
        if not flight_number:
            print("Flight number cannot be empty.")
            continue
        if _is_main_menu_request(flight_number):
            return RETURN_TO_MENU
        if not flight_exists(flight_number):
            print(f"Flight number {flight_number} does not exist.")
            continue
        return flight_number


def prompt_valid_leg_number(flight_number: str):
    """Prompt until the user enters a valid leg number for a flight."""
    while True:
        leg_raw = input("Leg number or m for main menu: ").strip()
        if not leg_raw:
            print("Leg number cannot be empty.")
            continue
        if _is_main_menu_request(leg_raw):
            return RETURN_TO_MENU
        if not leg_raw.isdigit():
            print("Leg number must be a whole number. Try again or press m for main menu.")
            continue

        leg_no = int(leg_raw)
        if not leg_exists(flight_number, leg_no):
            print(
                f"Leg number {leg_no} does not exist for flight {flight_number}. "
                "Try again or press m for main menu."
            )
            continue
        return leg_no


def prompt_optional_leg_number(flight_number: str):
    """Prompt for an optional leg number while allowing a main-menu return."""
    while True:
        leg_raw = input("Optional leg number, m for main menu, or press Enter to skip: ").strip()
        if not leg_raw:
            return None
        if _is_main_menu_request(leg_raw):
            return RETURN_TO_MENU
        if not leg_raw.isdigit():
            print("Leg number must be a whole number. Try again or press m for main menu.")
            continue

        leg_no = int(leg_raw)
        if not leg_exists(flight_number, leg_no):
            print(
                f"Leg number {leg_no} does not exist for flight {flight_number}. "
                "Try again or press m for main menu."
            )
            continue
        return leg_no


def prompt_valid_date_for_leg_instance(flight_number: str, leg_no: int):
    """Prompt for a valid date and confirm the selected leg instance exists."""
    while True:
        date_str = input("Date (YYYY-MM-DD) or m for main menu: ").strip()
        if _is_main_menu_request(date_str):
            return RETURN_TO_MENU
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please enter YYYY-MM-DD or press m to return to the main menu.")
            continue

        if not leg_instance_exists(flight_number, leg_no, date_str):
            print(
                f"Flight {flight_number} and leg {leg_no} are valid, "
                f"but no leg instance exists on {date_str}."
            )
            continue
        return date_str


def prompt_valid_flight_leg_date() -> tuple[str, int, str] | None:
    """Shared flow for options that require flight, leg, and date."""
    flight_number = prompt_valid_flight_number()
    if flight_number is RETURN_TO_MENU:
        return None

    leg_no = prompt_valid_leg_number(flight_number)
    if leg_no is RETURN_TO_MENU:
        return None

    date_str = prompt_valid_date_for_leg_instance(flight_number, leg_no)
    if date_str is RETURN_TO_MENU:
        return None

    return flight_number, leg_no, date_str


def format_letter_summary(letters: list[str]) -> str:
    """Format seat letters as a compact range when possible."""
    if not letters:
        return "none"

    normalized = sorted({letter.upper() for letter in letters})
    if all(len(letter) == 1 for letter in normalized):
        code_points = [ord(letter) for letter in normalized]
        if code_points == list(range(code_points[0], code_points[-1] + 1)):
            if len(normalized) == 1:
                return normalized[0]
            return f"{normalized[0]}-{normalized[-1]}"
    return ", ".join(normalized)


def format_limited_list(values: list[str], limit: int = 5, total_count: int | None = None) -> str:
    """Format a short sample without flooding the console."""
    if not values:
        return "none"

    rendered = ", ".join(values[:limit])
    count = len(values) if total_count is None else total_count
    if count > limit:
        rendered += "..."
    return rendered


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
    flight_number = prompt_valid_flight_number()
    if flight_number is RETURN_TO_MENU:
        return

    ok, result = safe_get_flight_legs(flight_number)
    if not ok:
        print(result)
        return
    print_rows(f"Flight legs for flight {flight_number}:", result)


def handle_show_fares() -> None:
    """Show fare options for a specific flight."""
    flight_number = prompt_valid_flight_number()
    if flight_number is RETURN_TO_MENU:
        return

    ok, result = safe_get_fares(flight_number)
    if not ok:
        print(result)
        return
    print_rows(f"Fares for flight {flight_number}:", result)


def handle_show_leg_instances() -> None:
    """Show leg instances for a flight, optionally filtered by leg number."""
    flight_number = prompt_valid_flight_number()
    if flight_number is RETURN_TO_MENU:
        return

    leg_no = prompt_optional_leg_number(flight_number)
    if leg_no is RETURN_TO_MENU:
        return

    ok, result = safe_get_leg_instances(flight_number, leg_no)
    if not ok:
        print(result)
        return

    if leg_no is None:
        print_rows(f"Leg instances for flight {flight_number}:", result)
    else:
        print_rows(f"Leg instances for leg {leg_no} of flight {flight_number}:", result)


def handle_show_available_seats() -> None:
    """Show a compact seat summary for one validated leg instance."""
    selection = prompt_valid_flight_leg_date()
    if selection is None:
        return

    flight_number, leg_no, date_str = selection
    ok, result = safe_show_available_seats_summary(flight_number, leg_no, date_str)
    if not ok:
        print(result)
        return

    leg_instance = result["leg_instance"]
    print("\nLeg instance:")
    for key, value in leg_instance.items():
        if key == "No_of_avail_seats":
            continue
        print(f"{key}: {value}")

    print(f"\nTotal seats: {result['total_seat_count']}")
    print(f"Booked seats count: {result['booked_count']}")
    print(f"Remaining available seats: {result['available_count']}")

    if result["stored_available_count"] != result["available_count"]:
        print(
            "Stored LEG_INSTANCE.No_of_avail_seats is "
            f"{result['stored_available_count']}; calculated remaining is "
            f"{result['available_count']}."
        )

    row_min = result["available_row_min"]
    row_max = result["available_row_max"]
    if row_min is None or row_max is None:
        print("Available seat row range: none")
    else:
        print(f"Available seat row range: {row_min}-{row_max}")

    print(f"Available seat letters: {format_letter_summary(result['available_letters'])}")
    print(
        "Sample available seats: "
        f"{format_limited_list(result['available_sample_seats'], total_count=result['available_count'])}"
    )
    print(f"Booked seats: {format_limited_list(result['booked_seat_numbers'], limit=10)}")


def handle_make_reservation() -> None:
    """Create a reservation after validating the selected leg instance."""
    selection = prompt_valid_flight_leg_date()
    if selection is None:
        return

    flight_number, leg_no, date_str = selection

    seat_no = prompt_valid_reservation_seat(flight_number, leg_no, date_str)
    if seat_no is RETURN_TO_MENU:
        return

    customer_name = prompt_valid_customer_name()
    if customer_name is RETURN_TO_MENU:
        return

    cphone = prompt_valid_customer_phone()
    if cphone is RETURN_TO_MENU:
        return

    ok, message = make_reservation(
        flight_number, leg_no, date_str, seat_no, customer_name, cphone
    )
    print(message)


def handle_cancel_reservation() -> None:
    """Cancel a reservation after validating the selected leg instance."""
    selection = prompt_valid_flight_leg_date()
    if selection is None:
        return

    flight_number, leg_no, date_str = selection
    seat_no = prompt_text_or_menu("Seat number")
    if seat_no is RETURN_TO_MENU:
        return

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
