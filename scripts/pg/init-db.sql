CREATE TABLE pms_user (
	email VARCHAR(255) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_no VARCHAR(15),
    forename VARCHAR(255) NOT NULL,
    middlename VARCHAR(100) DEFAULT '',
    surname VARCHAR(100) NOT NULL,
    balance DECIMAL(26, 2) DEFAULT 0
);

CREATE TABLE team (
	team_name VARCHAR(512) PRIMARY KEY
);

CREATE TABLE swimmer (
	email VARCHAR(255) PRIMARY KEY,
  	number_of_sessions_attended INT DEFAULT 0,
  	member_of_team VARCHAR(512),
  	FOREIGN KEY (email) REFERENCES pms_user,
  	FOREIGN KEY (member_of_team) REFERENCES team
);

CREATE TABLE pms_admin (
	email VARCHAR(255) PRIMARY KEY,
  	FOREIGN KEY (email) REFERENCES pms_user
);

CREATE TABLE accessed_report_categories (
	email VARCHAR(255),
  	report_category VARCHAR(255),
  	PRIMARY KEY (email, report_category),
  	FOREIGN KEY (email) REFERENCES pms_admin
);

CREATE TABLE coach (
	email VARCHAR(255) PRIMARY KEY,
  	fee_per_hour DECIMAL(26, 2),
  	number_of_hours_thought INT DEFAULT 0,
  	years_of_experience INT DEFAULT 0,
	rating DECIMAL(3,2), -- Average coach rating
  	FOREIGN KEY (email) REFERENCES pms_user
);

CREATE TABLE lifeguard (
	email VARCHAR(255) PRIMARY KEY,
  	FOREIGN KEY (email) REFERENCES pms_user
);

