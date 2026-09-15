from __future__ import annotations

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen

import database as db
from common import button, card, icon_button, muted_label, section_label, text_field
from common import toast as _snack


def _app_root():
    return App.get_running_app().root


class StudentRow(BoxLayout):
    def __init__(self, student: db.Student, on_edit, on_delete, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, spacing=dp(4), **kwargs)
        self.padding = (dp(14), dp(10), dp(14), dp(10))
        c = card(padding=12, spacing=6)
        c.size_hint_y = None

        name_row = BoxLayout(size_hint_y=None, height=dp(28))
        name_label = section_label(student.full_name)
        name_label.font_style = "Title"
        name_label.role = "small"
        name_row.add_widget(name_label)
        status = muted_label("Active" if student.active else "Inactive")
        status.size_hint_x = None
        status.width = dp(70)
        name_row.add_widget(status)
        c.add_widget(name_row)

        detail = f"{student.level or 'No level set'} · {student.subjects or 'No subjects set'}"
        c.add_widget(muted_label(detail))
        c.add_widget(muted_label(f"Rs {student.monthly_fee:,.0f} / month  ·  {student.phone or 'no phone'}"))

        actions = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        actions.add_widget(button("Edit", on_edit, style="outlined"))
        actions.add_widget(button("Delete", on_delete, style="text"))
        c.add_widget(actions)

        self.add_widget(c)
        self.bind(minimum_height=self.setter("height"))
        c.bind(minimum_height=c.setter("height"))


class StudentsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "students"

        outer = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        top_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.search_field = text_field("Search students...")
        self.search_field.bind(text=lambda *_: self._reload())
        top_row.add_widget(self.search_field)
        top_row.add_widget(icon_button("plus", lambda: self._add()))
        outer.add_widget(top_row)

        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        outer.add_widget(scroll)

        self.add_widget(outer)

    def on_pre_enter(self, *args):
        self._reload()

    def _reload(self) -> None:
        search = self.search_field.text.strip()
        students = db.get_students(search=search or None)
        self.list_box.clear_widgets()
        if not students:
            self.list_box.add_widget(muted_label("No students yet. Tap + to add one."))
            return
        for student in students:
            row = StudentRow(
                student,
                on_edit=lambda s=student: self._edit(s),
                on_delete=lambda s=student: self._delete(s),
            )
            self.list_box.add_widget(row)

    def _add(self) -> None:
        form = _app_root().sm.get_screen("student_form")
        form.load(None)
        _app_root().goto("student_form", title="Add Student")

    def _edit(self, student: db.Student) -> None:
        form = _app_root().sm.get_screen("student_form")
        form.load(student)
        _app_root().goto("student_form", title="Edit Student")

    def _delete(self, student: db.Student) -> None:
        db.delete_student(student.id)
        _snack(f"Deleted {student.full_name}")
        self._reload()


class StudentFormScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "student_form"
        self.student: db.Student | None = None

        outer = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        scroll = ScrollView()
        form = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        scroll.add_widget(form)
        outer.add_widget(scroll)

        self.name_field = text_field("Full name*")
        self.guardian_field = text_field("Guardian name")
        self.phone_field = text_field("Phone")
        self.email_field = text_field("Email")
        self.level_field = text_field("Level (e.g. O Level)")
        self.subjects_field = text_field("Subjects")
        self.fee_field = text_field("Monthly fee (Rs)")
        self.fee_field.input_filter = "float"
        self.notes_field = text_field("Notes")

        for field in (
            self.name_field, self.guardian_field, self.phone_field, self.email_field,
            self.level_field, self.subjects_field, self.fee_field, self.notes_field,
        ):
            form.add_widget(field)

        button_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        button_row.add_widget(button("Save", self._save))
        button_row.add_widget(button("Cancel", self._cancel, style="outlined"))
        outer.add_widget(button_row)

        self.add_widget(outer)

    def load(self, student: db.Student | None) -> None:
        self.student = student
        self.name_field.text = student.full_name if student else ""
        self.guardian_field.text = student.guardian_name if student else ""
        self.phone_field.text = student.phone if student else ""
        self.email_field.text = student.email if student else ""
        self.level_field.text = student.level if student else ""
        self.subjects_field.text = student.subjects if student else ""
        self.fee_field.text = str(int(student.monthly_fee)) if student else ""
        self.notes_field.text = student.notes if student else ""

    def _save(self) -> None:
        if not self.name_field.text.strip():
            _snack("Please enter the student's full name.")
            return
        try:
            fee = float(self.fee_field.text or 0)
        except ValueError:
            fee = 0.0

        from datetime import date

        fields = dict(
            full_name=self.name_field.text.strip(),
            guardian_name=self.guardian_field.text.strip(),
            phone=self.phone_field.text.strip(),
            email=self.email_field.text.strip(),
            level=self.level_field.text.strip(),
            subjects=self.subjects_field.text.strip(),
            monthly_fee=fee,
            date_joined=self.student.date_joined if self.student else date.today().isoformat(),
            notes=self.notes_field.text.strip(),
            active=1,
        )
        if self.student:
            db.update_student(self.student.id, **fields)
            _snack("Student updated.")
        else:
            db.add_student(**fields)
            _snack("Student added.")

        _app_root().goto_tab("students", "Students")
        _app_root().sm.get_screen("students")._reload()

    def _cancel(self) -> None:
        _app_root().goto_tab("students", "Students")
