# Milestone 2 - Airport Management System

**Course:** CS 4347 – Database Systems
**Team Name:** Dubnium

## Overview

This project implements an Airport Management System using **MySQL** and **Python**.
The database schema is based on the airline ER diagram from **Figure 3.21** in the course textbook.

The project includes:

- a MySQL schema and data-loading script
- a console-based Python application
- query features for flights, legs, fares, and leg instances
- reservation-related application logic with seat-layout validation

---

## Technologies Used

- **Python 3**
- **MySQL**
- **mysql-connector-python**

---

## Project Files

```text
project/
├── project_4347.sql
├── main.py
├── db.py
├── queries.py
├── reservations.py
├── requirements.txt
├── README.md
└── data/
    ├── AIRPORT.csv
    ├── AIRPLANE_TYPE.csv
    ├── AIRPLANE.csv
    ├── SEAT.csv
    ├── CAN_LAND.csv
    ├── FLIGHT.csv
    ├── FLIGHT_LEG.csv
    ├── LEG_INSTANCE.csv
    └── FARE.csv
```

---

## Prerequisites

Before running the project, make sure you have:

- Python 3 installed
- MySQL installed and running
- access to a MySQL user account
- the project folder downloaded with the same file structure shown above

---

## Install Python Dependency

From the project directory, run:

```bash
python3 -m pip install -r requirements.txt
```

Contents of `requirements.txt`:

```text
mysql-connector-python>=9.0.0
```

---

## MySQL Configuration

This project uses `LOAD DATA LOCAL INFILE` to import CSV files.
`local_infile` must be enabled in MySQL.

Open MySQL and run:

```sql
SHOW GLOBAL VARIABLES LIKE 'local_infile';
SET GLOBAL local_infile = 1;
SHOW GLOBAL VARIABLES LIKE 'local_infile';
```

If MySQL disables this again after restart, enable `local_infile=1` in the MySQL server configuration and restart MySQL.

---

## Create and Load the Database

Open Terminal and move into the project directory:

```bash
cd path/to/project
```

Run the SQL script:

```bash
mysql --local-infile=1 -u root -p < project_4347.sql
```

Enter your MySQL password when prompted.

This script will:

- create the `project_4347` database
- create all required tables
- load the CSV files into the database

---

## Run the Application

From the project directory, run:

```bash
python3 main.py
```

The program will first prompt you for your MySQL password (input is hidden). If the password is incorrect, you can try again.

---

## Application Features

The console application includes the following menu options:

1. Test database connection
2. Show first 10 flights
3. Show flight legs for a flight
4. Show fares for a flight
5. Show leg instances for a flight
6. Show available seats for a leg instance
7. Make reservation
8. Cancel reservation
9. Exit

---

## Database Connection Defaults

The application uses the following default connection settings:

- **Host:** `localhost`
- **Port:** `3306`
- **User:** `root`
- **Database:** `project_4347`

The password is requested securely at runtime and is not stored in the code or in a configuration file.

---

## Notes

- Run `project_4347.sql` before running `main.py`
- Keep the data/ folder in the same directory as `project_4347.sql`
- Make sure `local_infile` is enabled if CSV imports fail
- Use valid flight numbers when testing application features
- `data/SEAT.csv` is loaded into `AIRPLANE_SEAT`, which stores the valid seat layout for each airplane
- The booking table `SEAT` starts empty, so the SQL load script resets `LEG_INSTANCE.No_of_avail_seats` to full airplane capacity

---

## Team

**Team Name:** Dubnium

**Team Members:**

- Nimrod Ohayon Rozanes
- Ali Mohammed
- Kourosh Torkaman Sohrabi
- Yael Roldan Rico
- Ethan John Bickel
