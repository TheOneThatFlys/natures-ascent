import pygame

from engine import Screen, Node
from engine.ui import Text, Style
from util import draw_background_empty

from engine.types import *
from util.constants import *

from .common import TextButton, DividerX

class Leaderboard(Screen):
    def __init__(self, parent: Node) -> None:
        super().__init__(parent)
        self.master_container.style.alpha = 255
        self.master_container.style.image = draw_background_empty(self.rect.size)
        self.master_container.redraw_image()

        self.title_text = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "Leaderboard",
            style = Style(
                alignment = "top-center",
                offset = (0, 32),
                fore_colour = TEXT_GREEN,
                colour = TEXT_DARKGREEN,
                font = self.manager.get_font("alagard", 72),
                text_shadow = 2
            )
        ))

    def on_resize(self, new_res: Vec2) -> None:
        self.master_container.style.image = draw_background_empty(new_res)
        super().on_resize(new_res)


    
