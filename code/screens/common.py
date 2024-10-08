import pygame
from dataclasses import dataclass

from engine.ui import Element, Text, Style, Button, TextBox
from engine.types import *
from typing import Callable, Iterable, Optional

from util import create_gui_image, is_valid_username
from util.constants import *

@dataclass
class TextButtonColours:
    colour: Colour = TEXT_GREEN
    colour_shadow: Colour = TEXT_DARKGREEN
    hover_colour: Colour = TEXT_BROWN
    hover_colour_shadow: Colour = TEXT_DARKBROWN
    disabled_colour: Colour = TEXT_GRAY
    disabled_colour_shadow: Colour = TEXT_DARKGRAY

class TextButton(Button):
    def __init__(
        self,
        parent: Element,
        yoffset: int,
        text: str,
        colours: TextButtonColours = TextButtonColours(),
        font_size: int = 32,
        xoffset: int = 0,
        alignment: Alignment = "top-center",
        on_click: Optional[Callable] = None,
        click_args: Iterable = [],
        enabled: bool = True
        ) -> None:

        super().__init__(
            parent = parent,
            style = Style(
                alignment = alignment,
                offset = (xoffset, yoffset),
                size = (1, 1),
                alpha = 0
            ),
            on_click = on_click,
            click_args = click_args,
            enabled = enabled
            )

        self.colours = colours
        self.font_size = font_size

        text_size = self.manager.get_font("alagard", font_size).size(text)
        self.style.size = text_size[0] + 4, text_size[1] + 4
        self.hover_style.size = self.style.size
        self.redraw_image()

        fore_colour = self.colours.colour if self.enabled else self.colours.disabled_colour
        shadow_colour = self.colours.colour_shadow if self.enabled else self.colours.disabled_colour_shadow

        self._text_element = self.add_child(Text(
            self,
            Style(
                font = self.manager.get_font("alagard", self.font_size),
                colour = shadow_colour,
                fore_colour = fore_colour,
                alignment = alignment,
                position = "relative",
                text_shadow = 2,
            ),
            text
        ))

        self.text = text

    def set_text(self, text) -> None:
        self._text_element.set_text(text)
        self.text = text

    def update(self) -> None:
        if not self.enabled: return
        super().update()
        if self.hovering and not self.last_hovering:
            self._text_element.style.fore_colour = self.colours.hover_colour
            self._text_element.style.colour = self.colours.hover_colour_shadow
            self._text_element.redraw_image()
        elif not self.hovering and self.last_hovering:
            self._text_element.style.fore_colour = self.colours.colour
            self._text_element.style.colour = self.colours.colour_shadow
            self._text_element.redraw_image()

class IconText(Element):
    def __init__(self, parent: Element, style: Style, text: str, icon: pygame.Surface, icon_alignment: Literal["left", "right"] = "left", padding: int = 0) -> None:
        self.text = text
        self.icon = icon
        self.icon_alignment = icon_alignment
        self.padding = padding
        super().__init__(parent, style)

    def set_text(self, new_text: str) -> None:
        self.text = new_text
        self.redraw_image()

    def redraw_image(self) -> None:
        text_size = self.style.font.size(self.text)
        icon_size = self.icon.get_size()

        self.image = pygame.Surface(
            (text_size[0] + icon_size[0] + self.padding, max(text_size[1], icon_size[1])),
            pygame.SRCALPHA
        )
        self.rect = self.image.get_rect()

        text_surf = self.style.font.render(self.text, False, self.style.fore_colour)

        if self.icon_alignment == "left":
            icon_rect = self.icon.get_rect(centery = self.rect.height / 2, x = 0)
            self.image.blit(self.icon, icon_rect)
            self.image.blit(text_surf, text_surf.get_rect(left = icon_rect.right + self.padding, centery = self.rect.height / 2))
        else:
            text_rect = text_surf.get_rect(x = 0, centery = self.rect.height / 2)
            self.image.blit(text_surf, text_rect)
            self.image.blit(self.icon, self.icon.get_rect(left = text_rect.right + self.padding, centery = self.rect.height / 2))

        self.calculate_position()

class DividerX(Element):
    def __init__(self, parent: Element, y: int, thickness: int = 2, length: int = -1, colour: Colour = BG_DARKNAVY) -> None:
        self.thickness = thickness
        self.length = length
        super().__init__(parent, style = Style(
            colour = colour,
            alignment = "top-center",
            offset = (0, y),
        ))

    def redraw_image(self) -> None:
        self.style.size = (self.parent.style.size[0] if self.length == -1 else self.length, self.thickness)
        super().redraw_image()

class NameInput(TextBox):
    def __init__(self, parent: Element, alignment: Alignment, offset: Vec2 = (0, 0), subtext_offset: Vec2 = (0, 24)) -> None:
        super().__init__(
            parent = parent,
            initial_text = parent.manager.game.username,
            text_padding = (4, 2),
            max_length = 16,
            on_unfocus = (self._on_unfocus, ()),
            character_set = ALLOWED_CHARACTERS,
            style = Style(
                fore_colour = TEXT_WHITE,
                image = create_gui_image((200, 24)),
                font = parent.manager.get_font("alagard", 16),
                alignment = alignment,
                offset = offset,
            )
        )

        self._subtext = self.add_child(Text(
            parent = self,
            text = "",
            style = Style(
                fore_colour = TEXT_RED,
                alignment = "bottom-right",
                font = self.manager.get_font("alagard", 16),
                offset = subtext_offset,
            )
        ))

    def _on_unfocus(self) -> None:
        username = self.text
        if is_valid_username(username):
            self.manager.game.username = username
            self._subtext.set_text("")
            self.style.image = create_gui_image((200, 24))
        else:
            self._subtext.set_text("Invalid Username")
            self.style.image = create_gui_image((200, 24), border_colour = TEXT_RED, shadow_colour = TEXT_RED)
            self.manager.play_sound("effect/error", 0.2)
        self.redraw_image()

@dataclass
class ItemChestData:
    position: Vec2
    item_id: int

@dataclass
class PickupChestData:
    position: Vec2
    number: int
    type: Literal["coin", "health"] 

@dataclass
class WorldItemData:
    item_id: int
    upgrade: int
    position: Vec2

@dataclass
class PersistantGameData:
    """Data that is persistant across the whole run i.e. current run data."""
    player_position: Vec2
    player_health: float
    player_iframes: float

    weapon_id: int
    spell_id: int

    weapon_upgrade: int
    spell_upgrade: int

    coins: int

    seed: float

    time: float
    player_hits: int

    rooms_discovered: list[Vec2]
    rooms_cleared: list[Vec2]

    coin_pickups: list[Vec2]
    health_pickups: list[Vec2]

    item_chests: list[ItemChestData]
    pickup_chests: list[PickupChestData]
    opened_chests: list[Vec2]

    world_items: list[WorldItemData]
    found_ids: list[int]

@dataclass
class OverviewData:
    """Data that is displayed on the game end screen."""
    game_data: PersistantGameData
    time: float
    score: int
    completed: bool
