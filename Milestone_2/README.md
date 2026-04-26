# Airport Management System

**Course:** CS 4347 - Database Systems
**Milestone:** 2
**Team Name:** Dubnium

## Overview

This package contains the Milestone 2 host application for the airline database project.
It implements the required application logic against a MySQL database whose core schema follows
Figure 3.21 from the textbook.

Milestone 2 asks for programming logic rather than a GUI. For that reason, this submission uses
a menu-driven console application that exercises the SQL database directly.

## Milestone 2 Compliance

- host application language: Python 3
- SQL database: MySQL
- interface style: console application, which matches the Milestone 2 focus on logic
- schema basis: Figure 3.21 airline ER diagram
- delivered artifacts: SQL schema/data loader, Python host application, and build/run instructions

## Package Contents

```text
Milestone_2/
|-- README.md
|-- requirements.txt
|-- project_4347.sql
|-- db.py
|-- main.py
|-- queries.py
|-- reservations.py
`-- data/
    |-- AIRPORT.csv
    |-- AIRPLANE_TYPE.csv
    |-- AIRPLANE.csv
    |-- CAN_LAND.csv
    |-- FLIGHT.csv
    |-- FLIGHT_LEG.csv
    |-- LEG_INSTANCE.csv
    |-- FARE.csv
    `-- SEAT.csv
```

## ER Diagram Mapping

The implementation follows the entities and relationships in Figure 3.21 as follows:

- `AIRPORT`, `AIRPLANE_TYPE`, `AIRPLANE`, `CAN_LAND`, `FLIGHT`, `FLIGHT_LEG`, `LEG_INSTANCE`, and `FARE` map directly from the ER diagram.
- The `SEAT` table stores one booked seat for one leg instance, together with `Customer_name` and `Cphone`. In the relational implementation, this is how the reservation information from Figure 3.21 is recorded.
- The `AIRPLANE_SEAT` table is an auxiliary implementation table used to load the provided seat-layout CSV and validate that a requested seat exists on the airplane assigned to a leg instance. It supports the application logic but does not change the core ER design.
- Database triggers enforce that every booked seat is valid for the airplane assigned to the selected leg instance and keep `LEG_INSTANCE.No_of_avail_seats` synchronized even for direct SQL writes.

## Prerequisites

- Python 3
- MySQL server running locally
- a MySQL account that can create the `project_4347` database

## Python Dependency

Install the required connector from inside `Milestone_2/`:

```bash
python3 -m pip install -r requirements.txt
```

`requirements.txt` contains:

```text
mysql-connector-python>=9.0.0
```

## MySQL Configuration

This package uses `LOAD DATA LOCAL INFILE` to import the provided CSV files. If `local_infile`
is disabled, enable it before running the SQL script:

```sql
SHOW GLOBAL VARIABLES LIKE 'local_infile';
SET GLOBAL local_infile = 1;
SHOW GLOBAL VARIABLES LIKE 'local_infile';
```

## Build And Run

From inside the `Milestone_2/` directory:

1. Create and load the database:

```bash
mysql --local-infile=1 -u root -p < project_4347.sql
```

2. Start the host application:

```bash
python3 main.py
```

The application prompts for the MySQL password at startup. Enter `m` at later prompts to return
to the main menu.

## Application Features

The menu supports the following Milestone 2 operations:

1. Test database connection
2. Show the first 10 flights
3. Show all legs for a flight
4. Show all fares for a flight
5. Show leg instances for a flight
6. Show available seats for a specific leg instance
7. Make a reservation
8. Cancel a reservation
9. Exit

## Runtime Assumptions

- host: `localhost`
- port: `3306`
- database: `project_4347`
- user: `root`

The password is requested at runtime and is not stored in the repository.
If needed, the host, port, user, and database name can be overridden with
`AIRLINE_DB_HOST`, `AIRLINE_DB_PORT`, `AIRLINE_DB_USER`, and `AIRLINE_DB_NAME`.
Customer phone numbers must be entered as exactly 10 digits.

## Submission Notes

- This directory is the authoritative Milestone 2 package.
- The final archive should be created from `Milestone_2/`.
- This README is the source document for the required submission readme; export it to `readme.pdf` when assembling the final archive if the course submission format requires PDF specifically.

## Team Members

- Nimrod Ohayon Rozanes
- Ali Mohammed
- Kourosh Torkaman Sohrabi
- Yael Roldan Rico
- Ethan John Bickel
