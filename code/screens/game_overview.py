import pygame, os

from engine import Screen, Node
from engine.ui import Text, Style
from util.constants import *

from .common import TextButton, TextButtonColours

class GameOverviewScreen(Screen):
    def __init__(self, parent: Node, game_data: dict) -> None:
        super().__init__(parent)
        os.remove(RUN_SAVE_PATH)

        temp_text = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "you died unlucky lol",
            style = Style(
                fore_colour = (255, 0, 0),
                font = self.manager.get_font("alagard", 32),
                alignment = "center-center",
            )
        ))

        b = temp_text.add_child(TextButton(
            temp_text,
            yoffset = 40,
            text = "wtf??",
            colours = TextButtonColours(),
            on_click = self.parent.set_screen, click_args = ["menu"]
        ))



