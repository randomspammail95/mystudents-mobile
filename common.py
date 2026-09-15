"""Small shared UI helpers used across every screen."""
from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

ACCENT_HEX = "5b5bf0"
SUCCESS_HEX = "1fa971"
WARNING_HEX = "d98a26"
DANGER_HEX = "e0435a"
MUTED_HEX = "6b7086"


def button(text: str, on_press=None, style: str = "filled") -> MDButton:
    btn = MDButton(MDButtonText(text=text), style=style, size_hint_x=None)
    btn.width = dp(max(90, 14 * len(text)))
    if on_press:
        btn.bind(on_release=lambda *_: on_press())
    return btn


def icon_button(icon: str, on_press=None) -> MDIconButton:
    btn = MDIconButton(icon=icon)
    if on_press:
        btn.bind(on_release=lambda *_: on_press())
    return btn


def text_field(hint: str, text: str = "", password: bool = False) -> MDTextField:
    field = MDTextField(MDTextFieldHintText(text=hint), text=text, password=password)
    return field


def section_label(text: str) -> MDLabel:
    return MDLabel(text=text, bold=True, adaptive_height=True, font_style="Title", role="medium")


def muted_label(text: str) -> MDLabel:
    label = MDLabel(text=text, adaptive_height=True, font_style="Label", role="large")
    label.theme_text_color = "Custom"
    label.text_color = _hex_to_rgba(MUTED_HEX)
    return label


def card(padding=16, spacing=10, orientation="vertical") -> MDCard:
    c = MDCard(
        orientation=orientation,
        padding=dp(padding),
        spacing=dp(spacing),
        radius=[14, 14, 14, 14],
        size_hint_y=None,
        style="elevated",
    )
    c.bind(minimum_height=c.setter("height"))
    return c


def row(spacing=10, height=None) -> BoxLayout:
    r = BoxLayout(orientation="horizontal", spacing=dp(spacing), size_hint_y=None)
    r.height = dp(height) if height else dp(44)
    return r


def spinner(values: list[str], initial: str | None = None) -> Spinner:
    sp = Spinner(
        text=initial or (values[0] if values else ""),
        values=values,
        size_hint_y=None,
        height=dp(44),
        background_color=_hex_to_rgba(ACCENT_HEX),
        color=(1, 1, 1, 1),
    )
    return sp


def toast(message: str, duration: float = 1.8) -> None:
    """A minimal, dependency-light toast notification. Deliberately avoids
    MDSnackbar/MDCard's ripple effect, which needs an FBO that can fail to
    initialize on some software-rendered/headless setups."""
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.graphics import Color, RoundedRectangle
    from kivy.uix.label import Label

    label = Label(
        text=message,
        size_hint=(None, None),
        size=(dp(min(320, 40 + 7 * len(message))), dp(42)),
        pos_hint={"center_x": 0.5},
        color=(1, 1, 1, 1),
    )
    label.pos = (Window.width / 2 - label.width / 2, dp(24))

    with label.canvas.before:
        Color(0.15, 0.15, 0.2, 0.92)
        rect = RoundedRectangle(pos=label.pos, size=label.size, radius=[10])

    def _sync_rect(*_):
        rect.pos = label.pos
        rect.size = label.size

    label.bind(pos=_sync_rect, size=_sync_rect)
    Window.add_widget(label)
    Clock.schedule_once(lambda dt: Window.remove_widget(label), duration)


def status_color(status: str):
    return _hex_to_rgba(
        {"Present": SUCCESS_HEX, "Paid": SUCCESS_HEX, "Late": WARNING_HEX, "Partial": WARNING_HEX,
         "Absent": DANGER_HEX, "Unpaid": DANGER_HEX, "Excused": MUTED_HEX}.get(status, MUTED_HEX)
    )


def _hex_to_rgba(hex_color: str, alpha: float = 1.0):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return (r, g, b, alpha)
