from __future__ import annotations

from datetime import date, timedelta

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen

import database as db
from common import button, card, muted_label, section_label, spinner, text_field


class ReportsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "reports"

        outer = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        outer.add_widget(muted_label("Student"))
        self.student_spinner = spinner(["No students yet"])
        outer.add_widget(self.student_spinner)

        form_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.from_field = text_field("From (YYYY-MM-DD)", text=(date.today() - timedelta(days=30)).isoformat())
        form_row.add_widget(self.from_field)
        self.to_field = text_field("To (YYYY-MM-DD)", text=date.today().isoformat())
        form_row.add_widget(self.to_field)
        outer.add_widget(form_row)

        self.comments_field = text_field("Comments for parent (optional)")
        outer.add_widget(self.comments_field)

        outer.add_widget(button("Generate Report", self._generate))

        self.report_card = card(padding=16, spacing=8)
        self.report_card.size_hint_y = None
        self.report_label = section_label("Select a student and tap Generate Report.")
        self.report_label.font_style = "Body"
        self.report_label.role = "medium"
        self.report_label.text_size = (None, None)
        self.report_card.add_widget(self.report_label)

        scroll = ScrollView()
        scroll.add_widget(self.report_card)
        outer.add_widget(scroll)

        self.add_widget(outer)

        note = muted_label(
            "Note: this mobile app shows the report on screen. For a PDF you can print or email, "
            "generate it from the desktop app's Reports page."
        )
        outer.add_widget(note)

    def on_pre_enter(self, *args):
        students = db.get_students(active_only=True)
        self._students_by_name = {s.full_name: s.id for s in students}
        names = list(self._students_by_name.keys()) or ["No students yet"]
        self.student_spinner.values = names
        if self.student_spinner.text not in names:
            self.student_spinner.text = names[0]

    def _generate(self) -> None:
        student_id = self._students_by_name.get(self.student_spinner.text)
        if not student_id:
            self.report_label.text = "Add a student first from the Students tab."
            return
        student = db.get_student(student_id)
        start = self.from_field.text.strip()
        end = self.to_field.text.strip()

        summary = db.get_attendance_summary(student_id, start=start, end=end)
        payments = db.get_payments(student_id, start=start, end=end)
        total_paid = sum(p["amount"] for p in payments)
        current_period = date.today().strftime("%Y-%m")
        paid_this_period = db.get_total_paid(student_id, period=current_period)
        outstanding = max(student.monthly_fee - paid_this_period, 0.0)
        comments = self.comments_field.text.strip()

        lines = [
            f"[b]{student.full_name}[/b]",
            f"Level: {student.level or '-'}   Subjects: {student.subjects or '-'}",
            f"Period: {start} to {end}",
            "",
            "[b]Attendance[/b]",
            f"Attendance rate: {summary['attendance_rate']}%",
            f"Present: {summary['counts'].get('Present', 0)}   "
            f"Late: {summary['counts'].get('Late', 0)}   "
            f"Absent: {summary['counts'].get('Absent', 0)}   "
            f"Excused: {summary['counts'].get('Excused', 0)}",
            "",
            "[b]Payments[/b]",
            f"Total paid in period: Rs {total_paid:,.0f}",
            f"Outstanding for {current_period}: Rs {outstanding:,.0f}",
        ]
        if comments:
            lines += ["", "[b]Comments[/b]", comments]

        self.report_label.markup = True
        self.report_label.text = "\n".join(lines)
