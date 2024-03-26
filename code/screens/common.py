import pygame
from dataclasses import dataclass

from engine.ui import Element, Text, Style, Button
from engine.types import *
from typing import Any, Callable, Iterable

@dataclass
class TextButtonColours:
    colour: Colour = (99, 169, 65)
    colour_shadow: Colour = (23, 68, 41)
    hover_colour: Colour = (95, 41, 46)
    hover_colour_shadow: Colour = (51, 22, 31)
    disabled_colour: Colour = (100, 100, 100)
    disabled_colour_shadow: Colour = (10, 10, 10)

class TextButton(Button):
    def __init__(
        self,
        parent: Element,
        yoffset: int,
        text: str,
        colours: TextButtonColours,
        font_size: int = 32,
        on_click: Callable = None,
        click_args: Iterable[Any] = [],
        text_hover: str = None,
        enabled: bool = True
        ) -> None:

        super().__init__(
            parent = parent,
            style = Style(
                alignment = "top-center",
                offset = (0, yoffset),
                size = (1, 1),
                alpha = 0
            ),
            hover_style=None,
            on_click = self._on_click_with_sound,
            click_args = click_args
            )

        self.click_func = on_click if on_click else self.do_nothing
        self.colours = colours
        self.font_size = font_size
        self.enabled = enabled

        text_size = self.manager.get_font("alagard", 32).size(text)
        self.style.size = text_size[0] + 4, text_size[1] + 4
        self.hover_style.size = self.style.size
        self.redraw_image()

        fore_colour = self.colours.colour if self.enabled else self.colours.disabled_colour
        shadow_colour = self.colours.colour_shadow if self.enabled else self.colours.disabled_colour_shadow

        self.text = self.add_child(Text(
            self,
            Style(
                font = self.manager.get_font("alagard", self.font_size),
                colour = shadow_colour,
                fore_colour = fore_colour,
                alignment = "center-center",
                position = "relative",
                text_shadow = 2,
            ),
            text
        ))

        self.text_normal = text
        self.text_hover = text_hover if text_hover else text

    def _on_click_with_sound(self, *args) -> None:
        self.manager.play_sound(sound_name = "effect/button_click", volume = 0.3)
        self.click_func(*args)

    def update(self) -> None:
        if not self.enabled: return
        super().update()
        if self.hovering and not self.last_hovering:
            self.manager.play_sound(sound_name = "effect/button_hover", volume = 0.1)
            self.text.style.fore_colour = self.colours.hover_colour
            self.text.style.colour = self.colours.hover_colour_shadow
            self.text.set_text(self.text_hover)
            self.text.redraw_image()
        elif not self.hovering and self.last_hovering:
            self.text.style.fore_colour = self.colours.colour
            self.text.style.colour = self.colours.colour_shadow
            self.text.set_text(self.text_normal)
            self.text.redraw_image()