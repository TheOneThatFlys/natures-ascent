import pygame, requests, threading

from engine import Screen, Node, Logger
from engine.ui import Text, Style, Element, Button
from util import draw_background_empty, parse_spritesheet, seconds_to_stime, is_valid_username

from engine.types import *
from util.constants import *

from .common import TextButton, DividerX, NameInput

class LeaderboardList(Element):
    def __init__(self, parent: Element, style: Style):
        self.titles = ("Position", "Name", "Score", "Time")
        self.n_cols = len(self.titles)
        self.row_height = 24
        self.col_width = style.size[0] // self.n_cols
        self.n_rows = style.size[1] // self.row_height

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
            if y == self.n_rows - 1: return
            for x, field in enumerate(item):
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

        self.leaderboard_list = self.master_container.add_child(LeaderboardList(
            parent = self.master_container,
            style = Style(
                alignment = "top-center",
                offset = (0, self.title_divider.rect.bottom + 16),
                size = (480, 16 * 24),
                font = self.manager.get_font("alagard", 16),
            )
        ))

        self.status_indicator = self.leaderboard_list.add_child(
            Element(
                parent = self.leaderboard_list,
                style = Style(
                    visible = False,
                    size = (128, 128),
                    alignment = "center-center"
                )
            )
        )

        self.config_container = self.master_container.add_child(
            Element(
                parent = self.master_container,
                style = Style(
                    size = (1, 1),
                    alignment = "top-center",
                    offset = (0, self.leaderboard_list.rect.bottom + 8),
                    alpha = 0,
                )
            )
        )

        section_font = self.manager.get_font("alagard", 32)
        self.scope_text = self.config_container.add_child(
            Text(
                parent = self.config_container,
                text = "Viewing ",
                style = Style(
                    font = section_font,
                    fore_colour = TEXT_WHITE,
                    alignment = "top-right",
                )
            )
        )

        self.scope_button = self.config_container.add_child(
            TextButton(
                parent = self.config_container,
                yoffset = 0,
                text = "global",
                on_click = self._on_scope_click,
                alignment = "top-left"
            )    
        )

        self.sort_text = self.scope_text = self.config_container.add_child(
            Text(
                parent = self.config_container,
                text = "Sort ",
                style = Style(
                    font = section_font,
                    fore_colour = TEXT_WHITE,
                    alignment = "top-right",
                    offset = (0, self.scope_text.rect.height)
                )
            )
        )

        self.sort_button = self.scope_button.add_child(
            TextButton(
                parent = self.scope_button,
                text = "score",
                alignment = "top-left",
                yoffset = self.scope_text.rect.height,
                on_click = self._on_sort_click,
            )    
        )

        self.type_text = self.config_container.add_child(
            Text(
                parent = self.config_container,
                text = "Type ",
                style = Style(
                    font = section_font,
                    fore_colour = TEXT_WHITE,
                    alignment = "top-right",
                    offset = (0, self.sort_text.rect.height + self.sort_text.style.offset[1])
                )
            )
        )

        self.type_button = self.scope_button.add_child(
            TextButton(
                parent = self.scope_button,
                text = "only completed",
                alignment = "top-left",
                yoffset = self.sort_text.rect.height + self.sort_text.style.offset[1],
                on_click = self._on_type_click,
            )    
        )

        self.username_text = self.config_container.add_child(
            Text(
                parent = self.config_container,
                text = "Username ",
                style = Style(
                    font = section_font,
                    fore_colour = TEXT_WHITE,
                    alignment = "top-right",
                    offset = (0, self.type_text.rect.height + self.type_text.style.offset[1])
                )
            )
        )

        self.username_input = self.config_container.add_child(
            NameInput(
                parent = self.config_container,
                alignment = "top-left",
                offset = (0, self.username_text.style.offset[1] + 2),
                subtext_offset = (0, -24)
            )
        )

        reload_norm, reload_hover = parse_spritesheet(self.manager.get_image("menu/reload", 0.5), assume_square=True)
        self.reload_button = self.config_container.add_child(
            Button(
                parent = self.config_container,
                style = Style(
                    image = reload_norm,
                    alignment = "top-center",
                    offset = (0, self.username_input.style.offset[1] + self.username_input.rect.height + 8)
                ),
                hover_style = Style(image = reload_hover),
                on_click = self._update_leaderboard_nonblocking,
            )
        )

        self._currently_fetching = False
        self.status_icon_noconnection, self.status_icon_error = parse_spritesheet(self.manager.get_image("menu/lb_icons"), assume_square=True)

        self._update_leaderboard_nonblocking()

    def _on_scope_click(self) -> None:
        if self.scope_button.text == "global":
            self.scope_button.set_text("player")
        else:
            self.scope_button.set_text("global")
        self._update_leaderboard_nonblocking()

    def _on_sort_click(self) -> None:
        if self.sort_button.text == "score":
            self.sort_button.set_text("time")
        else:
            self.sort_button.set_text("score")
        self._update_leaderboard_nonblocking()

    def _on_type_click(self) -> None:
        if self.type_button.text == "only completed":
            self.type_button.set_text("all")
        else:
            self.type_button.set_text("only completed")
        self._update_leaderboard_nonblocking()

    def _parse_response(self, response: dict) -> list[tuple]:
        l = []
        for v in response:
            l.append((
                "#" + str(v["position"]),
                v["username"],
                str(v["score"]),
                seconds_to_stime(v["time"])
            ))
        return l

    def _fetch_leaderboard(self, sort: str, only_completed: bool, only_player: bool) -> dict:
        self.set_status(None)
        headers = {
            "sort": sort,
            "only-completed": "1" if only_completed else "0"
        }
        if only_player == True:
            sub_route = "player"
            if not is_valid_username(self.manager.game.username):
                self.username_input._on_unfocus()
                return []
            headers["username"] = self.manager.game.username
        else:
            sub_route = "global"

        try:
            res = requests.get(
                SERVER_ADDRESS + "/leaderboard/" + sub_route,
                headers = headers,
                timeout = 5,
            )
        except requests.Timeout:
            Logger.warn(f"Could not fetch leaderboard ({headers}) [timeout]")
            self.set_status(self.status_icon_error)
            return []
        except requests.ConnectionError:
            self.set_status(self.status_icon_noconnection)
            return []

        if res.status_code == 200:
            return res.json()
        else:
            Logger.warn(f"Could not fetch leaderboard ({headers}) [code {res.status_code}]")
            self.set_status(self.status_icon_error)
            return []

    def _update_leaderboard(self) -> None:
        self.leaderboard_list.set_items(self._parse_response(self._fetch_leaderboard(
            self.sort_button.text,
            False if self.type_button.text == "all" else True,
            True if self.scope_button.text == "player" else False
        )))
        self._currently_fetching = False

    def _update_leaderboard_nonblocking(self) -> None:
        """Update leaderboard by calling requests with a seperate thread"""
        if self._currently_fetching: return
        self._currently_fetching = True
        a = threading.Thread(target = self._update_leaderboard)
        a.start()

    def set_status(self, status_image: None|pygame.Surface) -> None:
        if status_image is None:
            self.status_indicator.style.visible = False
        else:
            self.status_indicator.style.visible = True
            self.status_indicator.style.image = status_image

        self.status_indicator.redraw_image()

    def on_resize(self, new_res: Vec2) -> None:
        self.master_container.style.image = draw_background_empty(new_res)
        super().on_resize(new_res)
