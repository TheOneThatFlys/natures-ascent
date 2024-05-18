from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from ..main import Game

import pygame
from engine import Screen, Node
from engine.types import *
from engine.ui import Element, Style, Text, Button, Dropdown
from util import draw_background
from util.constants import *

from .common import TextButton, TextButtonColours

_do_nothing = lambda: None

def _draw_dropdown_top(size: Vec2) -> pygame.Surface:
    s = pygame.Surface(size)
    s.fill((88, 105, 131))
    pygame.draw.rect(s, (26, 30, 36), (0, 0, *size), 4)
    return s

class DividerX(Element):
    def __init__(self, parent: Element, y: int, thickness: int = 2) -> None:
        self.thickness = thickness
        super().__init__(parent, style = Style(
            colour = (26, 30, 36),
            alignment = "top-center",
            offset = (0, y),
            size = (parent.style.size[0], thickness)
        ))

    def redraw_image(self) -> None:
        self.style.size = (self.parent.style.size[0], self.thickness)
        super().redraw_image()

class SettingsUI(Element):
    def __init__(self, parent: Node, size: Vec2, exit_binding: Callable[[], None] = _do_nothing) -> None:
        super().__init__(
            parent = parent,
            style = Style(
                image = self._draw_background(size),
                size = size,
                alignment = "center-center"
            )
        )

        button_colours = TextButtonColours()

        self.title_text = self.add_child(Text(
            parent = self,
            text = "Settings",
            style = Style(
                alignment = "top-center",
                offset = (0, 32),
                fore_colour = button_colours.colour,
                colour = button_colours.colour_shadow,
                font = self.manager.get_font("alagard", 72),
                text_shadow = 2
            )
        ))

        self.exit_button = self.add_child(Button(
            parent = self,
            on_click = exit_binding,
            style = Style(
                image = pygame.Surface((TILE_SIZE, TILE_SIZE)),
                alignment = "top-left",
                offset = (32, 32)
            ),
            hover_style = None
        ))

        self.divider1 = self.add_child(DividerX(self, self.title_text.style.offset[1] + self.title_text.rect.height))

        self.horizontal_container_1 = self.add_child(Element(self, style = Style(
            alpha = 0,
            size = (384, 40),
            alignment = "top-center",
            offset = (0, self.title_text.style.offset[1] + self.title_text.rect.height + 32)
        )))

        self.window_mode_dropdown = self.horizontal_container_1.add_child(Dropdown(
            parent = self.horizontal_container_1,
            options = ["Windowed", "Fullscreen", "Borderless"],
            on_change = self._on_window_mode_change,
            style = Style(
                alignment = "center-right",
                font = self.manager.get_font("alagard", 20),
                fore_colour = (255, 255, 255),
                image = _draw_dropdown_top((128, 40))
            ),
            button_style = Style(
                size = (128, 40),
                colour = (88, 105, 131),
                font = self.manager.get_font("alagard", 20),
                fore_colour = (255, 255, 255)
            ),
            hover_style = Style(
                colour = (62, 74, 93)
            )
        ))

        self.window_mode_text = self.horizontal_container_1.add_child(Text(
            parent = self.horizontal_container_1,
            text = "Window Mode",
            style = Style(
                fore_colour = (99, 169, 65),
                font = self.manager.get_font("alagard", 20),
                alignment = "center-left",
            ),
        ))

    def _on_window_mode_change(self, mode: str) -> None:
        match mode:
            case "Windowed":
                self.manager.game.set_windowed(STARTUP_SCREEN_SIZE)
            case "Borderless":
                self.manager.game.set_fullscreen(borderless=True)
            case "Fullscreen":
                self.manager.game.set_fullscreen()
            case _:
                raise TypeError(f"Unknown window mode: {mode}")

    def redraw_image(self) -> None:
        self.style.image = self._draw_background(self.style.size)
        super().redraw_image()

    def _draw_background(self, size: Vec2) -> pygame.Surface:
        image = pygame.Surface(size)
        image.fill((37, 44, 55))
        pygame.draw.rect(image, (26, 30, 36), (0, 0, *size), 24)
        return image

class SettingsScreen(Screen):
    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.ui = self.add_child(SettingsUI(self, self.rect.size, self._on_exit))

    def _on_exit(self) -> None:
        self.parent.set_screen("menu")

    def on_resize(self, new_res: Vec2) -> None:
        self.rect.size = new_res
        self.ui.style.size = new_res
        for child in self.ui.get_all_children():
            child.redraw_image()

    def on_mouse_down(self, button: int) -> None:
        self.ui.on_mouse_down(button)

    def update(self) -> None:
        for child in self.children:
            child.update()

    def render(self, window: pygame.Surface) -> None:
        for child in self.children:
            child.render(window)