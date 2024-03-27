import pygame
from engine import Screen, Node
from engine.types import *
from engine.ui import Element, Style, Text, Button
import util

from .common import TextButton, TextButtonColours

class SettingsUI(Element):
    def __init__(self, parent: Node, size: Vec2) -> None:
        super().__init__(
            parent = parent,
            style = Style(
                image = util.draw_background(size),
                alignment = "center-center"
            )
        )

        button_colours = TextButtonColours()

        self.title_text = self.add_child(Text(
            parent = self,
            text = "Settings",
            style = Style(
                alignment = "top-center",
                offset = (0, 64),
                fore_colour = button_colours.colour,
                colour = button_colours.colour_shadow,
                font = self.manager.get_font("alagard", 72),
                text_shadow = 2
            )
        ))

class SettingsScreen(Screen):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.ui = SettingsUI(self, self.rect.size)

    def on_resize(self, new_res: Vec2) -> None:
        self.ui.style.size = new_res
        self.ui.style.image = util.draw_background(new_res)
        for child in self.ui.get_all_children():
            child.redraw_image()

    def update(self) -> None:
        self.ui.update()

    def render(self, window: pygame.Surface) -> None:
        self.ui.render(window)