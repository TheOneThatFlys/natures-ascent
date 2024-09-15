from __future__ import annotations
from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
    from entity import Player

import pygame, math, random

from engine import Node, Sprite, Logger
from engine.types import *
from item import Weapon, Spell, Pickup
from util.constants import *
from util import render_multiline, parse_spritesheet, create_outline

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

# class Sign(Interactable):
#     def __init__(self, parent: Node, position: Vec2, text: str) -> None:
#         super().__init__(parent)
#         self.image = self.manager.get_image("world/sign")
#         self.rect = self.image.get_rect(topleft = position)

#         rendered_text = render_multiline(self.manager.get_font("alagard", 16), text, PLAYER_GREEN, TILE_SIZE * 3, alignment = "center")
#         # shadow_text = render_multiline(self.manager.get_font("alagard", 16), text, TEXT_DARKWHITE, TILE_SIZE * 5, alignment = "center")

#         self.h_padding = 32
#         self.v_padding = 16

#         self.text_box = self.add_child(Sprite(self))
#         self.text_box.image = pygame.Surface((rendered_text.get_width() + self.h_padding, rendered_text.get_height() + self.v_padding))
#         self.text_box.rect = self.text_box.image.get_rect(centerx = self.rect.centerx, bottom = self.rect.top - 8)
#         self.text_box.z_index = 1
        
#         self.text_box.image.fill(BG_NAVY)
#         pygame.draw.rect(self.text_box.image, BG_DARKNAVY, self.text_box.image.get_rect(), 4)
#         midx = self.text_box.image.get_width() / 2
#         midy = self.text_box.image.get_height() / 2
#         # self.text_box.image.blit(shadow_text, shadow_text.get_rect(center = (midx, midy)))
#         self.text_box.image.blit(rendered_text, rendered_text.get_rect(center = (midx, midy)))

#         self.add_child(self.text_box)

#         self.text_active = False

#     def activate_text(self) -> None:
#         if not self.text_active:
#             self.text_active = True
#             self.text_box.add(self.manager.groups["render"])

#     def deactivate_text(self) -> None:
#         if self.text_active:
#             self.text_active = False
#             self.text_box.remove(self.manager.groups["render"])

#     def interact(self) -> None:
#         if self.text_active:
#             self.deactivate_text()
#         else:
#             self.activate_text()

#     def on_unfocus(self) -> None:
#         super().on_unfocus()
#         self.deactivate_text()

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

class PrayerStatue(Interactable):
    class PrayerStatueText(Sprite):
        def __init__(self, parent: PrayerStatue, cost: int) -> None:
            super().__init__(parent, [])
            self.cost = cost
            self.update_text(0)

        def update_text(self, coins: int) -> None:
            title_image = self.manager.get_font("alagard", 32).render("Pray", True, PLAYER_GREEN)
            title_shadow = self.manager.get_font("alagard", 32).render("Pray", True, PLAYER_DARKGREEN)
            cost_image = self.manager.get_font("alagard", 16).render(f"{min(coins, self.cost)}/{self.cost}", True, WHITE)
            coin_icon = self.manager.get_image("map/coin", 0.5)

            icontext_size = (
                cost_image.get_width() + coin_icon.get_width() + 4,
                max(cost_image.get_height(), coin_icon.get_height())
            )
            cost_icontext = pygame.Surface(icontext_size, pygame.SRCALPHA)
            cost_icontext.blit(cost_image, (0, 1))
            cost_icontext.blit(coin_icon, (cost_image.get_width() + 4, 0))

            img_size = (
                max(title_image.get_width(), cost_icontext.get_width()),
                title_image.get_height() + cost_icontext.get_height()
            )

            self.image = pygame.Surface(img_size, pygame.SRCALPHA)
            self.image.blit(title_shadow, title_image.get_rect(centerx = img_size[0] / 2, y = 2))
            self.image.blit(title_image, title_image.get_rect(centerx = img_size[0] / 2))
            self.image.blit(cost_icontext, cost_icontext.get_rect(centerx = img_size[0] / 2, top = title_image.get_height()))

            self.rect = self.image.get_rect(centerx = self.parent.rect.centerx, bottom = self.parent.rect.top - 8)

    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent, ["render"])
        self.image = self.manager.get_image("world/statue")
        self.rect = self.image.get_rect(center = position)

        self.pixel_scale = 4

        self.upgrade_cost = 50

        self.text = self.add_child(PrayerStatue.PrayerStatueText(self, self.upgrade_cost))

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

    def on_focus(self) -> None:
        player: Player = self.manager.get_object("player")
        self.text.update_text(player.inventory.coins)
        self.text.add(self.manager.groups["render"])
        super().on_focus()

    def on_unfocus(self) -> None:
        self.text.remove(self.manager.groups["render"])
        super().on_unfocus()
