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
9. Search trip between two airports
10. Search flight details by flight number
11. Aircraft utilization report
12. Passenger itinerary by customer name
13. Exit
"""

from __future__ import annotations

from datetime import datetime

from mysql.connector import Error

from db import prompt_for_password, test_connection
from queries import (
    flight_exists,
    leg_exists,
    leg_instance_exists,
    safe_get_aircraft_utilization,
    safe_get_fares,
    safe_get_flight_details,
    safe_get_flight_legs,
    safe_get_flights,
    safe_get_leg_instances,
    safe_get_passenger_itinerary,
    safe_search_trips,
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


def _print_prompt_db_error(exc: Error) -> None:
    """Show database prompt errors without crashing the menu loop."""
    print(f"Database error: {exc}")
    print("Returning to the main menu.")


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


def prompt_customer_name_search():
    """Prompt for a passenger name search without applying reservation-name rules."""
    while True:
        customer_name = prompt_text_or_menu("Customer name")
        if customer_name is RETURN_TO_MENU:
            return RETURN_TO_MENU
        if customer_name:
            return customer_name
        print("Customer name cannot be empty. Try again or press m for main menu.")


def prompt_airport_search(label: str):
    """Prompt for a city name or three-letter airport code."""
    while True:
        airport_search = prompt_text_or_menu(label)
        if airport_search is RETURN_TO_MENU:
            return RETURN_TO_MENU
        if airport_search:
            return airport_search
        print("Enter a city name or three-letter airport code. Try again or press m for main menu.")


def format_airport_matches(airports: list[dict]) -> str:
    """Format resolved airport rows for trip-search output."""
    if not airports:
        return "none"

    return ", ".join(
        f"{airport['Airport_code']} ({airport['City']})"
        for airport in airports
    )


def prompt_valid_date(label: str):
    """Prompt for a valid date string."""
    while True:
        date_str = input(f"{label} (YYYY-MM-DD) or m for main menu: ").strip()
        if _is_main_menu_request(date_str):
            return RETURN_TO_MENU
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please enter YYYY-MM-DD or press m for main menu.")
            continue
        return date_str


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
        try:
            exists = flight_exists(flight_number)
        except Error as exc:
            _print_prompt_db_error(exc)
            return RETURN_TO_MENU
        if not exists:
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
        try:
            exists = leg_exists(flight_number, leg_no)
        except Error as exc:
            _print_prompt_db_error(exc)
            return RETURN_TO_MENU
        if not exists:
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
        try:
            exists = leg_exists(flight_number, leg_no)
        except Error as exc:
            _print_prompt_db_error(exc)
            return RETURN_TO_MENU
        if not exists:
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

        try:
            exists = leg_instance_exists(flight_number, leg_no, date_str)
        except Error as exc:
            _print_prompt_db_error(exc)
            return RETURN_TO_MENU
        if not exists:
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
    print("9. Search trip between two airports")
    print("10. Search flight details by flight number")
    print("11. Aircraft utilization report")
    print("12. Passenger itinerary by customer name")
    print("13. Exit")


def print_rows(title: str, rows: list[dict]) -> None:
    """
    Print a list of dictionary rows in a readable format with pagination.
    """
    print(f"\n{title}")
    if not rows:
        print("No rows found.")
        return

    page_size = 20
    for index, row in enumerate(rows, start=1):
        print(f"\n[{index}]")
        for key, value in row.items():
            print(f"{key}: {value}")

        if index % page_size == 0 and index < len(rows):
            choice = input(f"\nShowing {index}/{len(rows)}. Press Enter for more, or m for menu: ").strip()
            if _is_main_menu_request(choice):
                print("Returning to the main menu.")
                break


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


def handle_search_trips() -> None:
    """Search direct and one-connection trips between two airports."""
    origin = prompt_airport_search("Origin city or airport code")
    if origin is RETURN_TO_MENU:
        return

    destination = prompt_airport_search("Destination city or airport code")
    if destination is RETURN_TO_MENU:
        return

    ok, result = safe_search_trips(origin, destination)
    if not ok:
        print(result)
        return

    print(f"\nResolved origin: {format_airport_matches(result['origin_airports'])}")
    print(f"Resolved destination: {format_airport_matches(result['destination_airports'])}")
    print_rows(f"Direct trips from {origin} to {destination}:", result["direct"])
    print_rows(
        f"One-connection trips from {origin} to {destination}:",
        result["one_connection"],
    )


def handle_search_flight_details() -> None:
    """Show complete details for a flight number."""
    flight_number = prompt_valid_flight_number()
    if flight_number is RETURN_TO_MENU:
        return

    ok, result = safe_get_flight_details(flight_number)
    if not ok:
        print(result)
        return

    print_rows(f"Flight {flight_number}:", [result["flight"]])
    print_rows(f"Legs for flight {flight_number}:", result["legs"])
    print_rows(f"Fares for flight {flight_number}:", result["fares"])
    print(f"\nLeg instances scheduled for flight {flight_number}: {result['instance_count']}")


def handle_aircraft_utilization_report() -> None:
    """Show aircraft usage between two dates."""
    start_date = prompt_valid_date("Start date")
    if start_date is RETURN_TO_MENU:
        return

    end_date = prompt_valid_date("End date")
    if end_date is RETURN_TO_MENU:
        return

    if end_date < start_date:
        print("End date cannot be before start date.")
        return

    ok, result = safe_get_aircraft_utilization(start_date, end_date)
    if not ok:
        print(result)
        return

    print_rows(f"Aircraft utilization from {start_date} to {end_date}:", result)


def handle_passenger_itinerary() -> None:
    """Show booked legs and seats for a customer name."""
    customer_name = prompt_customer_name_search()
    if customer_name is RETURN_TO_MENU:
        return

    ok, result = safe_get_passenger_itinerary(customer_name)
    if not ok:
        print(result)
        return

    print_rows(f"Passenger itinerary for {customer_name}:", result)


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
        try:
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
                handle_search_trips()
            elif choice == "10":
                handle_search_flight_details()
            elif choice == "11":
                handle_aircraft_utilization_report()
            elif choice == "12":
                handle_passenger_itinerary()
            elif choice == "13":
                print("Goodbye.")
                break
            else:
                print("Invalid option. Please choose a number from 1 to 13.")
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break


if __name__ == "__main__":
    main()
