from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from ..main import Game

import pygame
from engine import Screen, Node
from engine.types import *
from engine.ui import Element, Style, Text, Button, Dropdown, Slider, ScrollableElement
from util import parse_spritesheet, create_gui_image
from util.constants import *

from .common import DividerX

_do_nothing = lambda: None

class KeybindSelector(Element):
    """Size provided in style is size of one keybind row"""
    def __init__(self, parent: Element, style: Style):
        super().__init__(parent, style = style)

        self.buttons: dict[str, Button] = {}
        self.considering = None
        self.key_translations: dict[str, str] = {
            "LEFT SHIFT": "SHIFT",
            "RIGHT SHIFT": "RSHIFT",
            "LEFT CTRL": "CTRL",
            "RIGHT CTRL": "RCTRL",
            "LEFT ALT": "ALT",
            "RIGHT ALT": "RALT",
            "LEFT META": "META",
            "RIGHT META": "RMETA",
            "ESCAPE": "ESC",
            "PAGE UP": "PGUP",
            "PAGE DOWN": "PGDN",
            "CAPS LOCK": "CAPS",
            "NUM LOCK": "NUM",
            "SCROLL LOCK": "SCROLL",
            "BACKSPACE": "BACK",
            "INSERT": "INS",
            "DELETE": "DEL",
        }

        self._button_image = create_gui_image((80, 32))
        self._button_image_selected = create_gui_image((80, 32), border_colour = TEXT_GREEN, shadow_colour = TEXT_GREEN)
        self.create_rows()

    def create_rows(self) -> None:
        i = 0
        for action, key in self.manager.keybinds.items():
            # text
            self.add_child(Text(
                parent = self,
                text = action.replace("-", " ").title(),
                style = Style(
                    alignment = "center-left",
                    font = self.manager.get_font("alagard", 16),
                    offset = (0, i * self.style.size[1]),
                    colour = self.style.colour,
                    fore_colour = self.style.fore_colour
                )
            ))
            # button
            b = self.add_child(Button(
                parent = self,
                hover_sound = None,
                on_click = self._on_keybind_click,
                click_args = (action,),
                style = Style(
                    image = self._button_image,
                    alignment = "center-right",
                    offset = (0, i * self.style.size[1]),
                )
            ))

            b.add_child(Text(
                parent = b,
                text = self.translate_key(key),
                style = Style(
                    font = self.manager.get_font("alagard", 16),
                    fore_colour = TEXT_WHITE,
                    alignment = "center-center",
                    offset = (0, 2)
                )
            ))

            self.buttons[action] = b
            i += 1

    def _on_keybind_click(self, action: str) -> None:
        self.select_button(action)

    def translate_key(self, key: int) -> None:
        """Translate a key enum into a max 6 letter string."""
        name = pygame.key.name(key).upper()
        if name in self.key_translations:
            return self.key_translations[name]
        return name

    def select_button(self, action: str) -> None:
        if self.considering:
            self.buttons[self.considering].style.image = self._button_image
            self.buttons[self.considering].redraw_image()

        self.considering = action
        self.buttons[action].style.image = self._button_image_selected
        self.buttons[action].redraw_image()

    def deselect_button(self, action: str) -> None:
        self.buttons[action].style.image = self._button_image
        self.buttons[action].redraw_image()
        self.considering = None

    def on_key_down(self, key: int, unicode: str) -> None:
        super().on_key_down(key, unicode)
        if self.considering:
            self.manager.keybinds[self.considering] = key
            self.buttons[self.considering].children[0].set_text(self.translate_key(key))
            self.deselect_button(self.considering)

    def on_mouse_down(self, button: int) -> None:
        if (button == 1 or button == 3) and self.considering:
            self.deselect_button(self.considering)
        super().on_mouse_down(button)

