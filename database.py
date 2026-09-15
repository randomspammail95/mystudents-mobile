"""
SQLite data layer for the MyStudents mobile app.

Identical schema and functions to the desktop app's data layer, so the two
stay compatible if you ever want to import/export between them — this is a
separate, standalone project with its own database file on the phone.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _app_dir() -> Path:
    """Where the database file lives: the app's private data directory on
    Android (and desktop, when testing), provided by Kivy's App class."""
    try:
        from kivy.app import App

        app = App.get_running_app()
        if app is not None:
            return Path(app.user_data_dir)
    except Exception:
        pass
    return Path(__file__).resolve().parent


APP_DIR = _app_dir()
DB_PATH = APP_DIR / "mystudents.db"

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ATTENDANCE_STATUSES = ["Present", "Absent", "Late", "Excused"]
PAYMENT_METHODS = ["Cash", "Bank Transfer", "Mobile Money", "Cheque", "Other"]


def get_connection() -> sqlite3.Connection:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                guardian_name TEXT,
                phone TEXT,
                email TEXT,
                level TEXT,
                subjects TEXT,
                monthly_fee REAL NOT NULL DEFAULT 0,
                date_joined TEXT,
                notes TEXT,
                active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                day_of_week TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                subject TEXT,
                location TEXT,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                session_date TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                period TEXT,
                method TEXT,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Students
# --------------------------------------------------------------------------- #

@dataclass
class Student:
    id: int
    full_name: str
    guardian_name: str
    phone: str
    email: str
    level: str
    subjects: str
    monthly_fee: float
    date_joined: str
    notes: str
    active: bool

    @staticmethod
    def from_row(row: sqlite3.Row) -> "Student":
        return Student(
            id=row["id"],
            full_name=row["full_name"],
            guardian_name=row["guardian_name"] or "",
            phone=row["phone"] or "",
            email=row["email"] or "",
            level=row["level"] or "",
            subjects=row["subjects"] or "",
            monthly_fee=row["monthly_fee"] or 0.0,
            date_joined=row["date_joined"] or "",
            notes=row["notes"] or "",
            active=bool(row["active"]),
        )


def add_student(**fields) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO students
               (full_name, guardian_name, phone, email, level, subjects, monthly_fee, date_joined, notes, active)
               VALUES (:full_name, :guardian_name, :phone, :email, :level, :subjects, :monthly_fee, :date_joined, :notes, :active)""",
            fields,
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_student(student_id: int, **fields) -> None:
    conn = get_connection()
    try:
        fields["id"] = student_id
        conn.execute(
            """UPDATE students SET
                 full_name = :full_name,
                 guardian_name = :guardian_name,
                 phone = :phone,
                 email = :email,
                 level = :level,
                 subjects = :subjects,
                 monthly_fee = :monthly_fee,
                 date_joined = :date_joined,
                 notes = :notes,
                 active = :active
               WHERE id = :id""",
            fields,
        )
        conn.commit()
    finally:
        conn.close()


def delete_student(student_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
    finally:
        conn.close()


def get_students(search: Optional[str] = None, active_only: bool = False) -> list[Student]:
    conn = get_connection()
    try:
        query = "SELECT * FROM students"
        clauses = []
        params: list = []
        if search:
            clauses.append("(full_name LIKE ? OR guardian_name LIKE ? OR subjects LIKE ? OR level LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like, like, like])
        if active_only:
            clauses.append("active = 1")
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY full_name COLLATE NOCASE"
        rows = conn.execute(query, params).fetchall()
        return [Student.from_row(r) for r in rows]
    finally:
        conn.close()


def get_student(student_id: int) -> Optional[Student]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        return Student.from_row(row) if row else None
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Schedule
# --------------------------------------------------------------------------- #

def add_schedule_entry(**fields) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO schedule (student_id, day_of_week, start_time, end_time, subject, location, notes)
               VALUES (:student_id, :day_of_week, :start_time, :end_time, :subject, :location, :notes)""",
            fields,
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_schedule_entry(entry_id: int, **fields) -> None:
    conn = get_connection()
    try:
        fields["id"] = entry_id
        conn.execute(
            """UPDATE schedule SET
                 student_id = :student_id,
                 day_of_week = :day_of_week,
                 start_time = :start_time,
                 end_time = :end_time,
                 subject = :subject,
                 location = :location,
                 notes = :notes
               WHERE id = :id""",
            fields,
        )
        conn.commit()
    finally:
        conn.close()


