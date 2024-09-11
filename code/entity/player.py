from __future__ import annotations

import pygame
from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
    from screens import Level
    from world import Interactable

from engine import Node, Sprite
from engine.types import *
from util import parse_spritesheet, get_closest_direction, create_outline
from util.constants import *

from item import Weapon, Spell, Sword

from .entity import Entity
from .stats import PlayerStats, player_stats

class LastFacing:
    """Class to store last facing direction data of player."""
    def __init__(self) -> None:
        self.walk: Direction = "right"
        self.attack: Direction = "right"
        self.overall: Direction = "right"

    def set(self, type: str, direction: Direction) -> None:
        self.overall = direction
        if type == "walk":
            self.walk = direction
        elif type == "attack":
            self.attack = direction
        else:
            raise TypeError("Unknown facing type: " + type)

class Inventory(Node):
    def __init__(self, parent: Player) -> None:
        super().__init__(parent)
        self.player: Player = parent

        self.primary: Weapon = None
        self.spell: Spell = None
        
        self.coins: int = 0

    def add_coin(self, value: int) -> None:
        self.coins += value

    def set_weapon(self, slot: int, weapon: Type[Weapon]|Weapon) -> None:
        instance = self.player.add_child(weapon(self.player)) if isinstance(weapon, Type) else weapon
        if instance.parent != self.player: instance.transfer(self.player)
        if slot == 0:
            if self.primary != None:
                self.remove_weapon(0)
            self.primary = instance
        elif slot == 1:
            if self.spell != None:
                self.remove_weapon(1)
            self.spell = instance
            self.player.spell_cd = self.spell.cooldown_time

    def remove_weapon(self, slot: int) -> None:
        if slot == 0:
            if self.primary != None:
                self.player.remove_child(self.primary)
                self.primary = None
        if slot == 1:
            if self.spell != None:
                self.player.remove_child(self.spell)
                self.spell = None

    def at(self, index: int) -> Weapon | None:
        if index == 0:
            return self.primary
        if index == 1:
            return self.secondary
        raise IndexError()

class InteractionOverlay(Sprite):
    def __init__(self, parent: Sprite, max_distance: float) -> None:
        super().__init__(parent, groups = ["render", "update"])

        self.image = pygame.Surface((0, 0))
        self.rect = self.image.get_rect()

        self.max_distance = max_distance

        self.current_focus: Interactable | None = None

    def update_outline(self) -> None:
        if self.current_focus == None:
            self.image = pygame.Surface((0, 0))
        else:
            self.image = create_outline(self.current_focus.image, pixel_scale = self.current_focus.pixel_scale)
            self.rect = self.image.get_rect(center = self.current_focus.rect.center)
            self.z_index = self.current_focus.z_index
            self.current_focus.on_focus()

    def update(self) -> None:
        closest_object: Interactable = min(
            self.manager.groups["interact"],
            key = lambda sprite: (pygame.Vector2(sprite.rect.center) - self.parent.rect.center).magnitude()
        )

        if (pygame.Vector2(closest_object.rect.center) - self.parent.rect.center).magnitude() > self.max_distance: closest_object = None

        if closest_object != self.current_focus:
            if self.current_focus != None: self.current_focus.on_unfocus()
            self.current_focus = closest_object
            self.update_outline()

        if self.current_focus != None:
            self.rect.center = self.current_focus.rect.center

        pressed = pygame.key.get_just_pressed()
        if pressed[self.manager.keybinds["interact"]] and self.current_focus != None:
            self.current_focus.interact()

