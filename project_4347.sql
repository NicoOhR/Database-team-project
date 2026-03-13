-- CS 4347 Database Systems
-- Team Project
-- Team name: Dubnium
-- Airline Database Script
-- Based on ER Diagram Figure 3.21
-- Database: project_4347

-- From Terminal, run the script:
-- mysql --local-infile=1 -u root -p < "/Users/kourosh/Desktop/4347 Database/project/project_4347.sql"

DROP DATABASE IF EXISTS project_4347;
CREATE DATABASE project_4347;
USE project_4347;

CREATE TABLE AIRPORT (
  Airport_code CHAR(3) PRIMARY KEY,
  Name VARCHAR(60),
  City VARCHAR(60),
  State VARCHAR(60)
);

CREATE TABLE AIRPLANE_TYPE (
  Type_name VARCHAR(40) PRIMARY KEY,
  Company VARCHAR(60),
  Max_seats INT
);

CREATE TABLE AIRPLANE (
  Airplane_id VARCHAR(20) PRIMARY KEY,
  Total_no_of_seats INT,
  Type_name VARCHAR(40),
  FOREIGN KEY (Type_name) REFERENCES AIRPLANE_TYPE(Type_name)
);

CREATE TABLE CAN_LAND (
  Airport_code CHAR(3),
  Type_name VARCHAR(40),
  PRIMARY KEY (Airport_code, Type_name),
  FOREIGN KEY (Airport_code) REFERENCES AIRPORT(Airport_code),
  FOREIGN KEY (Type_name) REFERENCES AIRPLANE_TYPE(Type_name)
);

CREATE TABLE FLIGHT (
  Number VARCHAR(10) PRIMARY KEY,
  Airline VARCHAR(60),
  Weekdays VARCHAR(20)
);

CREATE TABLE FLIGHT_LEG (
  Flight_number VARCHAR(10),
  Leg_no INT,
  Dep_airport_code CHAR(3),
  Arr_airport_code CHAR(3),
  Scheduled_dep_time TIME,
  Scheduled_arr_time TIME,
  PRIMARY KEY (Flight_number, Leg_no),
  FOREIGN KEY (Flight_number) REFERENCES FLIGHT(Number),
  FOREIGN KEY (Dep_airport_code) REFERENCES AIRPORT(Airport_code),
  FOREIGN KEY (Arr_airport_code) REFERENCES AIRPORT(Airport_code)
);

CREATE TABLE LEG_INSTANCE (
  Flight_number VARCHAR(10),
  Leg_no INT,
  Date DATE,
  No_of_avail_seats INT,
  Airplane_id VARCHAR(20),
  Dep_time TIME,
  Arr_time TIME,
  PRIMARY KEY (Flight_number, Leg_no, Date),
  FOREIGN KEY (Flight_number, Leg_no) REFERENCES FLIGHT_LEG(Flight_number, Leg_no),
  FOREIGN KEY (Airplane_id) REFERENCES AIRPLANE(Airplane_id)
);

CREATE TABLE FARE (
  Flight_number VARCHAR(10),
  Code VARCHAR(10),
  Amount DECIMAL(10,2),
  Restrictions VARCHAR(200),
  PRIMARY KEY (Flight_number, Code),
  FOREIGN KEY (Flight_number) REFERENCES FLIGHT(Number)
);

CREATE TABLE SEAT (
  Airplane_id VARCHAR(20),
  Seat_no VARCHAR(5),
  Class VARCHAR(20),
  PRIMARY KEY (Airplane_id, Seat_no),
  FOREIGN KEY (Airplane_id) REFERENCES AIRPLANE(Airplane_id)
);

-- RESERVATION relationship from Figure 3.21
-- No CSV file was provided for this table, so it is created but not loaded
CREATE TABLE RESERVATION (
  Flight_number   VARCHAR(10),
  Leg_no          INT,
  Date            DATE,
  Airplane_id     VARCHAR(20),
  Seat_no         VARCHAR(5),
  Customer_name   VARCHAR(60),
  Cphone          VARCHAR(20),
  PRIMARY KEY (Flight_number, Leg_no, Date, Airplane_id, Seat_no),
  FOREIGN KEY (Flight_number, Leg_no, Date)
    REFERENCES LEG_INSTANCE(Flight_number, Leg_no, Date),
  FOREIGN KEY (Airplane_id, Seat_no)
    REFERENCES SEAT(Airplane_id, Seat_no)
);

LOAD DATA LOCAL INFILE '/Users/kourosh/Desktop/4347 Database/project/TEAM PROJECT FILES/AIRPORT.csv'
INTO TABLE AIRPORT
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE '/Users/kourosh/Desktop/4347 Database/project/TEAM PROJECT FILES/AIRPLANE_TYPE.csv'
INTO TABLE AIRPLANE_TYPE
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE '/Users/kourosh/Desktop/4347 Database/project/TEAM PROJECT FILES/AIRPLANE.csv'
INTO TABLE AIRPLANE
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE '/Users/kourosh/Desktop/4347 Database/project/TEAM PROJECT FILES/CAN_LAND.csv'
INTO TABLE CAN_LAND
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE '/Users/kourosh/Desktop/4347 Database/project/TEAM PROJECT FILES/FLIGHT.csv'
INTO TABLE FLIGHT
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE '/Users/kourosh/Desktop/4347 Database/project/TEAM PROJECT FILES/FLIGHT_LEG.csv'
INTO TABLE FLIGHT_LEG
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE '/Users/kourosh/Desktop/4347 Database/project/TEAM PROJECT FILES/LEG_INSTANCE.csv'
INTO TABLE LEG_INSTANCE
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE '/Users/kourosh/Desktop/4347 Database/project/TEAM PROJECT FILES/FARE.csv'
INTO TABLE FARE
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE '/Users/kourosh/Desktop/4347 Database/project/TEAM PROJECT FILES/SEAT.csv'
INTO TABLE SEAT
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;