from __future__ import annotations
from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
    from entity import Player

import pygame, math, random

from engine import Node, Sprite, Logger
from engine.types import *
from item import Weapon, Spell, Pickup
from util.constants import *
from util import parse_spritesheet, lerp_colour

class Interactable(Sprite):
    def __init__(self, parent: Node, groups: list[str] = []) -> None:
        super().__init__(parent, groups = ["interact", "render"] + groups)
        self.pixel_scale = 4
        self.is_focused = False
    
    @property
    def focus_point(self) -> Vec2:
        return self.rect.center

    def interact(self) -> None:
        """Called when the player interacts with the object"""
        Logger.warn(f"Interact method not implemented for {self.__class__.__name__}.")

    def on_focus(self) -> None:
        """Called when current interact focus is on object."""
        self.is_focused = True

    def on_unfocus(self) -> None:
        """Called when current interact focus is removed from object."""
        self.is_focused = False

class WorldItem(Interactable):
    def __init__(self, parent: Node, position: Vec2, item: Weapon|Spell) -> None:
        super().__init__(parent, ["update"])
        self.item = item

        self.image = self.manager.get_image(item.icon_key, 0.5)
        self.rect = self.image.get_rect(center = position)
        self.pixel_scale = 2
        self.z_index = 1

        self.origin_y = self.rect.centery
        self.t = 0

    def interact(self) -> None:
        player: Player = self.manager.get_object("player")
        is_weapon = not isinstance(self.item, Spell)

        if is_weapon:
            if player.inventory.primary == None:
                player.inventory.set_weapon(0, self.item)
                self.kill()
            else:
                temp = player.inventory.primary
                player.inventory.set_weapon(0, self.item)
                temp.transfer(self)
                self.item = temp
                self.image = self.manager.get_image(self.item.icon_key, 0.5)
                player.interact_overlay.update_outline()
        else:
            if player.inventory.spell == None:
                self.item.transfer(player)
                player.inventory.set_weapon(1, self.item)
                self.kill()
            else:
                temp = player.inventory.spell
                player.inventory.set_weapon(1, self.item)
                temp.transfer(self)
                self.item = temp
                self.image = self.manager.get_image(self.item.icon_key, 0.5)
                player.interact_overlay.update_outline()
        self.manager.play_sound("effect/item_pickup", 0.7)

    def update(self) -> None:
        self.t += self.manager.dt

        self.rect.centery = self.origin_y + 8 * math.sin(self.t * 0.1)
        if self.is_focused:
            self.manager.get_object("player").interact_overlay.rect.centery = self.rect.centery

class Chest(Interactable):
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent)

        self.closed_image, self.opened_image = parse_spritesheet(self.manager.get_image("world/chest"), frame_count=2)
        self.image = self.closed_image
        self.rect = self.image.get_rect(center = position)

        self.opened = False

    def interact(self) -> None:
        self.open()
        self.manager.play_sound("effect/chest_open", 0.7)

    def open(self) -> None:
        if not self.opened:
            self.opened = True
            self.image = self.opened_image
            self.remove(self.manager.groups["interact"])
            self.on_open()

    def on_open(self) -> None:
        pass

class ItemChest(Chest):
    def __init__(self, parent: Node, position: Vec2, item: Type[Weapon]|Type[Spell]|None) -> None:
        super().__init__(parent, position)

        self.held_item: Weapon|Spell|None = self.add_child(item(self)) if item else None
    
    def on_open(self) -> None:
        if self.held_item:
            level = self.manager.get_object("level")
            level.add_child(WorldItem(level, (self.rect.centerx, self.rect.centery - TILE_SIZE), self.held_item))

class PickupChest(Chest):
    def __init__(self, parent: Node, position: Vec2, pickup_type: Type[Pickup], number: int) -> None:
        super().__init__(parent, position)

        self.pickup_type = pickup_type
        self.number = number

    def on_open(self) -> None:
        level = self.manager.get_object("level")
        for _ in range(self.number):
            level.add_child(self.pickup_type(level, (self.rect.centerx, self.rect.centery - TILE_SIZE)))

