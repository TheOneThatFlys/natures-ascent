from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..main import Game

import pygame
from engine import Screen, Node
from engine.types import *
from engine.ui import Element, Style, Text, Button
from util import draw_background
from util.constants import *

from .common import TextButton, TextButtonColours

class SettingsUI(Element):
    def __init__(self, parent: Node, size: Vec2) -> None:
        super().__init__(
            parent = parent,
            style = Style(
                image = draw_background(size),
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

    def redraw_image(self) -> None:
        self.style.size = self.parent.rect.size
        self.style.image = draw_background(self.style.size)
        super().redraw_image()

class SettingsScreen(Screen):
    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.ui = self.add_child(SettingsUI(self, self.rect.size))
        self.exit_button = self.add_child(Button(
            parent = self,
            on_click = game.set_screen,
            click_args = ["menu"],
            style = Style(
                image = pygame.Surface((TILE_SIZE, TILE_SIZE)),
                alignment = "top-left",
                offset = (TILE_SIZE, TILE_SIZE)
            ),
            hover_style = None
        ))

    def on_resize(self, new_res: Vec2) -> None:
        self.ui.style.size = new_res
        for child in self.ui.get_all_children():
            child.redraw_image()

    def update(self) -> None:
        for child in self.children:
            child.update()

    def render(self, window: pygame.Surface) -> None:
        for child in self.children:
            child.render(window)