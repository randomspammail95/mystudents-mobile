from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.screen import MDScreen

import database as db
from common import card, muted_label, section_label


def make_stat_card(label: str, value: str):
    c = card(padding=16, spacing=4)
    value_label = section_label(value)
    value_label.font_style = "Headline"
    value_label.role = "small"
    c.add_widget(value_label)
    c.add_widget(muted_label(label.upper()))
    return c, value_label


class DashboardScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "dashboard"

        root = GridLayout(cols=2, spacing=dp(12), padding=dp(16), size_hint_y=None)
        root.bind(minimum_height=root.setter("height"))

        from kivy.uix.scrollview import ScrollView

        scroll = ScrollView()
        scroll.add_widget(root)
        self.add_widget(scroll)

        self.students_card, self.students_value = make_stat_card("Active Students", "0")
        self.sessions_card, self.sessions_value = make_stat_card("Weekly Sessions", "0")
        self.expected_card, self.expected_value = make_stat_card("Expected This Month", "Rs 0")
        self.outstanding_card, self.outstanding_value = make_stat_card("Outstanding", "Rs 0")

        for c in (self.students_card, self.sessions_card, self.expected_card, self.outstanding_card):
            c.size_hint_x = 1
            root.add_widget(c)

    def on_pre_enter(self, *args):
        stats = db.get_dashboard_stats()
        self.students_value.text = str(stats["total_students"])
        self.sessions_value.text = str(stats["weekly_sessions"])
        self.expected_value.text = f"Rs {stats['expected_this_month']:,.0f}"
        self.outstanding_value.text = f"Rs {stats['outstanding_this_month']:,.0f}"