def delete_schedule_entry(entry_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM schedule WHERE id = ?", (entry_id,))
        conn.commit()
    finally:
        conn.close()


def get_schedule(student_id: Optional[int] = None, day_of_week: Optional[str] = None) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        query = """SELECT schedule.*, students.full_name AS student_name
                   FROM schedule JOIN students ON students.id = schedule.student_id"""
        clauses = []
        params: list = []
        if student_id is not None:
            clauses.append("schedule.student_id = ?")
            params.append(student_id)
        if day_of_week is not None:
            clauses.append("schedule.day_of_week = ?")
            params.append(day_of_week)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += """ ORDER BY CASE day_of_week
                       WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
                       WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
                       ELSE 7 END, start_time"""
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def get_schedule_counts_by_day() -> dict:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT day_of_week, COUNT(*) AS c FROM schedule GROUP BY day_of_week"
        ).fetchall()
        counts = {day: 0 for day in DAYS_OF_WEEK}
        for row in rows:
            if row["day_of_week"] in counts:
                counts[row["day_of_week"]] = row["c"]
        return counts
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Attendance
# --------------------------------------------------------------------------- #

def mark_attendance(student_id: int, session_date: str, status: str, notes: str = "") -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO attendance (student_id, session_date, status, notes) VALUES (?, ?, ?, ?)",
            (student_id, session_date, status, notes),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete_attendance(entry_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM attendance WHERE id = ?", (entry_id,))
        conn.commit()
    finally:
        conn.close()


def get_attendance(student_id: int, start: Optional[str] = None, end: Optional[str] = None) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        query = "SELECT * FROM attendance WHERE student_id = ?"
        params: list = [student_id]
        if start:
            query += " AND session_date >= ?"
            params.append(start)
        if end:
            query += " AND session_date <= ?"
            params.append(end)
        query += " ORDER BY session_date DESC"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def get_attendance_summary(student_id: int, start: Optional[str] = None, end: Optional[str] = None) -> dict:
    rows = get_attendance(student_id, start, end)
    total = len(rows)
    counts = {status: 0 for status in ATTENDANCE_STATUSES}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    present_like = counts.get("Present", 0) + counts.get("Late", 0)
    percent = round((present_like / total) * 100, 1) if total else 0.0
    return {"total": total, "counts": counts, "attendance_rate": percent}


# --------------------------------------------------------------------------- #
# Payments
# --------------------------------------------------------------------------- #

def add_payment(**fields) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO payments (student_id, amount, payment_date, period, method, notes)
               VALUES (:student_id, :amount, :payment_date, :period, :method, :notes)""",
            fields,
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete_payment(payment_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
        conn.commit()
    finally:
        conn.close()


def get_payments(student_id: int, start: Optional[str] = None, end: Optional[str] = None) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        query = "SELECT * FROM payments WHERE student_id = ?"
        params: list = [student_id]
        if start:
            query += " AND payment_date >= ?"
            params.append(start)
        if end:
            query += " AND payment_date <= ?"
            params.append(end)
        query += " ORDER BY payment_date DESC"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def get_total_paid(student_id: int, period: Optional[str] = None) -> float:
    conn = get_connection()
    try:
        query = "SELECT COALESCE(SUM(amount), 0) AS total FROM payments WHERE student_id = ?"
        params: list = [student_id]
        if period:
            query += " AND period = ?"
            params.append(period)
        row = conn.execute(query, params).fetchone()
        return float(row["total"])
    finally:
        conn.close()


def get_payment_status(period: str, search: Optional[str] = None) -> list[dict]:
    students = get_students(search=search, active_only=True)
    results = []
    for student in students:
        paid = get_total_paid(student.id, period=period)
        if student.monthly_fee <= 0 or paid >= student.monthly_fee:
            status = "Paid"
        elif paid > 0:
            status = "Partial"
        else:
            status = "Unpaid"
        results.append(
            {
                "student": student,
                "paid": paid,
                "outstanding": max(student.monthly_fee - paid, 0.0),
                "status": status,
            }
        )
    return results


# --------------------------------------------------------------------------- #
# Dashboard helpers
# --------------------------------------------------------------------------- #

def get_dashboard_stats() -> dict:
    conn = get_connection()
    try:
        total_students = conn.execute("SELECT COUNT(*) AS c FROM students WHERE active = 1").fetchone()["c"]
        total_sessions = conn.execute("SELECT COUNT(*) AS c FROM schedule").fetchone()["c"]
        month_prefix = _current_month_prefix()
        paid_this_month = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM payments WHERE period = ?", (month_prefix,)
        ).fetchone()["s"]
        expected_this_month = conn.execute(
            "SELECT COALESCE(SUM(monthly_fee), 0) AS s FROM students WHERE active = 1"
        ).fetchone()["s"]
        outstanding = max(float(expected_this_month) - float(paid_this_month), 0.0)
        return {
            "total_students": total_students,
            "weekly_sessions": total_sessions,
            "expected_this_month": float(expected_this_month),
            "paid_this_month": float(paid_this_month),
            "outstanding_this_month": outstanding,
        }
    finally:
        conn.close()


def _current_month_prefix() -> str:
    from datetime import date

    return date.today().strftime("%Y-%m")