class InteractableCostText(Sprite):
    def __init__(self, parent: Interactable, title: str, text: str, icon: pygame.Surface, offset: int = 8, text_colour = WHITE) -> None:
        super().__init__(parent, ["update"])
        self.parent: Interactable
        self._title = title
        self._text = text
        self._icon = icon
        self._offset = offset
        self._text_colour = text_colour

        self._t = 0
        self._flash_time = 30
        self._flash_colour = text_colour
        self.update_text(self._text)

    def update_text(self, text: str) -> None:
        """Update sub text"""
        self._text = text
        title_image = self.manager.get_font("alagard", 32).render(self._title, True, PLAYER_GREEN)
        title_shadow = self.manager.get_font("alagard", 32).render(self._title, True, PLAYER_DARKGREEN)
        text_image = self.manager.get_font("alagard", 16).render(self._text, True, lerp_colour(self._text_colour, self._flash_colour, max(self._t / self._flash_time, 0)))
        icon = self._icon

        icontext_size = (
            text_image.get_width() + icon.get_width() + 4,
            max(text_image.get_height(), icon.get_height())
        )
        icontext = pygame.Surface(icontext_size, pygame.SRCALPHA)
        icontext.blit(text_image, (0, 1))
        icontext.blit(icon, (text_image.get_width() + 4, 0))

        img_size = (
            max(title_image.get_width(), icontext.get_width()),
            title_image.get_height() + icontext.get_height()
        )

        self.image = pygame.Surface(img_size, pygame.SRCALPHA)
        self.image.blit(title_shadow, title_image.get_rect(centerx = img_size[0] / 2, y = 2))
        self.image.blit(title_image, title_image.get_rect(centerx = img_size[0] / 2))
        self.image.blit(icontext, icontext.get_rect(centerx = img_size[0] / 2, top = title_image.get_height()))

        self.rect = self.image.get_rect(centerx = self.parent.rect.centerx, bottom = self.parent.rect.top - self._offset)

    def flash(self, colour: Colour, time: int = 30) -> None:
        self._flash_colour = colour
        self._t = time
        self._flash_time
        self.update_text(self._text)

    def update(self) -> None:
        r_group = self.manager.groups["render"]
        # if displayed
        if r_group in self.groups():
            # remove if not focused
            if not self.parent.is_focused:
                self.remove(r_group)
        else: # if not displayed
            # add if focused
            if self.parent.is_focused:
                self.add(r_group)

        if self._t > 0:
            self._t -= self.manager.dt
            self.update_text(self._text)
        else:
            self._t = 0

class PrayerStatue(Interactable):
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent, ["render"])
        self.image = self.manager.get_image("world/statue")
        self.rect = self.image.get_rect(center = position)

        self.upgrade_cost = 50

        self.text = self.add_child(InteractableCostText(self, "Pray", "???", self.manager.get_image("map/coin", 0.5)))

    @property
    def focus_point(self) -> Vec2:
        return (self.rect.centerx, self.rect.bottom)

    def interact(self) -> None:
        player: Player = self.manager.get_object("player")
        if player.inventory.coins >= self.upgrade_cost:
            player.inventory.coins -= self.upgrade_cost
            
            valid_slots = [0, 1]
            for s in (0, 1):
                if player.inventory.at(s) == None:
                    valid_slots.remove(s)
                elif player.inventory.at(s).upgrade_level == 3:
                    valid_slots.remove(s)
            if valid_slots:
                slot_to_upgrade = random.choice(valid_slots)
                player.inventory.at(slot_to_upgrade).upgrade()
                self.update_hover_text()
                self.manager.play_sound("effect/upgrade", 0.4)
                return
            
        # If the player doesn't have enough coins or all slots are maxed out
        self.text.flash(TEXT_RED)
        self.manager.play_sound("effect/error", 0.4)
        self.manager.get_object("camera").shake(3, 4)

    def update_hover_text(self):
        player: Player = self.manager.get_object("player")
        self.text.update_text(f"{min(player.inventory.coins, self.upgrade_cost)}/{self.upgrade_cost}")

    def on_focus(self) -> None:
        super().on_focus()
        self.update_hover_text()

class SpawnPortal(Interactable):
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent, ["render"])
        self.image = self.manager.get_image("world/spawn_portal")
        self.rect = self.image.get_rect(center = position)
        # render above floor and below player
        self.z_index = -0.5

        self.text = self.add_child(InteractableCostText(self, "Ascend", "???", self.manager.get_image("map/explored", 0.5), offset = -8))

    def _successfull_interact(self) -> None:
        level = self.manager.get_object("level")
        game = self.manager.game
        game.set_screen("overview", game_data = level.get_overview_data(), end_type = "win")

    def interact(self) -> None:
        fm = self.manager.get_object("floor-manager")
        for room in fm.rooms.values():
            if not room.completed:
                self.text.flash(TEXT_RED)
                self.manager.play_sound("effect/error", 0.4)
                self.manager.get_object("camera").shake(3, 4)
                return
        # self.manager.play_sound("effect/portal", 0.4)
        self._successfull_interact()

    def update_hover_text(self):
        fm = self.manager.get_object("floor-manager")
        rooms_completed, total_rooms = fm.get_completion_status()
        self.text.update_text(f"{rooms_completed}/{total_rooms}")

    def on_focus(self) -> None:
        super().on_focus()
        self.update_hover_text()