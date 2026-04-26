-- CS 4347 Database Systems
-- Team Project
-- Team name: Dubnium
-- Airline Database Script
-- Based on ER Diagram Figure 3.21
-- Database: project_4347
--
-- Core tables below follow the airline ER design from Figure 3.21.
-- One auxiliary support table, AIRPLANE_SEAT, is added so the provided seat-layout
-- CSV can be loaded and seat numbers can be validated against the airplane
-- assigned to each leg instance.

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

-- Auxiliary seat-layout table loaded from the provided seat CSV.
CREATE TABLE AIRPLANE_SEAT (
  Airplane_id VARCHAR(20) NOT NULL,
  Seat_no VARCHAR(5) NOT NULL,
  Seat_class VARCHAR(20),
  PRIMARY KEY (Airplane_id, Seat_no),
  FOREIGN KEY (Airplane_id) REFERENCES AIRPLANE(Airplane_id)
);

-- SEAT records one booked seat assignment for one leg instance.
-- Together with Customer_name and Cphone, it stores the reservation data used
-- by the Milestone 2 host application.
CREATE TABLE SEAT (
  Flight_number VARCHAR(10) NOT NULL,
  Leg_no INT NOT NULL,
  Date DATE NOT NULL,
  Seat_no VARCHAR(5) NOT NULL,
  Customer_name VARCHAR(60) NOT NULL,
  Cphone VARCHAR(20) NOT NULL,
  PRIMARY KEY (Flight_number, Leg_no, Date, Seat_no),
  CONSTRAINT fk_seat_leg_instance
    FOREIGN KEY (Flight_number, Leg_no, Date)
    REFERENCES LEG_INSTANCE(Flight_number, Leg_no, Date)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

DELIMITER //

CREATE PROCEDURE sync_leg_instance_available_seats(
  IN p_flight_number VARCHAR(10),
  IN p_leg_no INT,
  IN p_date DATE
)
BEGIN
  UPDATE LEG_INSTANCE li
  SET No_of_avail_seats = (
    SELECT COUNT(*)
    FROM AIRPLANE_SEAT aps
    WHERE aps.Airplane_id = li.Airplane_id
  ) - (
    SELECT COUNT(*)
    FROM SEAT s
    WHERE s.Flight_number = li.Flight_number
      AND s.Leg_no = li.Leg_no
      AND s.Date = li.Date
  )
  WHERE li.Flight_number = p_flight_number
    AND li.Leg_no = p_leg_no
    AND li.Date = p_date;
END//

CREATE TRIGGER seat_before_insert
BEFORE INSERT ON SEAT
FOR EACH ROW
BEGIN
  DECLARE v_airplane_id VARCHAR(20);

  SET NEW.Seat_no = UPPER(TRIM(NEW.Seat_no));
  SET NEW.Customer_name = TRIM(NEW.Customer_name);
  SET NEW.Cphone = TRIM(NEW.Cphone);

  IF NEW.Customer_name = '' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Customer name cannot be empty.';
  END IF;

  IF NEW.Cphone NOT REGEXP '^[0-9]{10}$' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Phone number must be exactly 10 digits.';
  END IF;

  SET v_airplane_id = (
    SELECT Airplane_id
    FROM LEG_INSTANCE
    WHERE Flight_number = NEW.Flight_number
      AND Leg_no = NEW.Leg_no
      AND Date = NEW.Date
    LIMIT 1
  );

  IF v_airplane_id IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Reservation references a missing leg instance.';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM AIRPLANE_SEAT
    WHERE Airplane_id = v_airplane_id
      AND Seat_no = NEW.Seat_no
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Seat number is not valid for the airplane assigned to this leg instance.';
  END IF;
END//

CREATE TRIGGER seat_before_update
BEFORE UPDATE ON SEAT
FOR EACH ROW
BEGIN
  DECLARE v_airplane_id VARCHAR(20);

  SET NEW.Seat_no = UPPER(TRIM(NEW.Seat_no));
  SET NEW.Customer_name = TRIM(NEW.Customer_name);
  SET NEW.Cphone = TRIM(NEW.Cphone);

  IF NEW.Customer_name = '' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Customer name cannot be empty.';
  END IF;

  IF NEW.Cphone NOT REGEXP '^[0-9]{10}$' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Phone number must be exactly 10 digits.';
  END IF;

  SET v_airplane_id = (
    SELECT Airplane_id
    FROM LEG_INSTANCE
    WHERE Flight_number = NEW.Flight_number
      AND Leg_no = NEW.Leg_no
      AND Date = NEW.Date
    LIMIT 1
  );

  IF v_airplane_id IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Reservation references a missing leg instance.';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM AIRPLANE_SEAT
    WHERE Airplane_id = v_airplane_id
      AND Seat_no = NEW.Seat_no
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Seat number is not valid for the airplane assigned to this leg instance.';
  END IF;
END//

CREATE TRIGGER seat_after_insert
AFTER INSERT ON SEAT
FOR EACH ROW
BEGIN
  CALL sync_leg_instance_available_seats(NEW.Flight_number, NEW.Leg_no, NEW.Date);
END//

CREATE TRIGGER seat_after_delete
AFTER DELETE ON SEAT
FOR EACH ROW
BEGIN
  CALL sync_leg_instance_available_seats(OLD.Flight_number, OLD.Leg_no, OLD.Date);
END//

CREATE TRIGGER seat_after_update
AFTER UPDATE ON SEAT
FOR EACH ROW
BEGIN
  CALL sync_leg_instance_available_seats(OLD.Flight_number, OLD.Leg_no, OLD.Date);
  CALL sync_leg_instance_available_seats(NEW.Flight_number, NEW.Leg_no, NEW.Date);
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
