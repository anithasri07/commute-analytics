-- CommuteCo synthetic dataset: schema (SQLite / PostgreSQL compatible)
CREATE TABLE sites     (site_id INTEGER PRIMARY KEY, site_name TEXT, city TEXT);
CREATE TABLE vendors   (vendor_id INTEGER PRIMARY KEY, vendor_name TEXT);
CREATE TABLE employees (employee_id INTEGER PRIMARY KEY, site_id INTEGER REFERENCES sites,
                        department TEXT, shift_time TEXT);
CREATE TABLE trips     (trip_id INTEGER PRIMARY KEY, employee_id INTEGER REFERENCES employees,
                        site_id INTEGER REFERENCES sites, vendor_id INTEGER REFERENCES vendors,
                        trip_date DATE, shift_time TEXT, trip_type TEXT,      -- LOGIN / LOGOUT
                        cab_delay_min INTEGER,                                -- minutes late vs scheduled pickup (negative = early); NULL if cancelled early
                        distance_km REAL,
                        status TEXT);                                         -- COMPLETED / NO_SHOW / CANCELLED / CANCELLED_LATE
CREATE TABLE feedback  (feedback_id INTEGER PRIMARY KEY, trip_id INTEGER REFERENCES trips,
                        rating INTEGER, issue_category TEXT);
CREATE TABLE disputes  (dispute_id INTEGER PRIMARY KEY, trip_id INTEGER REFERENCES trips,
                        raised_at TIMESTAMP, resolved_at TIMESTAMP, outcome TEXT);  -- ACCEPTED / REJECTED
CREATE INDEX idx_trips_emp_date ON trips(employee_id, trip_date);
