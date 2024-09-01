from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
    from entity import Player

import pygame, math

from engine import Node, Sprite, Logger
from engine.types import *
from item import Weapon, Spell, Pickup
from util.constants import *
from util import render_multiline, parse_spritesheet

class Interactable(Sprite):
    def __init__(self, parent: Node, groups: list[str] = []) -> None:
        super().__init__(parent, groups = ["interact", "render"] + groups)
        self.pixel_scale = 4
        self.is_focused = False

    def interact(self) -> None:
        """Called when the player interacts with the object"""
        Logger.warn(f"Interact method not implemented for {self.__class__.__name__}.")

    def on_focus(self) -> None:
        """Called when current interact focus is on object."""
        self.is_focused = True

    def on_unfocus(self) -> None:
        """Called when current interact focus is removed from object."""
        self.is_focused = False

class Sign(Interactable):
    def __init__(self, parent: Node, position: Vec2, text: str) -> None:
        super().__init__(parent)
        self.image = pygame.transform.scale_by(self.manager.get_image("world/sign"), PIXEL_SCALE)
        self.rect = self.image.get_rect(topleft = position)

        rendered_text = render_multiline(self.manager.get_font("alagard", 16), text, TEXT_LIGHTBROWN, TILE_SIZE * 3, alignment = "center")
        shadow_text = render_multiline(self.manager.get_font("alagard", 16), text, UI_DARKBROWN, TILE_SIZE * 3, alignment = "center")

        self.text_box = Sprite(self)
        self.text_box.image = pygame.Surface((rendered_text.get_width() + 16, rendered_text.get_height() + 16))
        self.text_box.rect = self.text_box.image.get_rect(centerx = self.rect.centerx, bottom = self.rect.top - 8)
        self.text_box.z_index = 1
        
        self.text_box.image.fill(UI_ALTBROWN)
        pygame.draw.rect(self.text_box.image, UI_BROWN, self.text_box.image.get_rect(), 4)
        midx = self.text_box.image.get_width() / 2
        midy = self.text_box.image.get_height() / 2
        self.text_box.image.blit(shadow_text, shadow_text.get_rect(center = (midx, midy + 1)))
        self.text_box.image.blit(rendered_text, rendered_text.get_rect(center = (midx, midy)))

        self.add_child(self.text_box)

        self.text_active = False

    def activate_text(self) -> None:
        if not self.text_active:
            self.text_active = True
            self.text_box.add(self.manager.groups["render"])

    def deactivate_text(self) -> None:
        if self.text_active:
            self.text_active = False
            self.text_box.remove(self.manager.groups["render"])

    def interact(self) -> None:
        if self.text_active:
            self.deactivate_text()
        else:
            self.activate_text()

    def on_unfocus(self) -> None:
        super().on_unfocus()
        self.deactivate_text()
    
class WorldItem(Interactable):
    def __init__(self, parent: Node, position: Vec2, item: Weapon|Spell) -> None:
        super().__init__(parent, ["update"])
        self.item = item

        self.image = self.manager.get_image(item.icon_key) 
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
                self.item.transfer(player)
                player.inventory.primary = self.item
                self.kill()
            else:
                self.item.transfer(player)
                player.inventory.primary.transfer(self)
                player.inventory.primary, self.item = self.item, player.inventory.primary
                self.image = self.manager.get_image(self.item.icon_key)
                player.interact_overlay.update_outline()
        else:
            if player.inventory.spell == None:
                self.item.transfer(player)
                player.inventory.spell = self.item
                self.kill()
            else:
                self.item.transfer(player)
                player.inventory.spell.transfer(self)
                player.inventory.spell, self.item = self.item, player.inventory.spell
                self.image = self.manager.get_image(self.item.icon_key)
                player.interact_overlay.update_outline()

    def update(self) -> None:
        self.t += self.manager.dt

        self.rect.centery = self.origin_y + 8 * math.sin(self.t * 0.1)
        if self.is_focused:
            self.manager.get_object("player").interact_overlay.rect.centery = self.rect.centery

class Chest(Interactable):
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent)

        self.closed_image, self.opened_image = parse_spritesheet(pygame.transform.scale_by(self.manager.get_image("world/chest"), PIXEL_SCALE), frame_count=2)
        self.image = self.closed_image
        self.rect = self.image.get_rect(center = position)

        self.opened = False

    def interact(self) -> None:
        self.open()

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