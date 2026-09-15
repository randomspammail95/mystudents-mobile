from __future__ import annotations

import re
from datetime import date

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen

import database as db
from common import button, card, muted_label, section_label, spinner, status_color, text_field
from common import toast as _snack

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class AttendanceRow(BoxLayout):
    def __init__(self, record, on_delete, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, padding=(dp(14), dp(4), dp(14), dp(4)), **kwargs)
        c = card(padding=10, spacing=4)
        c.size_hint_y = None
        row = BoxLayout(size_hint_y=None, height=dp(26))
        date_label = section_label(record["session_date"])
        date_label.font_style = "Body"
        date_label.role = "large"
        row.add_widget(date_label)
        status_label = section_label(record["status"])
        status_label.theme_text_color = "Custom"
        status_label.text_color = status_color(record["status"])
        status_label.size_hint_x = None
        status_label.width = dp(80)
        row.add_widget(status_label)
        c.add_widget(row)
        if record["notes"]:
            c.add_widget(muted_label(record["notes"]))
        c.add_widget(button("Delete", on_delete, style="text"))
        self.add_widget(c)
        self.bind(minimum_height=self.setter("height"))
        c.bind(minimum_height=c.setter("height"))


class AttendanceScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "attendance"
        self._records = []

        outer = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        outer.add_widget(muted_label("Student"))
        self.student_spinner = spinner(["No students yet"])
        self.student_spinner.bind(text=lambda *_: self._reload())
        outer.add_widget(self.student_spinner)

        form_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.date_field = text_field("Date (YYYY-MM-DD)", text=date.today().isoformat())
        form_row.add_widget(self.date_field)
        self.status_spinner = spinner(db.ATTENDANCE_STATUSES)
        form_row.add_widget(self.status_spinner)
        outer.add_widget(form_row)

        self.notes_field = text_field("Optional note")
        outer.add_widget(self.notes_field)
        outer.add_widget(button("Mark Attendance", self._mark))

        self.summary_label = muted_label("No attendance recorded yet.")
        outer.add_widget(self.summary_label)

        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        outer.add_widget(scroll)

        self.add_widget(outer)

    def on_pre_enter(self, *args):
        self._refresh_students()
        self._reload()

    def _refresh_students(self) -> None:
        students = db.get_students(active_only=True)
        self._students_by_name = {s.full_name: s.id for s in students}
        names = list(self._students_by_name.keys()) or ["No students yet"]
        current = self.student_spinner.text
        self.student_spinner.values = names
        if current not in names:
            self.student_spinner.text = names[0]

    def _current_student_id(self):
        return self._students_by_name.get(self.student_spinner.text)

    def _reload(self) -> None:
        student_id = self._current_student_id()
        self.list_box.clear_widgets()
        if not student_id:
            self.summary_label.text = "Add a student to start tracking attendance."
            self._records = []
            return
        self._records = db.get_attendance(student_id)
        if not self._records:
            self.list_box.add_widget(muted_label("No attendance recorded yet."))
        for record in self._records:
            self.list_box.add_widget(AttendanceRow(record, on_delete=lambda r=record: self._delete(r)))

        summary = db.get_attendance_summary(student_id)
        if summary["total"] == 0:
            self.summary_label.text = "No attendance recorded yet."
        else:
            self.summary_label.text = (
                f"Attendance rate: {summary['attendance_rate']}%  "
                f"({summary['counts'].get('Present', 0)} present, "
                f"{summary['counts'].get('Late', 0)} late, "
                f"{summary['counts'].get('Absent', 0)} absent, "
                f"{summary['counts'].get('Excused', 0)} excused)"
            )

    def _mark(self) -> None:
        student_id = self._current_student_id()
        if not student_id:
            _snack("Add a student first from the Students tab.")
            return
        if not DATE_RE.match(self.date_field.text.strip()):
            _snack("Enter the date as YYYY-MM-DD.")
            return
        db.mark_attendance(
            student_id=student_id,
            session_date=self.date_field.text.strip(),
            status=self.status_spinner.text,
            notes=self.notes_field.text.strip(),
        )
        self.notes_field.text = ""
        _snack("Attendance marked.")
        self._reload()

    def _delete(self, record) -> None:
        db.delete_attendance(record["id"])
        _snack("Entry removed.")
        self._reload()
