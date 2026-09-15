from __future__ import annotations

from datetime import date

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen

import database as db
from common import button, card, muted_label, section_label, spinner, status_color, text_field
from common import toast as _snack


def _app_root():
    return App.get_running_app().root


def _recent_periods(count: int = 13) -> list[str]:
    periods = []
    year, month = date.today().year, date.today().month
    for _ in range(count):
        periods.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return periods


class StatusRow(BoxLayout):
    def __init__(self, entry, on_history, on_log, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, padding=(dp(14), dp(4), dp(14), dp(4)), **kwargs)
        student = entry["student"]
        c = card(padding=12, spacing=4)
        c.size_hint_y = None

        row = BoxLayout(size_hint_y=None, height=dp(26))
        name = section_label(student.full_name)
        name.font_style = "Title"
        name.role = "small"
        row.add_widget(name)
        status_label = section_label(entry["status"])
        status_label.theme_text_color = "Custom"
        status_label.text_color = status_color(entry["status"])
        status_label.size_hint_x = None
        status_label.width = dp(80)
        row.add_widget(status_label)
        c.add_widget(row)

        c.add_widget(muted_label(f"Paid Rs {entry['paid']:,.0f} of Rs {student.monthly_fee:,.0f}"))
        if entry["outstanding"] > 0:
            c.add_widget(muted_label(f"Outstanding: Rs {entry['outstanding']:,.0f}"))

        actions = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        actions.add_widget(button("History", on_history, style="outlined"))
        actions.add_widget(button("Log Payment", on_log, style="text"))
        c.add_widget(actions)

        self.add_widget(c)
        self.bind(minimum_height=self.setter("height"))
        c.bind(minimum_height=c.setter("height"))


class PaymentsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "payments"
        self._rows = []

        outer = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        outer.add_widget(section_label("Log a Payment"))
        outer.add_widget(muted_label("Student"))
        self.log_student_spinner = spinner(["No students yet"])
        outer.add_widget(self.log_student_spinner)

        form_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.amount_field = text_field("Amount (Rs)")
        self.amount_field.input_filter = "float"
        form_row.add_widget(self.amount_field)
        self.date_field = text_field("Date (YYYY-MM-DD)", text=date.today().isoformat())
        form_row.add_widget(self.date_field)
        outer.add_widget(form_row)

        form_row2 = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.period_spinner = spinner(_recent_periods())
        form_row2.add_widget(self.period_spinner)
        self.method_spinner = spinner(db.PAYMENT_METHODS)
        form_row2.add_widget(self.method_spinner)
        outer.add_widget(form_row2)

        outer.add_widget(button("Add Payment", self._add_payment))

        outer.add_widget(section_label("Student Payment Status"))
        self.search_field = text_field("Search students...")
        self.search_field.bind(text=lambda *_: self._reload_status())
        outer.add_widget(self.search_field)

        filter_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.status_period_spinner = spinner(_recent_periods())
        self.status_period_spinner.bind(text=lambda *_: self._reload_status())
        filter_row.add_widget(self.status_period_spinner)
        self.filter_spinner = spinner(["All", "Paid", "Unpaid"])
        self.filter_spinner.bind(text=lambda *_: self._reload_status())
        filter_row.add_widget(self.filter_spinner)
        outer.add_widget(filter_row)

        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        outer.add_widget(scroll)

        self.add_widget(outer)

    def on_pre_enter(self, *args):
        self._refresh_students()
        self._reload_status()

    def _refresh_students(self) -> None:
        students = db.get_students(active_only=True)
        self._students_by_name = {s.full_name: s.id for s in students}
        names = list(self._students_by_name.keys()) or ["No students yet"]
        current = self.log_student_spinner.text
        self.log_student_spinner.values = names
        if current not in names:
            self.log_student_spinner.text = names[0]

    def _add_payment(self) -> None:
        student_id = self._students_by_name.get(self.log_student_spinner.text)
        if not student_id:
            _snack("Add a student first from the Students tab.")
            return
        try:
            amount = float(self.amount_field.text or 0)
        except ValueError:
            amount = 0.0
        if amount <= 0:
            _snack("Enter an amount greater than zero.")
            return
        db.add_payment(
            student_id=student_id,
            amount=amount,
            payment_date=self.date_field.text.strip() or date.today().isoformat(),
            period=self.period_spinner.text,
            method=self.method_spinner.text,
            notes="",
        )
        self.amount_field.text = ""
        _snack("Payment logged.")
        self._reload_status()

    def _reload_status(self) -> None:
        period = self.status_period_spinner.text or date.today().strftime("%Y-%m")
        search = self.search_field.text.strip() or None
        rows = db.get_payment_status(period=period, search=search)
        status_filter = self.filter_spinner.text
        if status_filter == "Paid":
            rows = [r for r in rows if r["status"] == "Paid"]
        elif status_filter == "Unpaid":
            rows = [r for r in rows if r["status"] in ("Unpaid", "Partial")]
        self._rows = rows

        self.list_box.clear_widgets()
        if not rows:
            self.list_box.add_widget(muted_label("No students match this search/filter."))
            return
        for entry in rows:
            self.list_box.add_widget(
                StatusRow(
                    entry,
                    on_history=lambda e=entry: self._view_history(e),
                    on_log=lambda e=entry: self._log_for(e),
                )
            )

    def _view_history(self, entry) -> None:
        history_screen = _app_root().sm.get_screen("payment_history")
        history_screen.load(entry["student"])
        _app_root().goto("payment_history", title=f"History — {entry['student'].full_name}")

    def _log_for(self, entry) -> None:
        name = entry["student"].full_name
        if name in self.log_student_spinner.values:
            self.log_student_spinner.text = name
        _snack(f"Ready to log a payment for {name} above.")


class PaymentHistoryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "payment_history"
        self.student: db.Student | None = None

        outer = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        outer.add_widget(scroll)
        self.add_widget(outer)

    def load(self, student: db.Student) -> None:
        self.student = student
        self._reload()

    def _reload(self) -> None:
        self.list_box.clear_widgets()
        payments = db.get_payments(self.student.id)
        if not payments:
            self.list_box.add_widget(muted_label("No payments recorded yet."))
            return
        for payment in payments:
            row = BoxLayout(orientation="vertical", size_hint_y=None, padding=(dp(4), dp(4)))
            c = card(padding=10, spacing=2)
            c.size_hint_y = None
            c.add_widget(section_label(f"Rs {payment['amount']:,.0f}  ·  {payment['payment_date']}"))
            c.add_widget(muted_label(f"{payment['period'] or ''}  ·  {payment['method'] or ''}"))
            c.add_widget(button("Delete", lambda p=payment: self._delete(p), style="text"))
            row.add_widget(c)
            row.bind(minimum_height=row.setter("height"))
            c.bind(minimum_height=c.setter("height"))
            self.list_box.add_widget(row)

    def _delete(self, payment) -> None:
        db.delete_payment(payment["id"])
        _snack("Payment removed.")
        self._reload()