CREATE TABLE work_days_of_the_week (
	email VARCHAR(255),
  	work_day VARCHAR(255),
  	PRIMARY KEY (email, work_day),
  	FOREIGN KEY (email) REFERENCES lifeguard,
  	CONSTRAINT chk_valid_work_day CHECK (work_day IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'))
);

CREATE TABLE non_member (
	email VARCHAR(255) PRIMARY KEY,
  	access_hours_start VARCHAR(5),
  	access_hours_end VARCHAR(5),
  	FOREIGN KEY (email) REFERENCES swimmer
);

CREATE TABLE pms_member (
	email VARCHAR(255) PRIMARY KEY,
  	membership_start_date DATE DEFAULT CURRENT_DATE,
  	membership_end_date DATE,
  	FOREIGN KEY (email) REFERENCES swimmer,
  	CONSTRAINT chk_member_date_order CHECK (membership_end_date >= membership_start_date)
);

CREATE TABLE pool (
	pool_id VARCHAR(255) PRIMARY KEY,
  	pool_city VARCHAR(100),
  	pool_name VARCHAR(255),
  	max_swimmers INT,
  	max_depth DECIMAL(10, 2),
  	min_depth DECIMAL(10, 2),
  	min_age INT,
  	CONSTRAINT chk_depth_order CHECK (max_depth >= min_depth)
);

CREATE TABLE lane (
	pool_id VARCHAR(255),
  	lane_id VARCHAR(255),
  	PRIMARY KEY (pool_id, lane_id),
  	FOREIGN KEY (pool_id) REFERENCES pool
);

CREATE TABLE report (
	report_id VARCHAR(255) PRIMARY KEY,
  	analysis_start_date DATE,
  	analysis_end_date DATE,
  	generated_by VARCHAR(255),
  	FOREIGN KEY (generated_by) REFERENCES pms_admin,
  	CONSTRAINT chk_report_date_order CHECK (analysis_end_date >= analysis_start_date)
);

CREATE TABLE session_report (
	report_id VARCHAR(255) PRIMARY KEY,
  	description VARCHAR(512),
  	no_of_total_sessions INT,
  	no_of_free_sessions INT,
  	no_of_one_to_one_sessions INT,
  	no_of_competitions INT,
  	no_of_class_sessions INT,
  	FOREIGN KEY (report_id) REFERENCES report
);

CREATE TABLE swimming_session (
	session_name VARCHAR(255),
  	session_date DATE,
  	start_hour TIME,
  	end_hour TIME,
  	price DECIMAL(26, 2) DEFAULT 0,
  	coach_email VARCHAR(255),
  	PRIMARY KEY (session_name, session_date, start_hour, end_hour),
	FOREIGN KEY (coach_email) REFERENCES coach,
  	CONSTRAINT chk_session_hours CHECK (end_hour >= start_hour)
);

CREATE TABLE race_report (
	report_id VARCHAR(255) PRIMARY KEY,
  	no_of_participants INT,
  	FOREIGN KEY (report_id) REFERENCES report
);

CREATE TABLE race (
	session_name VARCHAR(255),
  	session_date DATE,
  	start_hour TIME,
  	end_hour TIME,
  	age_group VARCHAR(100),
  	stroke_style VARCHAR(100),
  	report_id VARCHAR(255),
  	PRIMARY KEY (session_name, session_date, start_hour, end_hour),
  	FOREIGN KEY (report_id) REFERENCES race_report,
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session ON UPDATE CASCADE
);

CREATE TABLE employee_report (
	report_id VARCHAR(255) PRIMARY KEY,
  	days_lifeguards_worked INT,
  	hours_coaches_worked INT,
  	FOREIGN KEY (report_id) REFERENCES report
);

CREATE TABLE benefit (
	benefit_id VARCHAR(255) PRIMARY KEY,
  	start_date DATE,
  	end_date DATE,
  	swimmer_email VARCHAR(255),
  	FOREIGN KEY (swimmer_email) REFERENCES swimmer
);

CREATE TABLE free_session (
	benefit_id VARCHAR(255) PRIMARY KEY,
  	number_of_sesions INT,
  	session_type VARCHAR(255),
  	FOREIGN KEY (benefit_id) REFERENCES benefit
);

CREATE TABLE free_membership (
	benefit_id VARCHAR(255) PRIMARY KEY,
  	number_of_months INT,
  	FOREIGN KEY (benefit_id) REFERENCES benefit
);

CREATE TABLE individual_session (
	session_name VARCHAR(255),
  	session_date DATE,
  	start_hour TIME,
  	end_hour TIME,
  	number_of_months INT,
  	PRIMARY KEY (session_name, session_date, start_hour, end_hour),
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session ON UPDATE CASCADE
);

CREATE TABLE class_session (
	session_name VARCHAR(255),
  	session_date DATE,
  	start_hour TIME,
  	end_hour TIME,
  	age_group VARCHAR(100),
  	number_of_participants INT,
  	max_capacity INT,
  	class_level VARCHAR(255),
  	signup_date DATE,
  	PRIMARY KEY (session_name, session_date, start_hour, end_hour),
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session ON UPDATE CASCADE
);

CREATE TABLE one_to_one_session (
	session_name VARCHAR(255),
  	session_date DATE,
  	start_hour TIME,
  	end_hour TIME,
  	special_request_comment VARCHAR(512),
  	PRIMARY KEY (session_name, session_date, start_hour, end_hour),
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session ON UPDATE CASCADE
);

CREATE TABLE lifeguard_watch (
	email VARCHAR(255),
  	pool_id VARCHAR(255),
  	watch_date DATE,
  	time_slot VARCHAR(5),
  	PRIMARY KEY (email, pool_id),
  	FOREIGN KEY (email) REFERENCES lifeguard,
  	FOREIGN KEY (pool_id) REFERENCES pool
);

CREATE TABLE swimmer_attend_session (
	email VARCHAR(255),
  	session_name VARCHAR(255),
  	session_date DATE,
  	start_hour TIME,
  	end_hour TIME,
  	PRIMARY KEY (email, session_name, session_date, start_hour, end_hour),
  	FOREIGN KEY (email) REFERENCES swimmer,
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session ON UPDATE CASCADE
);

CREATE TABLE booking (
	pool_id VARCHAR(255),
  	lane_id VARCHAR(255),
  	session_name VARCHAR(255),
  	session_date DATE,
  	start_hour TIME,
  	end_hour TIME,
  	PRIMARY KEY (pool_id, lane_id, session_name, session_date, start_hour, end_hour),
  	FOREIGN KEY (pool_id, lane_id) REFERENCES lane,
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session ON UPDATE CASCADE
);

CREATE TABLE team_attend_race (
	team_name VARCHAR(512),
  	session_name VARCHAR(255),
  	session_date DATE,
  	start_hour TIME,
  	end_hour TIME,
  	PRIMARY KEY (team_name, session_name, session_date, start_hour, end_hour),
  	FOREIGN KEY (team_name) REFERENCES team,
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session ON UPDATE CASCADE
);

<<<<<<< Updated upstream
-- Populating Database --

-- Password is '123'
INSERT INTO pms_user (email, username, password_hash, phone_no, forename, surname, balance) VALUES
('c@c.com', 'coach1', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', '+901234567890', 'Coach', 'Smith', 1000.00),
('s@s.com', 'swimmer1', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', '+901234567891', 'Sam', 'Johnson', 500.00),
('n@n.com', 'nonmember1', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', '+901234567892', 'Ian', 'Brown', 0.00),
('l@l.com', 'lifeguard1', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', '+901234567893', 'Lisa', 'Guard', 800.00);

-- Specialized users
INSERT INTO coach (email, fee_per_hour, years_of_experience) VALUES
('c@c.com', 100.00, 5);

INSERT INTO team (team_name) VALUES
('Dolphins'),
('Sharks');

INSERT INTO swimmer (email, number_of_sessions_attended, member_of_team) VALUES
('s@s.com', 10, 'Dolphins'),
('n@n.com', 2, NULL);

INSERT INTO lifeguard (email) VALUES
('l@l.com');

INSERT INTO work_days_of_the_week (email, work_day) VALUES
('l@l.com', 'Monday'),
('l@l.com', 'Wednesday'),
('l@l.com', 'Friday');

INSERT INTO pms_member (email, membership_start_date, membership_end_date) VALUES
('s@s.com', '2024-01-01', '2024-12-31');

INSERT INTO non_member (email, access_hours_start, access_hours_end) VALUES
('n@n.com', '09:00', '17:00');

-- Pools and lanes
INSERT INTO pool (pool_id, pool_city, pool_name, max_swimmers, max_depth, min_depth, min_age) VALUES
('P1', 'Ankara', 'Main Pool', 50, 3.0, 1.2, 5),
('P2', 'Ankara', 'Training Pool', 30, 2.0, 1.0, 3);

INSERT INTO lane (pool_id, lane_id) VALUES
('P1', 'L1'),
('P1', 'L2'),
('P2', 'L1');

-- Create sessions
INSERT INTO swimming_session (session_name, session_date, start_hour, end_hour, price, coach_email) VALUES
('Class-Beginner', '2024-03-15', '10:00', '11:00', 50.00, 'c@c.com'),
('Individual-Program', '2024-03-15', '12:00', '13:00', 75.00, 'c@c.com'),
('OneToOne-Special', '2024-03-15', '14:00', '15:00', 100.00, 'c@c.com'),
('Race-Freestyle', '2024-03-16', '16:00', '17:00', 25.00, 'c@c.com');

INSERT INTO class_session (session_name, session_date, start_hour, end_hour, age_group, number_of_participants, max_capacity, class_level, signup_date) VALUES
('Class-Beginner', '2024-03-15', '10:00', '11:00', '7-12', 5, 10, 'Beginner', '2024-03-01');

INSERT INTO individual_session (session_name, session_date, start_hour, end_hour, number_of_months) VALUES
('Individual-Program', '2024-03-15', '12:00', '13:00', 3);

INSERT INTO one_to_one_session (session_name, session_date, start_hour, end_hour, special_request_comment) VALUES
('OneToOne-Special', '2024-03-15', '14:00', '15:00', 'Focus on butterfly technique');

INSERT INTO race (session_name, session_date, start_hour, end_hour, age_group, stroke_style) VALUES
('Race-Freestyle', '2024-03-16', '16:00', '17:00', 'Adult', 'Freestyle');

-- Bookings and attendances
INSERT INTO booking (pool_id, lane_id, session_name, session_date, start_hour, end_hour) VALUES
('P1', 'L1', 'Class-Beginner', '2024-03-15', '10:00', '11:00'),
('P1', 'L2', 'Race-Freestyle', '2024-03-16', '16:00', '17:00');

INSERT INTO swimmer_attend_session (email, session_name, session_date, start_hour, end_hour) VALUES
('s@s.com', 'Class-Beginner', '2024-03-15', '10:00', '11:00'),
('s@s.com', 'Individual-Program', '2024-03-15', '12:00', '13:00');

-- Benefits
INSERT INTO benefit (benefit_id, start_date, end_date, swimmer_email) VALUES
('B1', '2024-03-01', '2024-06-01', 's@s.com');
=======
CREATE TABLE coach_rating (
	id SERIAL PRIMARY KEY,
	coach_email VARCHAR(255) NOT NULL REFERENCES coach(email) ON DELETE CASCADE,
	swimmer_email VARCHAR(255) NOT NULL REFERENCES swimmer(email) ON DELETE CASCADE,
	session_name VARCHAR(255) NOT NULL,
    session_date DATE NOT NULL,
    start_hour TIME NOT NULL,
    end_hour TIME NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    UNIQUE (coach_email, swimmer_email, session_name, session_date, start_hour, end_hour)
);

-- Trigger function to update the coach's average rating
CREATE OR REPLACE FUNCTION update_coach_average_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE coach
    SET rating = (
        SELECT AVG(rating)::DECIMAL(3,2)
        FROM coach_rating
        WHERE coach_email = NEW.coach_email
    )
    WHERE email = NEW.coach_email;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for INSERT on coach_rating
CREATE TRIGGER trg_update_coach_rating_insert
AFTER INSERT ON coach_rating
FOR EACH ROW
EXECUTE FUNCTION update_coach_average_rating();

-- Trigger for UPDATE on coach_rating
CREATE TRIGGER trg_update_coach_rating_update
AFTER UPDATE ON coach_rating
FOR EACH ROW
EXECUTE FUNCTION update_coach_average_rating();
>>>>>>> Stashed changes
