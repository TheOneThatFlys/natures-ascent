
import pygame, os, json, threading

from engine import Screen, Node
from engine.ui import Text, Style, Element, TextBox, Button
from engine.types import *
from util.constants import *
from util import create_gui_image, is_valid_username, draw_background_empty, seconds_to_stime, SaveHelper

from .common import TextButton, TextButtonColours, OverviewData, DividerX, NameInput

try:
    import requests
except ImportError:
    # weird hack to import a local version of requests
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "external"))
    import requests

class GameOverviewScreen(Screen):
    def __init__(self, parent: Node, game_data: OverviewData) -> None:
        super().__init__(parent)
        if os.path.exists(RUN_SAVE_PATH): os.remove(RUN_SAVE_PATH)

        self.end_type = "win" if game_data.completed else "die"

        self.master_container.style.alpha = 255
        self.master_container.style.image = draw_background_empty(self.rect.size)
        self.master_container.redraw_image()

        self.title_text = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "Run Complete" if self.end_type == "win" else "You Died",
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

        self.time_value = self.v_container.add_child(Text(
            parent = self.v_container,
            text = seconds_to_stime(game_data.time),
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

        self.name_field = self.name_container.add_child(NameInput(
            parent = self.name_container,
            alignment = "center-right",
        ))

        self.upload_notice = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "Click the button below to submit your run onto the leaderboard!",
            style = Style(
                alignment = "top-center",
                offset = (0, self.name_container.rect.bottom + 16),
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
            hover_style = Style(image = create_gui_image((128, 32), border_colour = TEXT_GREEN, shadow_colour = TEXT_GREEN)),
            on_click = self._submit_run_nonblocking,
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

        self.status_text = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "",
            style = Style(
                font = self.manager.get_font("alagard", 16),
                fore_colour = TEXT_WHITE,
                alignment = "top-center",
                offset = (0, self.submit_button.rect.bottom + 8)
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

        self.game_data = game_data
        self._submitted_data = False
        self._currently_submitting = False

        self.manager.stop_music(1000)

    def _on_continue(self) -> None:
        self.manager.game.set_screen("menu")
        
    def _submit_run(self):
        if self._currently_submitting:
            return
        self._currently_submitting = True
        if self._submitted_data:
            self.set_status_text("You have already submitted this run!")
            return

        if not is_valid_username(self.name_field.text):
            self.name_field._on_unfocus()
            return
        
        self.set_status_text("Submitting run...")
        message = {
            "username": self.name_field.text,
            "data": SaveHelper.encode_data(bytes(json.dumps({
                "score": self.game_data.score,
                "time": self.game_data.time,
                "completed": self.game_data.completed,
            }), "utf-8"))
        }
        failed = False
        try:
            res = requests.post(SERVER_ADDRESS + "/leaderboard/submit", json = message, timeout = 5)
        except (ConnectionError, TimeoutError) as e:
            failed = True
        if not failed and res.status_code != 200:
            failed = True

        if failed:
            self.set_status_text("Error submitting run. Try again later.")
            return

        self.set_status_text("Run successfully submitted!")
        self._submitted_data = True
        self._currently_submitting = False

    def _submit_run_nonblocking(self):
        # TODO: actually make this nonblocking
        submit_thread = threading.Thread(target = self._submit_run)
        submit_thread.start()

    def set_status_text(self, text: str) -> None:
        self.status_text.set_text(text)

    def on_resize(self, new_res: Vec2) -> None:
        self.master_container.style.image = draw_background_empty(new_res)
        super().on_resize(new_res)