class Player(Entity):
    def __init__(self, parent: Node, start_pos: pygame.Vector2) -> None:
        super().__init__(
            parent,
            stats = player_stats,
            health_bar_mode = "normal"
        )

        self.stats: PlayerStats

        self.id = "player"
        
        self._load_animations()
        self.image = self.animation_manager.set_animation("idle-right")
        self.rect = self.image.get_frect(topleft = start_pos)

        self.hitbox = pygame.Rect(0, 0, self.rect.width - 18, self.rect.height)
        self.hitbox_offset = pygame.Vector2(2, 0)

        self.health_bar.health_colour = PLAYER_GREEN

        self.last_facing = LastFacing()
        self.walking = False
        self.disable_movement_input = False

        self.inventory = self.add_child(Inventory(parent = self))
        self.inventory.set_weapon(0, Sword)

        self.interact_overlay = self.add_child(InteractionOverlay(self, INTERACT_DISTANCE))

        self.attack_cd = 0
        self.spell_cd = 0

    def _load_animations(self) -> None:
        types = ["idle", "damage", "walk", "dash"]
        directions = ["right", "left", "down", "up"]
        for type in types:
            rows = parse_spritesheet(self.manager.get_image("player/" + type), frame_count = 4, direction = "y")
            for i, dir in enumerate(directions):
                anim = parse_spritesheet(rows[i], frame_size = (16 * PIXEL_SCALE, 16 * PIXEL_SCALE))
                self.animation_manager.add_animation(type + "-" + dir, anim)

        attack_types = ["sword_attack", "spear_attack"]
        for type in attack_types:
            attack_rows = parse_spritesheet(self.manager.get_image("player/" + type), frame_count = 4, direction = "y")
            for i, dir in enumerate(directions):
                anim = parse_spritesheet(attack_rows[i], frame_size = (16 * PIXEL_SCALE * 3, 16 * PIXEL_SCALE * 3))
                self.animation_manager.add_animation(type + "-" + dir, anim)

    def get_inputs(self) -> None:
        keys = pygame.key.get_pressed()

        # movement
        dv = pygame.Vector2()
        self.walking = False
        if not self.disable_movement_input:
            if keys[self.manager.keybinds["move-up"]]:
                dv.y -= 1
                self.last_facing.set("walk", "up")
                self.walking = True
            if keys[self.manager.keybinds["move-down"]]:
                dv.y += 1
                self.last_facing.set("walk", "down")
                self.walking = True
            if keys[self.manager.keybinds["move-left"]]:
                dv.x -= 1
                self.last_facing.set("walk", "left")
                self.walking = True
            if keys[self.manager.keybinds["move-right"]]:
                dv.x += 1
                self.last_facing.set("walk", "right")
                self.walking = True

        # attack
        if keys[self.manager.keybinds["attack-right"]]:
            self.try_attack("right")
        elif keys[self.manager.keybinds["attack-left"]]:
            self.try_attack("left")
        elif keys[self.manager.keybinds["attack-up"]]:
            self.try_attack("up")
        elif keys[self.manager.keybinds["attack-down"]]:
            self.try_attack("down")
        
        if keys[self.manager.keybinds["spell"]]:
            self.try_spell()

        # normalise vector so that diagonal movement is the
        # same speed as horizontal
        if dv.magnitude() != 0:
            dv = dv.normalize() * self.stats.walk_speed

        self.add_velocity(dv)

    def eval_anim(self) -> None:
        if self.walking:
            # use last attack direction if in attack anim, else use walk direction
            direction = self.last_facing.attack if self.attack_cd > 0 else self.last_facing.walk
            proposed_key = "walk-" + direction
        else:
            proposed_key = "idle-" + self.last_facing.overall

        if proposed_key != self.animation_manager.current:
            self.animation_manager.set_animation(proposed_key)

    def on_hit(self, other: Sprite) -> None:
        self.manager.play_sound(sound_name = "effect/hit", volume = 0.2)
        hit_direction = get_closest_direction(pygame.Vector2(other.rect.center) - pygame.Vector2(self.rect.center))
        if not "attack" in self.animation_manager.current: 
            self.animation_manager.set_animation("damage-" + hit_direction)

    def try_attack(self, direction: Direction) -> bool:
        """Attempts an attack, returning True if successful and False if not"""
        current_weapon = self.inventory.primary
        if current_weapon == None: return
        if self.attack_cd <= 0:
            # create attack
            current_weapon.attack(direction)

            self.attack_cd = current_weapon.cooldown_time
            self.last_facing.set("attack", direction)

            # set player animation if avaliable
            if current_weapon.animation_key:
                self.animation_manager.set_animation(current_weapon.animation_key + "-" + direction)
            return True
        return False
    
    def try_spell(self) -> bool:
        """See ``Player.try_attack``"""
        current_spell = self.inventory.spell
        if current_spell == None: return
        if self.spell_cd <= 0:
            current_spell.attack()

            self.spell_cd = current_spell.cooldown_time

            if current_spell.animation_key:
                self.animation_manager.set_animation(current_spell.animation_key + "-" + self.animation_manager.current.split("-")[1])
            return True
        return False
        
    def add_health(self, value: int) -> None:
        self.health += value
        if self.health > self.stats.health:
            self.health = self.stats.health

    def kill(self) -> None:
        super().kill()
        level: Level = self.manager.get_object("level")
        level.parent.set_screen("overview", game_data = level.get_overview_data(), end_type = "die")

    def update(self) -> None:
        super().update()
        self.get_inputs()
        self.attack_cd -= self.manager.dt
        if self.attack_cd < 0:
            self.attack_cd = 0
        self.spell_cd -= self.manager.dt
        if self.spell_cd < 0:
            self.spell_cd = 0

        current_animation = self.animation_manager.current
        if "walk" in current_animation or "idle" in current_animation:
            self.eval_anim()
        else:
            if self.animation_manager.finished:
                self.eval_anim()