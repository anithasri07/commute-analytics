-- =====================================================================
-- CommuteCo commute analytics: business questions answered in SQL
-- Written for SQLite; notes show PostgreSQL equivalents where they differ.
-- =====================================================================

-- Q1. Overall health: trips, completion, no-show and cancellation rates by month
SELECT strftime('%Y-%m', trip_date)                                  AS month,
       COUNT(*)                                                      AS trips,
       ROUND(100.0 * SUM(status = 'COMPLETED')      / COUNT(*), 2)  AS completed_pct,
       ROUND(100.0 * SUM(status = 'NO_SHOW')        / COUNT(*), 2)  AS no_show_pct,
       ROUND(100.0 * SUM(status LIKE 'CANCELLED%')  / COUNT(*), 2)  AS cancelled_pct
FROM trips
GROUP BY month
ORDER BY month;

-- Q2. Which shifts have the highest no-show rate?
SELECT shift_time,
       COUNT(*)                                                AS trips,
       SUM(status = 'NO_SHOW')                                 AS no_shows,
       ROUND(100.0 * SUM(status = 'NO_SHOW') / COUNT(*), 2)   AS no_show_pct
FROM trips
GROUP BY shift_time
ORDER BY no_show_pct DESC;

-- Q3. Vendor scorecard: punctuality, no-shows and rider rating
SELECT v.vendor_name,
       COUNT(*)                                                               AS trips,
       ROUND(AVG(t.cab_delay_min), 1)                                         AS avg_delay_min,
       ROUND(100.0 * SUM(t.cab_delay_min <= 5) / COUNT(t.cab_delay_min), 1)   AS on_time_pct,   -- on time = within 5 min
       ROUND(100.0 * SUM(t.status = 'NO_SHOW') / COUNT(*), 2)                 AS no_show_pct,
       ROUND(AVG(f.rating), 2)                                                AS avg_rating
FROM trips t
JOIN vendors v       ON v.vendor_id = t.vendor_id
LEFT JOIN feedback f ON f.trip_id   = t.trip_id
GROUP BY v.vendor_name
ORDER BY on_time_pct;

-- Q4. How does cab delay affect rider rating?
SELECT CASE WHEN t.cab_delay_min <= 0  THEN '1. early / on time'
            WHEN t.cab_delay_min <= 5  THEN '2. 1-5 min late'
            WHEN t.cab_delay_min <= 10 THEN '3. 6-10 min late'
            WHEN t.cab_delay_min <= 20 THEN '4. 11-20 min late'
            ELSE                            '5. 20+ min late' END   AS delay_bucket,
       COUNT(*)                                                   AS rated_trips,
       ROUND(AVG(f.rating), 2)                                    AS avg_rating,
       ROUND(100.0 * SUM(f.rating <= 2) / COUNT(*), 1)            AS low_rating_pct
FROM feedback f
JOIN trips t ON t.trip_id = f.trip_id
GROUP BY delay_bucket
ORDER BY delay_bucket;

-- Q5. Do late cabs cause more no-shows?
SELECT CASE WHEN cab_delay_min > 10 THEN 'cab > 10 min late' ELSE 'cab within 10 min' END AS arrival,
       COUNT(*)                                                AS trips,
       ROUND(100.0 * SUM(status = 'NO_SHOW') / COUNT(*), 2)   AS no_show_pct
FROM trips
WHERE cab_delay_min IS NOT NULL
GROUP BY arrival;

-- Q6. No-show disputes by site: how often raised, how often the employee was right
SELECT s.site_name,
       SUM(t.status = 'NO_SHOW')                                              AS no_shows,
       COUNT(d.dispute_id)                                                    AS disputes,
       ROUND(100.0 * COUNT(d.dispute_id) / SUM(t.status = 'NO_SHOW'), 1)      AS dispute_rate_pct,
       ROUND(100.0 * SUM(d.outcome = 'ACCEPTED') / COUNT(d.dispute_id), 1)    AS accepted_pct
FROM trips t
JOIN sites s         ON s.site_id = t.site_id
LEFT JOIN disputes d ON d.trip_id = t.trip_id
GROUP BY s.site_name
ORDER BY accepted_pct DESC;

-- Q7. How long do disputes take to resolve? (median via window function)
WITH durations AS (
    SELECT (julianday(resolved_at) - julianday(raised_at)) * 24 AS hours   -- PostgreSQL: EXTRACT(EPOCH FROM resolved_at - raised_at)/3600
    FROM disputes
), ranked AS (
    SELECT hours,
           ROW_NUMBER() OVER (ORDER BY hours) AS rn,
           COUNT(*)     OVER ()               AS n
    FROM durations
)
SELECT ROUND(AVG(hours), 1)                                             AS median_hours,     -- PostgreSQL: PERCENTILE_CONT(0.5)
       (SELECT ROUND(100.0 * SUM(hours > 24) / COUNT(*), 1) FROM durations) AS over_24h_pct
