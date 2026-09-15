from __future__ import annotations

import re

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen

import database as db
from common import button, card, muted_label, section_label, spinner, text_field
from common import toast as _snack

TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _app_root():
    return App.get_running_app().root


class DayCard(BoxLayout):
    def __init__(self, day: str, count: int, on_view, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, padding=(dp(14), dp(6), dp(14), dp(6)), **kwargs)
        c = card(padding=14, spacing=4)
        c.size_hint_y = None
        row = BoxLayout(size_hint_y=None, height=dp(32))
        title = section_label(day)
        title.font_style = "Title"
        title.role = "medium"
        row.add_widget(title)
        c.add_widget(row)
        count_text = "No sessions" if count == 0 else f"{count} session{'s' if count != 1 else ''}"
        c.add_widget(muted_label(count_text))
        c.add_widget(button(f"View Students ({count})" if count else "View Students", on_view, style="outlined"))
        self.add_widget(c)
        self.bind(minimum_height=self.setter("height"))
        c.bind(minimum_height=c.setter("height"))


class ScheduleScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "schedule"
        outer = BoxLayout(orientation="vertical", padding=dp(8))
        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        outer.add_widget(scroll)
        self.add_widget(outer)

    def on_pre_enter(self, *args):
        self._reload()

    def _reload(self) -> None:
        counts = db.get_schedule_counts_by_day()
        self.list_box.clear_widgets()
        for day in db.DAYS_OF_WEEK:
            self.list_box.add_widget(DayCard(day, counts.get(day, 0), on_view=lambda d=day: self._view(d)))

    def _view(self, day: str) -> None:
        day_screen = _app_root().sm.get_screen("schedule_day")
        day_screen.load(day)
        _app_root().goto("schedule_day", title=day)


class SessionRow(BoxLayout):
    def __init__(self, entry, on_edit, on_delete, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, padding=(dp(14), dp(6), dp(14), dp(6)), **kwargs)
        c = card(padding=12, spacing=6)
        c.size_hint_y = None
        title = section_label(entry["student_name"])
        title.font_style = "Title"
        title.role = "small"
        c.add_widget(title)
        c.add_widget(muted_label(f"{entry['start_time']} - {entry['end_time']}  ·  {entry['subject'] or 'No subject'}"))
        if entry["location"]:
            c.add_widget(muted_label(entry["location"]))
        actions = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        actions.add_widget(button("Edit", on_edit, style="outlined"))
        actions.add_widget(button("Delete", on_delete, style="text"))
        c.add_widget(actions)
        self.add_widget(c)
        self.bind(minimum_height=self.setter("height"))
        c.bind(minimum_height=c.setter("height"))


class ScheduleDayScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "schedule_day"
        self.day: str | None = None

        outer = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        add_row = BoxLayout(size_hint_y=None, height=dp(48), padding=(dp(8), 0))
        add_row.add_widget(button("+ Add Session", self._add))
        outer.add_widget(add_row)

        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        outer.add_widget(scroll)
        self.add_widget(outer)

    def load(self, day: str) -> None:
        self.day = day
        self._reload()

    def _reload(self) -> None:
        if not self.day:
            return
        entries = db.get_schedule(day_of_week=self.day)
        self.list_box.clear_widgets()
        if not entries:
            self.list_box.add_widget(muted_label("No sessions scheduled this day."))
            return
        for entry in entries:
            self.list_box.add_widget(
                SessionRow(entry, on_edit=lambda e=entry: self._edit(e), on_delete=lambda e=entry: self._delete(e))
            )

    def _add(self) -> None:
        form = _app_root().sm.get_screen("schedule_form")
        form.load(None, default_day=self.day)
        _app_root().goto("schedule_form", title="Add Session")

    def _edit(self, entry) -> None:
        form = _app_root().sm.get_screen("schedule_form")
        form.load(entry, default_day=self.day)
        _app_root().goto("schedule_form", title="Edit Session")

    def _delete(self, entry) -> None:
        db.delete_schedule_entry(entry["id"])
        _snack("Session removed.")
        self._reload()


class ScheduleFormScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "schedule_form"
        self.entry = None
        self.return_day: str | None = None

        outer = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        scroll = ScrollView()
        form = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        scroll.add_widget(form)
        outer.add_widget(scroll)

        form.add_widget(muted_label("Student"))
        self.student_spinner = spinner(["No students yet"])
        form.add_widget(self.student_spinner)

        form.add_widget(muted_label("Day"))
        self.day_spinner = spinner(db.DAYS_OF_WEEK)
        form.add_widget(self.day_spinner)

        self.start_field = text_field("Start time (HH:MM)")
        self.end_field = text_field("End time (HH:MM)")
        self.subject_field = text_field("Subject")
        self.location_field = text_field("Location")
        for field in (self.start_field, self.end_field, self.subject_field, self.location_field):
            form.add_widget(field)

        button_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        button_row.add_widget(button("Save", self._save))
        button_row.add_widget(button("Cancel", self._cancel, style="outlined"))
        outer.add_widget(button_row)
        self.add_widget(outer)

    def load(self, entry, default_day: str | None = None) -> None:
        self.entry = entry
        self.return_day = (entry["day_of_week"] if entry else default_day) or db.DAYS_OF_WEEK[0]

        students = db.get_students(active_only=True)
        self._students_by_name = {s.full_name: s.id for s in students}
        names = list(self._students_by_name.keys()) or ["Add a student first"]
        self.student_spinner.values = names
        if entry:
            match = next((s for s in students if s.id == entry["student_id"]), None)
            self.student_spinner.text = match.full_name if match else names[0]
        else:
            self.student_spinner.text = names[0]

        self.day_spinner.text = self.return_day
        self.start_field.text = entry["start_time"] if entry else "16:00"
        self.end_field.text = entry["end_time"] if entry else "17:00"
        self.subject_field.text = entry["subject"] if entry else ""
        self.location_field.text = entry["location"] if entry else ""

    def _save(self) -> None:
        student_id = self._students_by_name.get(self.student_spinner.text)
        if not student_id:
            _snack("Add a student first from the Students tab.")
            return
        start, end = self.start_field.text.strip(), self.end_field.text.strip()
        if not TIME_RE.match(start) or not TIME_RE.match(end):
            _snack("Enter times as HH:MM, e.g. 16:00")
            return
        if end <= start:
            _snack("End time must be after the start time.")
            return

        fields = dict(
            student_id=student_id,
            day_of_week=self.day_spinner.text,
            start_time=start,
            end_time=end,
            subject=self.subject_field.text.strip(),
            location=self.location_field.text.strip(),
            notes="",
        )
        if self.entry:
            db.update_schedule_entry(self.entry["id"], **fields)
            _snack("Session updated.")
        else:
            db.add_schedule_entry(**fields)
            _snack("Session added.")

        day_screen = _app_root().sm.get_screen("schedule_day")
        day_screen.load(self.day_spinner.text)
        _app_root().goto("schedule_day", title=self.day_spinner.text, push=False)

    def _cancel(self) -> None:
        day_screen = _app_root().sm.get_screen("schedule_day")
        day_screen.load(self.return_day)
        _app_root().goto("schedule_day", title=self.return_day, push=False)
