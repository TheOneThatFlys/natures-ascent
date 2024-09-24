from ctypes import alignment
import pygame, os, time

from typing import Literal

from engine import Screen, Node
from engine.ui import Text, Style, Element, TextBox, Button
from engine.types import *
from util.constants import *
from util import create_gui_image, is_valid_username, draw_background_empty

from .common import TextButton, TextButtonColours, OverviewData, DividerX

class GameOverviewScreen(Screen):
    def __init__(self, parent: Node, game_data: OverviewData, end_type: Literal["win", "die"]) -> None:
        super().__init__(parent)
        if os.path.exists(RUN_SAVE_PATH): os.remove(RUN_SAVE_PATH)

        self.end_type = end_type

        self.master_container.style.alpha = 255
        self.master_container.style.image = draw_background_empty(self.rect.size)
        self.master_container.redraw_image()

        self.title_text = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "Run Complete" if end_type == "win" else "You Died",
            style = Style(
                fore_colour = TEXT_GREEN,
                colour = TEXT_DARKGREEN,
                text_shadow = 2,
                font = self.manager.get_font("alagard", 64),
                alignment = "top-center",
                offset = (0, 48)
            )
        ))

        self.title_divider = self.master_container.add_child(DividerX(
            parent = self.master_container,
            y = self.title_text.rect.bottom,
        ))

        self.v_container = self.master_container.add_child(Element(
            parent = self.master_container,
            style = Style(
                alpha = 0,
                alignment = "top-center",
                size = (384, 96),
                offset = (0, self.title_divider.style.offset[1] + 16)
            )
        ))

        self.time_text = self.v_container.add_child(Text(
            parent = self.v_container,
            text = "Time",
            style = Style(
                fore_colour = TEXT_GREEN,
                font = self.manager.get_font("alagard", 32),
                alignment = "top-left",
            )
        ))

        time_text = time.strftime("%Mm%Ss", time.gmtime(game_data.time))
        time_text = time_text.removeprefix("00m")
        self.time_value = self.v_container.add_child(Text(
            parent = self.v_container,
            text = time_text,
            style = Style(
                fore_colour = TEXT_WHITE,
                font = self.manager.get_font("alagard", 32),
                alignment = "top-right",
            )
        ))

        self.score_text = self.v_container.add_child(Text(
            parent = self.v_container,
            text = "Score",
            style = Style(
                fore_colour = TEXT_GREEN,
                font = self.manager.get_font("alagard", 32),
                alignment = "top-left",
                offset = (0, self.time_text.rect.height)
            )
        ))

        self.score_value = self.v_container.add_child(Text(
            parent = self.v_container,
            text = str(game_data.score),
            style = Style(
                fore_colour = TEXT_WHITE,
                font = self.manager.get_font("alagard", 32),
                alignment = "top-right",
                offset = self.score_text.style.offset,
            )
        ))

        self.divider_1 = self.master_container.add_child(DividerX(
            parent = self.master_container,
            y = self.score_value.rect.bottom + 16,
            length = 384
        ))

        self.online_header = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "Online",
            style = Style(
                font = self.manager.get_font("alagard", 48),
                fore_colour = TEXT_GREEN,
                colour = TEXT_DARKGREEN,
                text_shadow = 2,
                alignment = "top-center",
                offset = (0, self.divider_1.rect.y + 16)
            )
        ))

        self.name_container = self.master_container.add_child(Element(
            parent = self.master_container,
            style = Style(
                offset = (0, self.online_header.rect.bottom),
                alignment = "top-center",
                size = (384, 64),
                alpha = 0,
            )
        ))

        self.name_label = self.name_container.add_child(Text(
            parent = self.name_container,
            text = "Username",
            style = Style(
                fore_colour = TEXT_GREEN,
                font = self.manager.get_font("alagard", 32),
                alignment = "center-left",
            )
        ))

        self.name_field = self.name_container.add_child(TextBox(
            parent = self.name_container,
            initial_text = self.manager.game.username,
            text_padding = (4, 2),
            max_length = 16,
            on_unfocus = (self._on_name_unfocus, ()),
            character_set = ALLOWED_CHARACTERS,
            style = Style(
                fore_colour = TEXT_WHITE,
                image = create_gui_image((200, 24)),
                font = self.manager.get_font("alagard", 16),
                alignment = "center-right",
            ),
        ))

        self.name_subtext = self.name_container.add_child(Text(
            parent = self.name_container,
            text = "",
            style = Style(
                fore_colour = TEXT_RED,
                alignment = "center-right",
                font = self.manager.get_font("alagard", 16),
                offset = (0, 24),
            )
        ))

        self.upload_notice = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "Click the button below to submit your run onto the leaderboard!",
            style = Style(
                alignment = "top-center",
                offset = (0, self.name_container.rect.bottom),
                font = self.manager.get_font("alagard", 16),
                fore_colour = TEXT_WHITE,
            )
        ))

        self.submit_button = self.master_container.add_child(Button(
            parent = self.master_container,
            style = Style(
                image = create_gui_image((128, 32)),
                alignment = "top-center",
                offset = (0, self.upload_notice.rect.bottom + 8)
            ),
            hover_style = Style(image = create_gui_image((128, 32), border_colour = TEXT_GREEN, shadow_colour = TEXT_GREEN))
        ))

        self.submit_text = self.submit_button.add_child(Text(
            parent = self.submit_button,
            text = "Submit",
            style = Style(
                font = self.manager.get_font("alagard", 16),
                fore_colour = TEXT_WHITE,
                alignment = "center-center"
            )
        ))

        self.continue_container = self.master_container.add_child(Element(
            parent = self.master_container,
            style = Style(
                offset = (0, 96),
                alignment = "bottom-center",
                size = (1, 1)
            )
        ))

        self.continue_button = self.continue_container.add_child(TextButton(
            parent = self.continue_container,
            text = "Continue",
            yoffset = 0,
            colours = TextButtonColours(),
            on_click = self._on_continue,
        ))

        self.manager.stop_music(1000)
    
    def _on_name_unfocus(self) -> None:
        username = self.name_field.text
        if is_valid_username(username):
            self.manager.game.username = username
            self.name_subtext.set_text("")
            self.name_field.style.image = create_gui_image((200, 24))
        else:
            self.name_subtext.set_text("Invalid Username")
            self.name_field.style.image = create_gui_image((200, 24), border_colour = TEXT_RED, shadow_colour = TEXT_RED)
            self.manager.play_sound("effect/error", 0.2)
        self.name_field.redraw_image()

    def _on_continue(self) -> None:
        self.manager.game.set_screen("menu")

    def on_resize(self, new_res: Vec2) -> None:
        self.master_container.style.image = draw_background_empty(new_res)
        super().on_resize(new_res)