FROM ranked
WHERE rn IN ((n + 1) / 2, (n + 2) / 2);

-- Q8. Employees at risk of a booking block: 3+ no-shows within any rolling 30 days
WITH ns AS (
    SELECT employee_id, trip_date,
           LAG(trip_date, 2) OVER (PARTITION BY employee_id ORDER BY trip_date) AS two_no_shows_ago
    FROM trips
    WHERE status = 'NO_SHOW'
)
SELECT COUNT(DISTINCT employee_id) AS employees_hit_3_in_30_days
FROM ns
WHERE julianday(trip_date) - julianday(two_no_shows_ago) <= 30;

-- Q9. Weekly trend of no-show rate with week-over-week change
WITH weekly AS (
    SELECT strftime('%Y-W%W', trip_date)                          AS week,
           ROUND(100.0 * SUM(status = 'NO_SHOW') / COUNT(*), 2)  AS no_show_pct
    FROM trips
    GROUP BY week
)
SELECT week, no_show_pct,
       ROUND(no_show_pct - LAG(no_show_pct) OVER (ORDER BY week), 2) AS wow_change
FROM weekly
ORDER BY week;

-- Q10. Cancellations by day of week
SELECT CASE strftime('%w', trip_date) WHEN '0' THEN 'Sun' WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue'
         WHEN '3' THEN 'Wed' WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri' ELSE 'Sat' END AS weekday,
       COUNT(*)                                                       AS trips,
       ROUND(100.0 * SUM(status LIKE 'CANCELLED%') / COUNT(*), 2)    AS cancelled_pct,
       ROUND(100.0 * SUM(status = 'CANCELLED_LATE') / COUNT(*), 2)   AS late_cancel_pct
FROM trips
GROUP BY strftime('%w', trip_date)
ORDER BY strftime('%w', trip_date);

-- Q11. Rider retention by first-ride month (cohort analysis)
-- NULL means that month is not in the data yet.
WITH first_ride AS (
    SELECT employee_id,
           CAST(strftime('%Y', MIN(trip_date)) AS INTEGER) * 12 + CAST(strftime('%m', MIN(trip_date)) AS INTEGER) AS cohort_idx,
           strftime('%Y-%m', MIN(trip_date)) AS cohort
    FROM trips GROUP BY employee_id
), activity AS (
    SELECT DISTINCT employee_id,
           CAST(strftime('%Y', trip_date) AS INTEGER) * 12 + CAST(strftime('%m', trip_date) AS INTEGER) AS month_idx
    FROM trips
), bounds AS (
    SELECT MAX(month_idx) AS last_idx FROM activity
), cohort_activity AS (
    SELECT f.employee_id, f.cohort, f.cohort_idx, a.month_idx - f.cohort_idx AS month_n
    FROM first_ride f JOIN activity a ON a.employee_id = f.employee_id
)
SELECT c.cohort,
       COUNT(DISTINCT CASE WHEN month_n = 0 THEN employee_id END) AS riders,
       CASE WHEN MAX(c.cohort_idx) + 1 <= b.last_idx THEN
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN month_n = 1 THEN employee_id END)
                        / COUNT(DISTINCT CASE WHEN month_n = 0 THEN employee_id END), 1) END AS month_1_retained_pct,
       CASE WHEN MAX(c.cohort_idx) + 2 <= b.last_idx THEN
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN month_n = 2 THEN employee_id END)
                        / COUNT(DISTINCT CASE WHEN month_n = 0 THEN employee_id END), 1) END AS month_2_retained_pct
FROM cohort_activity c CROSS JOIN bounds b
GROUP BY c.cohort
ORDER BY c.cohort;

-- Q12. Which vendors cause the most wrong no-show marks (disputes accepted)?
SELECT v.vendor_name,
       COUNT(*)                                                         AS accepted_disputes,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)               AS share_of_wrong_marks_pct,
       ROUND(100.0 * vt.trips / SUM(vt.trips) OVER (), 1)               AS share_of_trips_pct
FROM disputes d
JOIN trips t   ON t.trip_id   = d.trip_id
JOIN vendors v ON v.vendor_id = t.vendor_id
JOIN (SELECT vendor_id, COUNT(*) AS trips FROM trips GROUP BY vendor_id) vt ON vt.vendor_id = t.vendor_id
WHERE d.outcome = 'ACCEPTED'
GROUP BY v.vendor_name, vt.trips
ORDER BY accepted_disputes DESC;