class SettingsScrollable(ScrollableElement):
    def __init__(self, parent: Element, size: Vec2, yoffset: int):
        super().__init__(parent, focus_only = False, scroll_factor = 10, style = Style(
            size = size,
            alignment = "top-center",
            offset = (0, yoffset),
            alpha = 0,
        ))

        ROW_WIDTH = size[0]
        ROW_HEIGHT = 40
        self.horizontal_container_1 = self.add_child(Element(self, style = Style(
            alpha = 0,
            size = (ROW_WIDTH, ROW_HEIGHT),
            alignment = "top-center",
            offset = (0, 4)
        )))

        self.horizontal_container_2 = self.add_child(Element(self, style = Style(
            alpha = 0,
            size = (ROW_WIDTH, ROW_HEIGHT),
            alignment = "top-center",
            offset = (0, self.horizontal_container_1.style.offset[1] + ROW_HEIGHT)
        )))

        self.horizontal_container_3 = self.add_child(Element(self, style = Style(
            alpha = 0,
            size = (ROW_WIDTH, ROW_HEIGHT),
            alignment = "top-center",
            offset = (0, self.horizontal_container_2.style.offset[1] + ROW_HEIGHT)
        )))

        self.window_mode_dropdown = self.horizontal_container_1.add_child(Dropdown(
            parent = self.horizontal_container_1,
            options = ["Windowed", "Fullscreen", "Borderless"],
            on_change = self._on_window_mode_change,
            style = Style(
                alignment = "center-right",
                font = self.manager.get_font("alagard", 16),
                fore_colour = TEXT_WHITE,
                image = create_gui_image((128, 40)),
            ),
            button_style = Style(
                size = (128, 40),
                colour = UI_ALTBROWN,
                font = self.manager.get_font("alagard", 16),
                fore_colour = TEXT_WHITE
            ),
            hover_style = Style(image = None, size = (128, 40), colour = UI_ALTLIGHTBROWN)
        ))

        self.window_mode_text = self.horizontal_container_1.add_child(Text(
            parent = self.horizontal_container_1,
            text = "Window Mode",
            style = Style(
                fore_colour = TEXT_GREEN,
                font = self.manager.get_font("alagard", 16),
                alignment = "center-left",
            ),
        ))

        self.sfx_volume_text = self.horizontal_container_2.add_child(Text(
            parent = self.horizontal_container_2,
            text = "SFX Volume",
            style = Style(
                fore_colour = TEXT_GREEN,
                font = self.manager.get_font("alagard", 16),
                alignment = "center-left",
            ),
        ))

        self.sfx_slider = self.horizontal_container_2.add_child(Slider(
            parent = self.horizontal_container_2,
            style = Style(
                alignment = "center-right",
                image = create_gui_image((192, 8)),
            ),
            knob_style = Style(
                image = self.manager.get_image("menu/slider_knob", 0.5),
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
                fore_colour = TEXT_GREEN,
                font = self.manager.get_font("alagard", 16)
            )
        ))

        self.music_volume_text = self.horizontal_container_3.add_child(Text(
            parent = self.horizontal_container_3,
            text = "Music Volume",
            style = Style(
                fore_colour = TEXT_GREEN,
                font = self.manager.get_font("alagard", 16),
                alignment = "center-left",
            ),
        ))

        self.music_slider = self.horizontal_container_3.add_child(Slider(
            parent = self.horizontal_container_3,
            style = Style(
                alignment = "center-right",
                image = create_gui_image((192, 8)),
            ),
            knob_style = Style(
                image = self.manager.get_image("menu/slider_knob", 0.5),
            ),
            on_change = self._on_music_change
        ))

        self.music_slider_annotation = self.horizontal_container_3.add_child(Text(
            parent = self.horizontal_container_3,
            text = str(int(self.manager.music_volume * 100)),
            style = Style(
                alignment = "center-left",
                offset = (self.horizontal_container_2.rect.width + 12, 0),
                fore_colour = TEXT_GREEN,
                font = self.manager.get_font("alagard", 16)
            )
        ))

        self.sfx_slider.set_value(self.manager.sfx_volume)
        self.music_slider.set_value(self.manager.music_volume)
        window_mode = self.manager.game.get_window_mode()
        self.window_mode_dropdown.set_selected(window_mode[0].upper()+window_mode[1:])

        self.section_divider = self.add_child(DividerX(self, self.horizontal_container_3.style.offset[1] + ROW_HEIGHT, length = ROW_WIDTH))

        self.controls_header = self.add_child(Text(
            parent = self,
            text = "Controls",
            style = Style(
                alignment = "top-center",
                offset = (0, self.section_divider.style.offset[1] + self.section_divider.rect.height + 4),
                fore_colour = TEXT_GREEN,
                colour = TEXT_DARKGREEN,
                font = self.manager.get_font("alagard", 32),
                text_shadow = 2
            )
        ))

        self.keybinds = self.add_child(KeybindSelector(self, style = Style(
            alpha = 0,
            size = (ROW_WIDTH, ROW_HEIGHT),
            alignment = "top-center",
            offset = (0, self.controls_header.style.offset[1] + self.controls_header.rect.height),
            fore_colour = TEXT_GREEN
        )))

        # send item 1 to back
        self.children.remove(self.horizontal_container_1)
        self.children.append(self.horizontal_container_1)

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

    def on_resize(self, size: Vec2) -> None:
        self.style.size = (384, self.parent.rect.height - self.style.offset[1] - 24)
        super().on_resize(size)

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

        self.title_text = self.add_child(Text(
            parent = self,
            text = "Settings",
            style = Style(
                alignment = "top-center",
                offset = (0, 32),
                fore_colour = TEXT_GREEN,
                colour = TEXT_DARKGREEN,
                font = self.manager.get_font("alagard", 64),
                text_shadow = 4
            )
        ))

        back_button_normal, back_button_hover = parse_spritesheet(self.manager.get_image("menu/back_arrow", 0.5), frame_count=2)
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

        self.settings = self.add_child(SettingsScrollable(
            parent = self,
            size = (384, self.rect.height - self.divider1.style.offset[1] - 26),
            yoffset = self.divider1.style.offset[1] + 2)
        )

    def _draw_background(self, size: Vec2) -> pygame.Surface:
        image = pygame.Surface(size)
        image.fill(BG_NAVY)
        pygame.draw.rect(image, BG_DARKNAVY, (0, 0, *size), 24)
        return image
    
    def redraw_image(self) -> None:
        self.style.image = self._draw_background(self.style.size)
        super().redraw_image()

class SettingsScreen(Screen):
    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.ui = self.master_container.add_child(SettingsUI(self.master_container, self.rect.size, self._on_exit))

    def _on_exit(self) -> None:
        self.parent.set_screen("menu")

    def on_resize(self, new_res: Vec2) -> None:
        self.ui.style.size = new_res
        super().on_resize(new_res)

    def update(self) -> None:
        for child in self.children:
            child.update()

    def render(self, window: pygame.Surface) -> None:
        for child in self.children:
            child.render(window)