import pygame, os, time, datetime

from typing import Literal

from engine import Screen, Node
from engine.ui import Text, Style, Element
from engine.types import *
from util.constants import *

from .common import TextButton, TextButtonColours, OverviewData, DividerX

class GameOverviewScreen(Screen):
    def __init__(self, parent: Node, game_data: OverviewData, end_type: Literal["win", "die"]) -> None:
        super().__init__(parent)
        if os.path.exists(RUN_SAVE_PATH): os.remove(RUN_SAVE_PATH)

        self.master_container.style.alpha = 255
        self.master_container.style.image = self._draw_background(self.rect.size)
        self.master_container.redraw_image()

        self.title_text = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "Run Complete" if end_type == "win" else "You Died",
            style = Style(
                fore_colour = TEXT_GREEN,
                colour = TEXT_DARKGREEN,
                text_shadow = 2,
                font = self.manager.get_font("alagard", 72),
                alignment = "top-center",
                offset = (0, 48)
            )
        ))

        self.title_divider = self.master_container.add_child(DividerX(
            parent = self.master_container,
            y = self.title_text.rect.bottom,
        ))

        self.time_text = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "Time Elapsed",
            style = Style(
                fore_colour = TEXT_GREEN,
                colour = TEXT_DARKGREEN,
                text_shadow = 2,
                font = self.manager.get_font("alagard", 32),
                alignment = "top-center",
                offset = (0, self.title_divider.style.offset[1] + 16)
            )
        ))

        self.time_value = self.master_container.add_child(Text(
            parent = self.master_container,
            text = f"{time.strftime("%H:%M:%S", time.gmtime(game_data.time))}.{str(round(game_data.time % 1, 3)).removeprefix("0.")}",
            style = Style(
                fore_colour = TEXT_BROWN,
                colour = TEXT_DARKBROWN,
                text_shadow = 1,
                font = self.manager.get_font("alagard", 24),
                alignment = "top-center",
                offset = (0, self.time_text.rect.bottom + 8)
            )
        ))

        self.score_text = self.master_container.add_child(Text(
            parent = self.master_container,
            text = "Score",
            style = Style(
                fore_colour = TEXT_GREEN,
                colour = TEXT_DARKGREEN,
                text_shadow = 2,
                font = self.manager.get_font("alagard", 32),
                alignment = "top-center",
                offset = (0, self.time_value.rect.bottom + 8)
            )
        ))

        self.score_value = self.master_container.add_child(Text(
            parent = self.master_container,
            text = str(game_data.score),
            style = Style(
                fore_colour = TEXT_BROWN,
                colour = TEXT_DARKBROWN,
                text_shadow = 1,
                font = self.manager.get_font("alagard", 24),
                alignment = "top-center",
                offset = (0, self.score_text.rect.bottom + 8)
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

    def _draw_background(self, size: Vec2) -> pygame.Surface:
        image = pygame.Surface(size)
        image.fill(BG_NAVY)
        pygame.draw.rect(image, BG_DARKNAVY, (0, 0, *size), 24)
        return image

    def on_resize(self, new_res: Vec2) -> None:
        self.master_container.style.image = self._draw_background(new_res)
        super().on_resize(new_res)

    def _on_continue(self) -> None:
        self.manager.game.set_screen("menu")



