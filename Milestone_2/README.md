# Airline Management System (Milestone 2)

**CS 4347 - Database Systems**
**Team:** Dubnium

## ✈️ Overview

This package implements a robust, menu-driven Python host application for an Airline Management System. Built on a MySQL backend, the system is based on Figure 3.21, with implementation extensions for seat validation and reservation handling. The application provides comprehensive logic for flight management, real-time seat reservations, multi-leg trip searches, and operational reporting.

## 🛠️ Core Technologies

- **Language:** Python 3.10+
- **Database:** MySQL 8.0+
- **Driver:** `mysql-connector-python`
- **Architecture:** Console-based interface with localized logic layers for database queries and reservation transactions.

## 📂 Project Structure

```text
Milestone_2/
├── data/                  # Source CSV data for bootstrap
├── db.py                  # Database connection & session management
├── main.py                # Application entry point & UI logic
├── queries.py             # Read-only SQL abstractions & data retrieval
├── reservations.py        # Transactional logic for booking & capacity
├── project_4347.sql       # SQL Schema & Trigger definitions
├── README.md              # Markdown project documentation
├── readme.pdf             # Required submission readme PDF
└── requirements.txt       # Python dependencies
```

## 🚀 Getting Started

### 1. Prerequisites

Ensure you have a local MySQL server running and Python 3 installed.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Configuration

The application requires `local_infile` to be enabled for data loading. Execute the following in your MySQL client:

```sql
SET GLOBAL local_infile = 1;
```

### 4. Build and Initialize

Load the schema and bootstrap the initial dataset:

```bash
mysql --local-infile=1 -u root -p < project_4347.sql
```

### 5. Run the Application

```bash
python3 main.py
```

## 📱 Application Features

The menu supports the following Milestone 2 operations:

1. **Test database connection:** Verifies connectivity and identifies the active database.
2. **Show first 10 flights:** Displays basic information for the first 10 flights in the system.
3. **Show all legs for a flight:** Lists every scheduled leg for a specific flight number.
4. **Show all fares for a flight:** Displays available pricing tiers and restrictions.
5. **Show leg instances for a flight:** Lists specific dates and times when a flight is scheduled to fly.
6. **Show available seats for a leg instance:** Provides a summary of capacity, booked seats, and a sample of available seat numbers.
7. **Make a reservation:** Allows a user to book a valid seat for a specific passenger.
8. **Cancel a reservation:** Removes a booking and restores seat capacity.
9. **Search trip between two airports:** Finds direct and one-connection trips.
10. **Search flight details by flight number:** Aggregates legs, fares, and instance counts for a flight.
11. **Aircraft utilization report:** Summarizes usage (hours and leg counts) for every airplane in a date range.
12. **Passenger itinerary by customer name:** Returns a complete list of booked legs and seats for a matching customer name.
13. **Exit:** Safely closes the application.

### Feature Highlights

- **Intelligent Trip Search:** Accepts either three-letter airport codes (e.g., `DFW`, `SFO`) or city names (e.g., `Dallas`, `San Francisco`). It automatically resolves city names to all relevant airports and supports both direct itineraries and trips with exactly one connection.
- **Operational Reporting:** The aircraft utilization report calculates flight duration and service frequency between a start and end date, providing a clear picture of fleet activity.
- **Customer Portals:** The passenger itinerary search enables quick retrieval of all flight legs and seat assignments associated with a specific name, facilitating easy travel management.

## 📊 Database Design

The implementation maps the textbook ER diagram to a relational schema with the following enhancements:

- **`SEAT` Table:** Acts as the central reservation ledger, storing customer details tied to specific leg instances.
- **`AIRPLANE_SEAT`:** A reference table defining the physical seat map for each aircraft type, ensuring users can only book valid seats.
- **`CAN_LAND`:** Stores compatibility rules for which aircraft types can land at specific airports.

## 🛡️ Runtime Assumptions

- **Host:** `localhost:3306`
- **Database:** `project_4347`
- **User:** `root` (Password prompted at runtime)
- **Data Integrity:** Phone numbers must be exactly 10 digits; customer names are validated against professional naming standards.

## 👥 Team Dubnium

- Nimrod Ohayon Rozanes
- Ali Mohammed
- Kourosh Torkaman Sohrabi
- Yael Roldan Rico
- Ethan John Bickel
