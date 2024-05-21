from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from ..main import Game

import pygame
from engine import Screen, Node
from engine.types import *
from engine.ui import Element, Style, Text, Button, Dropdown, Slider
from util import parse_spritesheet
from util.constants import *

from .common import TextButtonColours

_do_nothing = lambda: None

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

        back_button_normal, back_button_hover = parse_spritesheet(self.manager.get_image("menu/back_arrow"), frame_count=2)
        self.exit_button = self.add_child(Button(
            parent = self,
            on_click = exit_binding,
            style = Style(
                image = back_button_normal,
                alignment = "top-left",
                offset = (48, 48)
            ),
            hover_style = Style(image = back_button_hover)
        ))

        self.divider1 = self.add_child(DividerX(self, self.title_text.style.offset[1] + self.title_text.rect.height))

        ROW_HEIGHT = 40
        self.horizontal_container_1 = self.add_child(Element(self, style = Style(
            alpha = 0,
            size = (384, ROW_HEIGHT),
            alignment = "top-center",
            offset = (0, self.title_text.style.offset[1] + self.title_text.rect.height + 32)
        )))

        self.horizontal_container_2 = self.add_child(Element(self, style = Style(
            alpha = 0,
            size = (384, ROW_HEIGHT),
            alignment = "top-center",
            offset = (0, self.horizontal_container_1.style.offset[1] + ROW_HEIGHT)
        )))

        self.horizontal_container_3 = self.add_child(Element(self, style = Style(
            alpha = 0,
            size = (384, ROW_HEIGHT),
            alignment = "top-center",
            offset = (0, self.horizontal_container_2.style.offset[1] + ROW_HEIGHT)
        )))

        # send item 1 to back
        self.children.remove(self.horizontal_container_1)
        self.children.append(self.horizontal_container_1)

        self.window_mode_dropdown = self.horizontal_container_1.add_child(Dropdown(
            parent = self.horizontal_container_1,
            options = ["Windowed", "Fullscreen", "Borderless"],
            on_change = self._on_window_mode_change,
            style = Style(
                alignment = "center-right",
                font = self.manager.get_font("alagard", 20),
                fore_colour = (255, 255, 255),
                image = self.manager.get_image("menu/dropdown_head")
            ),
            button_style = Style(
                size = (128, 40),
                colour = (142, 82, 82),
                font = self.manager.get_font("alagard", 20),
                fore_colour = (255, 255, 255)
            ),
            hover_style = Style(image = None, size = (128, 40), colour = (186, 117, 106))
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

        self.sfx_volume_text = self.horizontal_container_2.add_child(Text(
            parent = self.horizontal_container_2,
            text = "SFX Volume",
            style = Style(
                fore_colour = (99, 169, 65),
                font = self.manager.get_font("alagard", 20),
                alignment = "center-left",
            ),
        ))

        self.sfx_slider = self.horizontal_container_2.add_child(Slider(
            parent = self.horizontal_container_2,
            style = Style(
                alignment = "center-right",
                image = self.manager.get_image("menu/slider_bar"),
            ),
            knob_style = Style(
                image = self.manager.get_image("menu/slider_knob"),
            ),
            on_change = self._on_sfx_change,
            on_unfocus = self._on_sfx_unfocus
        ))

        self.sfx_slider_annotation = self.horizontal_container_2.add_child(Text(
            parent = self.horizontal_container_2,
            text = str(int(self.manager.sfx_volume * 100)),
            style = Style(
                alignment = "center-left",
                offset = (self.horizontal_container_2.rect.width + 12, 0),
                fore_colour = (99, 169, 65),
                font = self.manager.get_font("alagard", 20)
            )
        ))

        self.music_volume_text = self.horizontal_container_3.add_child(Text(
            parent = self.horizontal_container_3,
            text = "Music Volume",
            style = Style(
                fore_colour = (99, 169, 65),
                font = self.manager.get_font("alagard", 20),
                alignment = "center-left",
            ),
        ))

        self.music_slider = self.horizontal_container_3.add_child(Slider(
            parent = self.horizontal_container_3,
            style = Style(
                alignment = "center-right",
                image = self.manager.get_image("menu/slider_bar"),
            ),
            knob_style = Style(
                image = self.manager.get_image("menu/slider_knob"),
            ),
            on_change = self._on_music_change
        ))

        self.music_slider_annotation = self.horizontal_container_3.add_child(Text(
            parent = self.horizontal_container_3,
            text = str(int(self.manager.music_volume * 100)),
            style = Style(
                alignment = "center-left",
                offset = (self.horizontal_container_2.rect.width + 12, 0),
                fore_colour = (99, 169, 65),
                font = self.manager.get_font("alagard", 20)
            )
        ))

        self.sfx_slider.set_value(self.manager.sfx_volume)
        self.music_slider.set_value(self.manager.music_volume)
        window_mode = self.manager.game.get_window_mode()
        self.window_mode_dropdown.set_selected(window_mode[0].upper()+window_mode[1:])

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

    def _on_sfx_change(self, value: float) -> None:
        self.manager.sfx_volume = value
        self.sfx_slider_annotation.set_text(str(int(value * 100)))

    def _on_music_change(self, value: float) -> None:
        self.manager.music_volume = value
        self.music_slider_annotation.set_text(str(int(value * 100)))

    def _on_sfx_unfocus(self, value: float) -> None:
        self.manager.play_sound("effect/hit", volume = 0.2)

    def _draw_background(self, size: Vec2) -> pygame.Surface:
        image = pygame.Surface(size)
        image.fill((37, 44, 55))
        pygame.draw.rect(image, (26, 30, 36), (0, 0, *size), 24)
        return image
    
    def redraw_image(self) -> None:
        self.style.image = self._draw_background(self.style.size)
        super().redraw_image()

class SettingsScreen(Screen):
    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.ui = self.add_child(SettingsUI(self, self.rect.size, self._on_exit))

    def _on_exit(self) -> None:
        self.parent.set_screen("menu")

    def on_resize(self, new_res: Vec2) -> None:
        super().on_resize(new_res)
        self.ui.style.size = new_res
        self.ui.on_resize(new_res)

    def on_mouse_down(self, button: int) -> None:
        self.ui.on_mouse_down(button)

    def on_mouse_up(self, button: int) -> None:
        self.ui.on_mouse_up(button)

    def update(self) -> None:
        for child in self.children:
            child.update()

    def render(self, window: pygame.Surface) -> None:
        for child in self.children:
            child.render(window)