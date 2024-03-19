import pygame
import random
from typing import Callable, Iterable
from engine import Screen
from engine.ui import Element, Style, Text, Button
import util

class TextButtonMenu(Button):
    def __init__(self, parent: Element, yoffset: int, text: str, on_click: Callable = None, click_args: Iterable = [], text_hover: str = None, enabled = True):
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
        self.enabled = enabled

        text_size = self.manager.get_font("alagard", 32).size(text)
        self.style.size = text_size[0] + 4, text_size[1] + 4
        self.hover_style.size = self.style.size
        self.redraw_image()

        fore_colour = (99, 169, 65) if self.enabled else (100, 100, 100)
        shadow_colour = (23, 68, 41) if self.enabled else (10, 10, 10)

        self.text = self.add_child(Text(
            self,
            Style(
                font = self.manager.get_font("alagard", 32),
                colour = shadow_colour,
                fore_colour = fore_colour,
                alignment = "center-center",
                position = "relative",
                text_shadow = True,
            ),
            text
        ))

        self.text_normal = text
        self.text_hover = text_hover if text_hover else text

    def _on_click_with_sound(self, *args):
        self.manager.play_sound(sound_name = "effect/button_click", volume = 0.3)
        self.click_func(*args)

    def update(self):
        if not self.enabled: return
        super().update()
        if self.hovering and not self.last_hovering:
            self.manager.play_sound(sound_name = "effect/button_hover", volume = 0.1)
            self.text.style.colour = (51, 22, 31)
            self.text.style.fore_colour = (95, 41, 46)
            self.text.set_text(self.text_hover)
            self.text.redraw_image()
        elif not self.hovering and self.last_hovering:
            self.text.style.colour = (23, 68, 41)
            self.text.style.fore_colour = (99, 169, 65)
            self.text.set_text(self.text_normal)
            self.text.redraw_image()

class Menu(Screen):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.master_container = Element(
            parent = self,
            style = Style(
                size = self.rect.size,
                image = util.draw_background(self.rect.size),
                stretch_type = "skew",
                colour = (78, 173, 245)
            )
        )

        self.tree_img = self.master_container.add_child(
            Element(
                self.master_container,
                style = Style(
                    size = (384, 384),
                    image = self.manager.get_image("menu/tree"),
                    stretch_type = "expand",
                    alignment = "bottom-center"
                )
            )
        )

        self.title = self.master_container.add_child(
            Text(
                parent = self.master_container,
                text = "Nature's Ascent",
                style = Style(
                    alignment = "top-center",
                    offset = (0, 64),
                    fore_colour = (99, 169, 65),
                    colour = (23, 68, 41),
                    text_shadow = True,
                    font = self.manager.get_font("alagard", 72),
                )
            )
        )

        self.play_button = self.master_container.add_child(TextButtonMenu(
            parent = self.master_container,
            yoffset = self.title.rect.bottom + 16,
            text = "New Run",
            on_click = self.parent.set_screen,
            click_args = ["level"]
        ))

        self.leaderboard_button = self.master_container.add_child(TextButtonMenu(
            parent = self.master_container,
            yoffset = self.play_button.rect.bottom,
            text = "Leaderboard",
            enabled = False
        ))

        self.settings_button = self.master_container.add_child(TextButtonMenu(
            parent = self.master_container,
            yoffset = self.leaderboard_button.rect.bottom,
            text = "Settings",
            on_click = self.parent.set_screen,
            click_args = ["settings"]
        ))
        
        self.exit_button = self.master_container.add_child(TextButtonMenu(
            parent = self.master_container,
            yoffset = self.settings_button.rect.bottom,
            text = "Exit",
            text_hover = ":c",
            on_click = self.parent.queue_close
        ))

        self.secret_button = self.tree_img.add_child(Button(
            parent = self.tree_img,
            style = Style(
                size = (8, 8),
                position = "relative",
                alignment = "center-center",
                visible = False
            ),
            hover_style = None,
            on_click = self.manager.play_sound,
            click_args=["effect/hit1"]
        ))

        self.manager.play_sound(sound_name = "music/menu", volume = 0.5, loop = True)
            
    def on_resize(self, new_res):
        self.master_container.style.size = new_res
        self.master_container.style.image = util.draw_background(new_res)

        for item in self.master_container.get_all_children():
            item.redraw_image()

    def render(self, window):
        self.master_container.render(window)

    def update(self):
        self.master_container.update()