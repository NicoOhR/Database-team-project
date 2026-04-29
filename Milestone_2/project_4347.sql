-- CS 4347 Database Systems
-- Team Project
-- Team name: Dubnium
-- Airline Database Script
-- Based on ER Diagram Figure 3.21
-- Database: project_4347

-- From Terminal, run the script:
-- cd project
-- mysql --local-infile=1 -u root -p < project_4347.sql

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
  Weekdays VARCHAR(50)
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
  Code VARCHAR(20),
  Amount DECIMAL(10,2),
  Restrictions VARCHAR(200),
  PRIMARY KEY (Flight_number, Code),
  FOREIGN KEY (Flight_number) REFERENCES FLIGHT(Number)
);

CREATE TABLE AIRPLANE_SEAT (
  Airplane_id VARCHAR(20) NOT NULL,
  Seat_no VARCHAR(5) NOT NULL,
  Seat_class VARCHAR(20),
  PRIMARY KEY (Airplane_id, Seat_no),
  FOREIGN KEY (Airplane_id) REFERENCES AIRPLANE(Airplane_id)
);

-- SEAT stores booked seats for a specific leg instance and starts empty.
CREATE TABLE SEAT (
  Flight_number VARCHAR(10) NOT NULL,
  Leg_no INT NOT NULL,
  Date DATE NOT NULL,
  Seat_no VARCHAR(5) NOT NULL,
  Customer_name VARCHAR(60),
  Cphone VARCHAR(20),
  PRIMARY KEY (Flight_number, Leg_no, Date, Seat_no),
  CONSTRAINT fk_seat_leg_instance
    FOREIGN KEY (Flight_number, Leg_no, Date)
    REFERENCES LEG_INSTANCE(Flight_number, Leg_no, Date)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

DELIMITER //

CREATE TRIGGER validate_seat_before_insert
BEFORE INSERT ON SEAT
FOR EACH ROW
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM LEG_INSTANCE li
    JOIN AIRPLANE_SEAT aps
      ON aps.Airplane_id = li.Airplane_id
     AND aps.Seat_no = NEW.Seat_no
    WHERE li.Flight_number = NEW.Flight_number
      AND li.Leg_no = NEW.Leg_no
      AND li.Date = NEW.Date
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Seat number is not valid for the assigned airplane';
  END IF;
END//

CREATE TRIGGER validate_seat_before_update
BEFORE UPDATE ON SEAT
FOR EACH ROW
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM LEG_INSTANCE li
    JOIN AIRPLANE_SEAT aps
      ON aps.Airplane_id = li.Airplane_id
     AND aps.Seat_no = NEW.Seat_no
    WHERE li.Flight_number = NEW.Flight_number
      AND li.Leg_no = NEW.Leg_no
      AND li.Date = NEW.Date
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Seat number is not valid for the assigned airplane';
  END IF;
END//

DELIMITER ;

LOAD DATA LOCAL INFILE 'data/AIRPORT.csv'
INTO TABLE AIRPORT
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'data/AIRPLANE_TYPE.csv'
INTO TABLE AIRPLANE_TYPE
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'data/AIRPLANE.csv'
INTO TABLE AIRPLANE
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'data/SEAT.csv'
INTO TABLE AIRPLANE_SEAT
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(Airplane_id, Seat_no, Seat_class);

LOAD DATA LOCAL INFILE 'data/CAN_LAND.csv'
INTO TABLE CAN_LAND
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'data/FLIGHT.csv'
INTO TABLE FLIGHT
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'data/FLIGHT_LEG.csv'
INTO TABLE FLIGHT_LEG
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'data/LEG_INSTANCE.csv'
INTO TABLE LEG_INSTANCE
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'data/FARE.csv'
INTO TABLE FARE
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

-- The booking table starts empty, so remaining capacity should match airplane capacity.
UPDATE LEG_INSTANCE li
JOIN AIRPLANE a ON a.Airplane_id = li.Airplane_id
SET li.No_of_avail_seats = a.Total_no_of_seats;
