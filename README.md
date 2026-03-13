# CS4347 – Airline Database Project
### Milestone 1 – Schema Creation and Data Import

## Overview
This project is part of CS4347 – Database Systems.
The database design is based on the Airline ER diagram (Figure 3.21) from the course textbook.

In Milestone 1, the objective is to:

- Create relational tables for each entity type shown in the ER diagram.
- Define appropriate primary keys and foreign keys.
- Implement compound primary keys for weak entities.
- Import the provided CSV data files into the tables.

Later milestones will expand the database with additional constraints, queries, and application logic.

## Tables Created

The following tables were created based on the ER diagram:

- AIRPORT
- AIRPLANE_TYPE
- AIRPLANE
- CAN_LAND
- FLIGHT
- FLIGHT_LEG
- LEG_INSTANCE
- FARE
- SEAT

Each table corresponds to an entity in the ER model.

## Data Files Used

The following CSV files are imported into the database:

- AIRPORT.csv
- AIRPLANE_TYPE.csv
- AIRPLANE.csv
- CAN_LAND.csv
- FLIGHT.csv
- FLIGHT_LEG.csv
- LEG_INSTANCE.csv
- FARE.csv
- SEAT.csv

## How to Run the Script

1. Create the database

CREATE DATABASE cs4347;
USE cs4347;

2. Run the SQL script

mysql -u root -p cs4347 < project_script.sql

3. Import CSV data

The script uses LOAD DATA LOCAL INFILE to load the CSV data into the tables.

## Project Structure

## Project Structure

```text
CS4347-Airline-Database/
├── project_script.sql
├── README.md
└── data/
    ├── AIRPORT.csv
    ├── AIRPLANE_TYPE.csv
    ├── AIRPLANE.csv
    ├── CAN_LAND.csv
    ├── FLIGHT.csv
    ├── FLIGHT_LEG.csv
    ├── LEG_INSTANCE.csv
    ├── FARE.csv
    └── SEAT.csv
## Notes

- This repository contains Milestone 1 only.
- Future milestones will include additional constraints and queries.

## Team Name: Dubnium

## Team Members

- Nimrod Ohayon Rozanes
- Ali Mohammed
- Kourosh Torkaman Sohrabi
- Yael Roldan Rico
- Ethan John Bickel
