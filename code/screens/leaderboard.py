import pygame, time

from engine import Screen, Node
from engine.ui import Text, Style, Element, Button
from util import draw_background_empty, parse_spritesheet

from engine.types import *
from util.constants import *

from .common import TextButton, DividerX

class LeaderboardList(Element):
    def __init__(self, parent: Element, style: Style):
        self.titles = ("Position", "Name", "Score", "Time")
        self.n_cols = len(self.titles)
        self.row_height = 24
        self.col_width = style.size[0] // self.n_cols

        self._cols: list[Element] = []
        self._items: list[tuple[str]] = []

        super().__init__(parent, style)
        self._add_ui_skeleton()

    def _add_ui_skeleton(self) -> None:
        # create columns for each field
        col_offsets = [self.col_width * i for i in range(self.n_cols)]
        for offset in col_offsets:
            c = self.add_child(Element(
                parent = self,
                style = Style(
                    alignment = "top-left",
                    offset = (offset, 0),
                    size = (self.col_width, self.style.size[1]),
                    alpha = 0,
                )
            ))
            self._cols.append(c)

        # add titles
        for j, title in enumerate(self.titles):
            self._cols[j].add_child(Text(
                    parent = self._cols[j],
                    text = title,
                    style = Style(
                        alignment = "top-center",
                        offset = (0, 4),
                        fore_colour = TEXT_GREEN,
                        colour = TEXT_DARKGREEN,
                        font = self.style.font,
                        text_shadow = 1,
                    )
            ))
        
        # add empty text elements for each grid position
        self._text_grid: list[list[Text]] = []
        for y in range(self.rect.height // self.row_height):
            row = []
            for x in range(self.n_cols):
                row.append(self._cols[x].add_child(Text(
                    parent = self._cols[x],
                    text = "",
                    style = Style(
                        alignment = "top-center",
                        font = self.style.font,
                        fore_colour = WHITE,
                        offset = (0, (y + 1) * self.row_height + 4)
                    )
                )))
            self._text_grid.append(row)

    def redraw_image(self) -> None:
        bg = pygame.Surface(self.style.size)
        for i in range(0, self.style.size[1] // self.row_height):
            colour = BG_NAVY if i % 2 == 0 else BG_LIGHTNAVY
            pygame.draw.rect(bg, colour, (0, i * self.row_height, self.style.size[0], self.row_height))
        pygame.draw.rect(bg, BG_DARKNAVY, (0, 0, *self.style.size), 2)
        pygame.draw.line(bg, BG_DARKNAVY, (0, self.row_height), (self.style.size[0], self.row_height), 2)
        self.style.image = bg

        super().redraw_image()

    def set_items(self, items: list[tuple[str]]):
        """Set the items to be displayed in the leaderboard."""
        self._items = items

        for y, row in enumerate(self._text_grid):
            for x, v in enumerate(row):
                v.set_text("")

        for y, item in enumerate(items):
            for x, field in enumerate((f"#{(y + 1)}",) + item):
                self._text_grid[y][x].set_text(field)

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
                font = self.manager.get_font("alagard", 64),
                text_shadow = 4
            )
        ))

        self.title_divider = self.master_container.add_child(DividerX(
            parent = self.master_container,
            y = self.title_text.rect.bottom
        ))

        back_button_normal, back_button_hover = parse_spritesheet(self.manager.get_image("menu/back_arrow", 0.5), frame_count=2)
        self.exit_button = self.master_container.add_child(Button(
            parent = self.master_container,
            on_click = self.parent.set_screen,
            click_args = ("menu",),
            style = Style(
                image = back_button_normal,
                alignment = "top-left",
                offset = (48, 48)
            ),
            hover_style = Style(image = back_button_hover)
        ))

        self.test_leaderboard = self.master_container.add_child(LeaderboardList(
            parent = self.master_container,
            style = Style(
                alignment = "top-center",
                offset = (0, self.title_divider.rect.bottom + 16),
                size = (480, 480),
                font = self.manager.get_font("alagard", 16),
            )
        ))

        self.test_leaderboard.set_items([
            ("TestPlayer1", "3240", "45m45s"),
            ("TestPlayer2", "2495", "34m23s"),
        ])

    def on_resize(self, new_res: Vec2) -> None:
        self.master_container.style.image = draw_background_empty(new_res)
        super().on_resize(new_res)
