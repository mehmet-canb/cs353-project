CREATE TABLE pms_user (
	email VARCHAR(255) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_no VARCHAR(15),
    forename VARCHAR(255) NOT NULL,
    middlename VARCHAR(100) NOT NULL,
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
  	price DECIMAL(26, 2),
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
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session
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
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session
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
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session
);

CREATE TABLE one_to_one_session (
	session_name VARCHAR(255),
  	session_date DATE,
  	start_hour TIME,
  	end_hour TIME,
  	special_request_comment VARCHAR(512),
  	PRIMARY KEY (session_name, session_date, start_hour, end_hour),
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session
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
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session
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
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session
);

CREATE TABLE team_attend_race (
	team_name VARCHAR(512),
  	session_name VARCHAR(255),
  	session_date DATE,
  	start_hour TIME,
  	end_hour TIME,
  	PRIMARY KEY (team_name, session_name, session_date, start_hour, end_hour),
  	FOREIGN KEY (team_name) REFERENCES team,
  	FOREIGN KEY (session_name, session_date, start_hour, end_hour) REFERENCES swimming_session
);
