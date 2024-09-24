import pygame
import os

from engine import Screen
from engine.ui import Element, Style, Text, Button
from engine.types import *
from util.constants import *
import util

from .common import TextButton, TextButtonColours

class Menu(Screen):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        
        self.master_container.style.alpha = 255
        self.master_container.style.image = util.draw_background(self.rect.size)
        self.master_container.redraw_image()

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
                    fore_colour = TEXT_GREEN,
                    colour = TEXT_DARKGREEN,
                    text_shadow = 4,
                    font = self.manager.get_font("alagard", 64),
                )
            )
        )

        button_colours = TextButtonColours()

        can_continue_run = os.path.exists(RUN_SAVE_PATH)

        self.continue_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.title.rect.bottom + 16,
            text = "Continue",
            on_click = lambda: self.parent.set_screen("level", load_from_file = True),
            colours = button_colours,
            enabled = can_continue_run,
        ))

        self.play_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.continue_button.rect.bottom,
            text = "New Run",
            on_click = self.parent.set_screen,
            click_args = ["level"],
            colours = button_colours
        ))

        self.leaderboard_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.play_button.rect.bottom,
            text = "Leaderboard",
            colours = button_colours,
            on_click = self.parent.set_screen,
            click_args = ["leaderboard"]
        ))

        self.settings_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.leaderboard_button.rect.bottom,
            text = "Settings",
            on_click = self.parent.set_screen,
            click_args = ["settings"],
            colours = button_colours
        ))
        
        self.exit_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.settings_button.rect.bottom,
            text = "Exit",
            on_click = self.parent.queue_close,
            colours = button_colours
        ))

        self.manager.play_music("music/menu")

    def on_resize(self, new_res: Vec2) -> None:
        self.master_container.style.image = util.draw_background(new_res)
        super().on_resize(new_res)