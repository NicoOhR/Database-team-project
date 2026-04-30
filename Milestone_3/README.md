# Airline Management System (Milestone 3)

**Course:** CS 4347 - Database Systems  
**Team:** Dubnium

## Build Info

- Python version: Python 3.10+ (tested with Python 3)
- MySQL version: MySQL 8.0+ (tested with MySQL client 9.x)
- Required modules:
  - `mysql-connector-python`
  - `tkinter` (standard library, no pip install needed)

Install command:

```bash
python3 -m pip install -r requirements.txt
```

Database load command:

```bash
mysql --local-infile=1 -u root -p < project_4347.sql
```

GUI run command:

```bash
python3 gui.py
```

Startup:
- The GUI prompts for the MySQL password before opening the main application tabs.

## Final Project Design

```text
Milestone_3/
|-- data/
|-- db.py
|-- main.py
|-- gui.py
|-- queries.py
|-- milestone3_queries.py
|-- reservations.py
|-- project_4347.sql
|-- requirements.txt
|-- README.md
`-- readme.pdf
```

## Design Patterns

- `db.py`: database connection layer (single place for MySQL connection/cursor lifecycle)
- `queries.py`: existing read-only query layer used by console workflow
- `milestone3_queries.py`: Milestone 3 read-only GUI query layer
- `reservations.py`: transaction/business logic layer for booking, canceling, and validation
- `gui.py`: presentation layer (Tkinter tabs, forms, result tables, and action handlers)

Schema/UML note:
- Core schema remains based on Figure 3.21.
- Reservation storage remains in `SEAT`.
- No additional schema tables are required for Milestone 3 GUI features.

## Required GUI Tabs Implemented

1. Flight Search
- Inputs: origin airport code, destination airport code, date
- Output: direct flights and one-connection flights
- Rule: one-connection gap is at least 1 hour
- One-connection output columns include:
  - `First_airline`, `First_flight_number`, `First_leg_no`, `First_date`, `Second_date`
  - `Origin_airport`, `Connection_airport`
  - `First_departure_time`, `First_arrival_time`
  - `Second_airline`, `Second_flight_number`, `Second_leg_no`
  - `Second_departure_time`, `Second_arrival_time`, `Destination_airport`

2. Flight Details
- Inputs: flight number, date
- Output: airline, flight number, date, departure time, arrival time

3. Seat Availability
- Inputs: flight number, leg number, date
- Output: total seats, booked seats, remaining seats, availability status

4. Book Seat
- Inputs: flight number, leg number, date, seat number, customer name, phone
- Output: booking success/failure message and a booking result table for the booked itinerary rows

5. Passenger Itinerary
- Inputs: customer name field and phone field
- Actions: separate search buttons for name and phone
- Output: booked legs, airports, scheduled times, seat assignments

6. Aircraft Utilization
- Inputs: airplane registration number, start date, end date
- Output: airplane, airplane type, registration number, number of flights

7. Cancel Reservation
- Inputs: flight number, leg number, date, seat number
- Output: cancellation success/failure message

## Quick Start Guide

1. Start MySQL and load the schema/data:

```bash
mysql --local-infile=1 -u root -p < project_4347.sql
```

2. Launch GUI:

```bash
python3 gui.py
```

3. Search trips:
- Open **Flight Search**
- Enter origin code, destination code, and date
- Click **Search**

4. Search flight details:
- Open **Flight Details**
- Enter flight number and date
- Click **Search**

5. Check seats:
- Open **Seat Availability**
- Enter flight number, leg number, and date
- Click **Check**

6. Book a seat:
- Open **Book Seat**
- Enter flight, leg, date, seat, customer name, phone
- Click **Book seat**

7. Retrieve passenger itinerary:
- Open **Passenger Itinerary**
- Enter customer name and click **Search by name**, or
- Enter phone and click **Search by phone**

8. Run aircraft utilization report:
- Open **Aircraft Utilization**
- Enter registration number, start date, end date
- Click **Run report**

9. Cancel a reservation:
- Open **Cancel Reservation**
- Enter flight number, leg number, date, seat number
- Click **Cancel reservation**

## Notes

- `main.py` console app is kept for backward compatibility and testing.
- Milestone 3 grading focus is GUI functionality and usability.
- All GUI result tables include horizontal and vertical scrollbars.
- Final submission should be a single archive containing source files and `readme.pdf`.
