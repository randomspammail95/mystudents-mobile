"""
MyStudents Mobile — Android companion app for tracking tuition students,
schedule, attendance and payments. A separate, standalone project from the
PyQt6 desktop app: its own codebase and its own database on the phone.
"""
from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel

import database as db
from attendance_screen import AttendanceScreen
from dashboard_screen import DashboardScreen
from payments_screen import PaymentHistoryScreen, PaymentsScreen
from reports_screen import ReportsScreen
from schedule_screen import ScheduleDayScreen, ScheduleFormScreen, ScheduleScreen
from students_screen import StudentFormScreen, StudentsScreen

MAIN_TABS = [
    ("dashboard", "Dashboard", "view-dashboard"),
    ("students", "Students", "account-group"),
    ("schedule", "Schedule", "calendar-clock"),
    ("attendance", "Attendance", "calendar-check"),
    ("payments", "Payments", "cash-multiple"),
    ("reports", "Reports", "file-document"),
]


class Root(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.history: list[str] = []

        # ---- top bar ----
        self.top_bar = BoxLayout(size_hint_y=None, height=dp(52), padding=(dp(4), 0))
        with self.top_bar.canvas.before:
            from kivy.graphics import Color, Rectangle

            Color(0.357, 0.357, 0.941, 1)
            self._bg_rect = Rectangle(pos=self.top_bar.pos, size=self.top_bar.size)
        self.top_bar.bind(pos=self._update_bg, size=self._update_bg)

        self.back_button = MDIconButton(icon="arrow-left", disabled=True, opacity=0)
        self.back_button.bind(on_release=lambda *_: self.go_back())
        self.top_bar.add_widget(self.back_button)

        self.title_label = MDLabel(text="Dashboard", bold=True)
        self.title_label.theme_text_color = "Custom"
        self.title_label.text_color = (1, 1, 1, 1)
        self.top_bar.add_widget(self.title_label)
        self.add_widget(self.top_bar)

        # ---- screen manager ----
        self.sm = MDScreenManager()
        self.sm.add_widget(DashboardScreen())
        self.sm.add_widget(StudentsScreen())
        self.sm.add_widget(StudentFormScreen())
        self.sm.add_widget(ScheduleScreen())
        self.sm.add_widget(ScheduleDayScreen())
        self.sm.add_widget(ScheduleFormScreen())
        self.sm.add_widget(AttendanceScreen())
        self.sm.add_widget(PaymentsScreen())
        self.sm.add_widget(PaymentHistoryScreen())
        self.sm.add_widget(ReportsScreen())
        self.add_widget(self.sm)

        # ---- bottom nav ----
        self.nav_buttons = {}
        self.bottom_nav = BoxLayout(size_hint_y=None, height=dp(58))
        with self.bottom_nav.canvas.before:
            from kivy.graphics import Color, Rectangle

            Color(0.96, 0.96, 0.98, 1)
            self._bottom_rect = Rectangle(pos=self.bottom_nav.pos, size=self.bottom_nav.size)
        self.bottom_nav.bind(pos=self._update_bottom_bg, size=self._update_bottom_bg)

        for name, title, icon in MAIN_TABS:
            btn = MDIconButton(icon=icon)
            btn.bind(on_release=lambda _btn, n=name, t=title: self.goto_tab(n, t))
            self.nav_buttons[name] = btn
            self.bottom_nav.add_widget(btn)
        self.add_widget(self.bottom_nav)

        self._set_active_tab("dashboard")

    def _update_bg(self, *_):
        self._bg_rect.pos = self.top_bar.pos
        self._bg_rect.size = self.top_bar.size

    def _update_bottom_bg(self, *_):
        self._bottom_rect.pos = self.bottom_nav.pos
        self._bottom_rect.size = self.bottom_nav.size

    def _set_active_tab(self, name: str) -> None:
        for tab_name, btn in self.nav_buttons.items():
            btn.theme_icon_color = "Custom" if tab_name == name else "Primary"
            btn.icon_color = (0.357, 0.357, 0.941, 1) if tab_name == name else (0.6, 0.6, 0.6, 1)

    def goto_tab(self, name: str, title: str) -> None:
        """Switch to one of the six main sections; clears the back-history."""
        self.history = []
        self.sm.current = name
        self.title_label.text = title
        self.back_button.disabled = True
        self.back_button.opacity = 0
        self._set_active_tab(name)

    def goto(self, name: str, title: str | None = None, push: bool = True) -> None:
        """Navigate to a sub-screen (form/detail), optionally remembering how to go back."""
        if push:
            self.history.append((self.sm.current, self.title_label.text))
        self.sm.current = name
        if title:
            self.title_label.text = title
        self.back_button.disabled = False
        self.back_button.opacity = 1

    def go_back(self) -> None:
        if not self.history:
            return
        prev_name, prev_title = self.history.pop()
        self.sm.current = prev_name
        self.title_label.text = prev_title
        if not self.history:
            self.back_button.disabled = True
            self.back_button.opacity = 0


class MyStudentsApp(MDApp):
    def build(self):
        self.title = "MyStudents"
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.theme_style = "Light"
        db.init_db()
        return Root()


if __name__ == "__main__":
    MyStudentsApp().run()
