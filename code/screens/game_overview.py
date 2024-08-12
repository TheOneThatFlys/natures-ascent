import pygame, os

from typing import Literal

from engine import Screen, Node
from engine.ui import Text, Style, Element
from util.constants import *

from .common import TextButton, TextButtonColours, PersistantGameData

class GameOverviewScreen(Screen):
    def __init__(self, parent: Node, game_data: PersistantGameData, end_type: Literal["win", "die"]) -> None:
        super().__init__(parent)
        if os.path.exists(RUN_SAVE_PATH): os.remove(RUN_SAVE_PATH)

        colours = TextButtonColours()

        self.title_text = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "Run Complete" if end_type == "win" else "You Died",
            style = Style(
                fore_colour = colours.colour,
                colour = colours.colour_shadow,
                text_shadow = 2,
                font = self.manager.get_font("alagard", 72),
                alignment = "top-center",
                offset = (0, 96)
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
            colours = colours,
            on_click = self._on_continue,
        ))

        self.manager.stop_music(1000)

    def _on_continue(self) -> None:
        self.manager.game.set_screen("menu")



