from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..main import Game

import pygame
import random

from util.constants import *
from engine import Screen, Sprite, Node, Logger, ui
from engine.types import *
from entity import Player
from world import FloorManager, Tile, Room

from .common import TextButtonColours, TextButton, IconText
from .settings import SettingsUI

class HealthBar(ui.Element):
    BAR_PADDING = 4
    def __init__(self, parent: Node, health_colour: Colour, shadow_colour: Colour, border_colour: Colour, background_colour: Colour, text_colour: Colour) -> None:
        super().__init__(
            parent = parent,
            style = ui.Style(
                alignment = "top-right",
                image = pygame.Surface((256, 32)),
                stretch_type = "none",
                offset = (16, 16),
            )
        )

        self.text = self.add_child(ui.Text(self, text = "0/0", style = ui.Style(
            alignment = "center-center",
            fore_colour = border_colour,
            font = self.manager.get_font("alagard", 16)
        )))

        self.health_colour = health_colour
        self.shadow_colour = shadow_colour
        self.border_colour = border_colour
        self.background_colour = background_colour
        self.text_colour = text_colour

        self.player = self.manager.get_object("player")

    def update(self) -> None:
        self.image = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        border_rect = self.image.get_rect()
        
        health_rect = pygame.Rect(
            self.BAR_PADDING,
            self.BAR_PADDING,
            (self.player.health / self.player.stats.health) * (self.rect.width - 2 * self.BAR_PADDING),
            self.rect.height - 2 * self.BAR_PADDING
            )
        
        shadow_rect = health_rect.copy()
        shadow_rect.height = self.BAR_PADDING * 2
        shadow_rect.bottom = border_rect.height - self.BAR_PADDING

        shading_rect = health_rect.copy()
        shading_rect.width = self.rect.width - 2 * self.BAR_PADDING

        # only have round right if one max health
        right_radius = 4 if self.player.health == self.player.stats.health else 0

        pygame.draw.rect(self.image, self.border_colour, border_rect, border_radius = 4)
        pygame.draw.rect(self.image, self.background_colour, shading_rect, border_radius = 4)
        pygame.draw.rect(self.image, self.health_colour, health_rect, border_bottom_left_radius = 4, border_top_left_radius = 4, border_bottom_right_radius = right_radius, border_top_right_radius = right_radius)
        pygame.draw.rect(self.image, self.shadow_colour, shadow_rect, border_bottom_left_radius = 4, border_bottom_right_radius = right_radius)
        self.style.image = self.image

        self.text.set_text(f"{self.player.health}/{self.player.stats.health}")

class Map(ui.Element):
    BORDER_SIZE = 4
    def __init__(self, parent: Node, style: ui.Style, scale = 32) -> None:
        super().__init__(parent, style = style)

        self.floor_manager: FloorManager = self.manager.get_object("floor-manager")
        self.player: Player = self.manager.get_object("player")
        self.scale = scale

        self.border_colour = (51, 22, 31)
        self.background_colour = (91, 49, 56)
        self.room_colour = (162, 109, 91)
        self.unactivated_colour = self.border_colour

        self.player_icon = pygame.transform.scale_by(self.manager.get_image("map/player_icon"), 0.5)
        self.spawn_icon = self.manager.get_image("map/spawn")
        self.done_icon = self.manager.get_image("map/check")
        self.boss_icon = self.manager.get_image("map/boss")

        self.update_map()

        self.explored_text = self.add_child(IconText(
            parent = self,
            text = "0/0",
            icon = self.manager.get_image("map/explored"),
            icon_alignment = "right",
            padding = 4,
            style = ui.Style(
                font = self.manager.get_font("alagard", 16),
                fore_colour = (218, 224, 234),
                alignment = "bottom-right",
                offset = (TILE_SIZE / 8, TILE_SIZE / 8)
            )
        ))

    def scale_room_to_map(self, room_coord: Vec2) -> None:
        "Scale a room coord into map coordinates"
        scaled_room_coords = pygame.Vector2(room_coord) * (self.scale + self.scale / 4) + pygame.Vector2(self.map_surf.get_size()) / 2 - pygame.Vector2(0.5, 0.5) * self.scale
        scaled_player_position = (pygame.Vector2(self.player.rect.center) / TILE_SIZE // self.floor_manager.room_size) * (self.scale + self.scale / 4)
        return scaled_room_coords - scaled_player_position

    def _get_room_colour(self, room: Room) -> None:
        if room.activated:
            return self.room_colour
        else:
            return self.unactivated_colour

    def _get_room_icon(self, room: Room) -> None:
        if "spawn" in room.tags:
            return self.spawn_icon
        elif "boss" in room.tags and room.activated:
            return self.boss_icon
        elif room.activated and len(room.enemies) == 0:
            return self.done_icon
        return pygame.Surface((0, 0))

    def update_map(self) -> None:
        self.map_surf = pygame.Surface((self.style.size[0] - self.BORDER_SIZE * 2, self.style.size[1] - self.BORDER_SIZE * 2))
        self.map_surf.fill(self.background_colour)

        player_pos = (0, 0)

        for room_coord, room in self.floor_manager.rooms.items():
            # draw room
            scaled_coord = self.scale_room_to_map(room_coord)

            room_rect = pygame.Rect(*scaled_coord, self.scale, self.scale)

            colour = self._get_room_colour(room)
            pygame.draw.rect(self.map_surf, colour, room_rect)

            icon = self._get_room_icon(room)
            self.map_surf.blit(icon, icon.get_rect(center = room_rect.center))

            # draw connections
            for connection in room.connections:
                con_rect = pygame.Rect(0, 0, self.scale / 4, self.scale / 4)
                if connection == "left":
                    con_rect.right = room_rect.left
                    con_rect.centery = room_rect.centery
                elif connection == "right":
                    con_rect.left = room_rect.right
                    con_rect.centery = room_rect.centery
                elif connection == "up":
                    con_rect.bottom = room_rect.top
                    con_rect.centerx = room_rect.centerx
                elif connection == "down":
                    con_rect.top = room_rect.bottom
                    con_rect.centerx = room_rect.centerx

                pygame.draw.rect(self.map_surf, colour, con_rect)

            if room.bounding_rect.colliderect(self.player.rect):
                rel = (pygame.Vector2(self.player.rect.center) - pygame.Vector2(room.bounding_rect.topleft)) / (self.floor_manager.room_size * TILE_SIZE) * self.scale
                player_pos = rel + scaled_coord

        self.map_surf.blit(self.player_icon, self.player_icon.get_rect(center = player_pos))

    def increase_scale(self) -> None:
        self.scale *= 2
        if self.scale > 64:
            self.scale = 64

    def decrease_scale(self) -> None:
        self.scale /= 2
        if self.scale < 4:
            self.scale = 4

    def update(self) -> None:
        super().update()
        self.image = pygame.Surface(self.style.size, pygame.SRCALPHA)
        self.update_map()
        # draw borders
        pygame.draw.rect(self.image, self.border_colour, [0, 0, *self.style.size], border_radius = 4)
        self.image.blit(self.map_surf, (self.BORDER_SIZE, self.BORDER_SIZE))
        self.style.image = self.image

        # explored text
        total_rooms = len(self.floor_manager.rooms)
        rooms_completed = len(list(filter(lambda coord_room: coord_room[1].activated and coord_room[1].completed, self.floor_manager.rooms.items())))
        self.explored_text.set_text(f"{rooms_completed}/{total_rooms}")

class InventoryUI(ui.Element):
    MAIN_SIZE = 96
    SECOND_SIZE = 48
    def __init__(self, parent: ui.Element) -> None:
        super().__init__(parent, ui.Style(
            alignment = "bottom-left",
            alpha = 0,
            offset = (16, 16),
        ))

        self.main_slot = self.add_child(ui.Element(
            parent = self,
            style = ui.Style(
                image = self._draw_slot_image(InventoryUI.MAIN_SIZE),
                alignment = "bottom-left"
            )
        ))

        self.secondary_slot = self.main_slot.add_child(ui.Element(
            parent = self.main_slot,
            style = ui.Style(
                image = self._draw_slot_image(InventoryUI.SECOND_SIZE),
                alignment = "top-right",
                offset = (-InventoryUI.SECOND_SIZE / 2, -InventoryUI.SECOND_SIZE / 2)
            )
        ))

        self.prev_main_slot: str = ""
        self.prev_secondary_slot: str = ""
        self.prev_selected_index: int = 0

        self.player: Player = self.manager.get_object("player")

    def _draw_slot_image(self, size: int, icon_key: str = "", is_selected = False) -> pygame.Surface:
        image = pygame.Surface((size, size))
        image.fill((162, 109, 91) if is_selected else (91, 49, 56))
        pygame.draw.rect(image, (51, 22, 31), (0, 0, size, size), 4)

        if icon_key:
            icon = self.manager.get_image(icon_key)
            icon = pygame.transform.scale(icon, (size - 16, size - 16))
            image.blit(icon, (8, 8))
        return image

    def update(self) -> None:
        current_main_slot = self.player.inventory.primary.icon_key
        current_secondary_slot = self.player.inventory.secondary.icon_key
        current_selected_index = self.player.selected_weapon_index

        should_redraw = False
        if current_main_slot != self.prev_main_slot:
            self.prev_main_slot = current_main_slot
            should_redraw = True

        if current_secondary_slot != self.prev_secondary_slot:
            self.prev_secondary_slot = current_secondary_slot
            should_redraw = True

        if current_selected_index != self.prev_selected_index:
            self.prev_selected_index = current_selected_index
            should_redraw = True

        if should_redraw:
            self.main_slot.style.image = self._draw_slot_image(InventoryUI.MAIN_SIZE, current_main_slot, current_selected_index == 0)
            self.main_slot.redraw_image()

            self.secondary_slot.style.image = self._draw_slot_image(InventoryUI.SECOND_SIZE, current_secondary_slot, current_selected_index == 1)
            self.secondary_slot.redraw_image()

class HudUI(ui.Element):
    BAR_PADDING = 4
    def __init__(self, parent: Node) -> None:
        super().__init__(parent, style = ui.Style(alpha = 0, visible = True, size = parent.rect.size))

        self.health_bar = self.add_child(
            HealthBar(
                self,
                health_colour = (99, 169, 65),
                shadow_colour = (46, 109, 53),
                border_colour = (51, 22, 31),
                background_colour = (91, 49, 56),
                text_colour = (51, 22, 31)
            )
        )

        self.map = self.add_child(
            Map(
                parent = self,
                style = ui.Style(
                    alignment = "top-right",
                    offset = (self.health_bar.style.offset[0], self.health_bar.rect.bottom + 8),
                    size = (256, 256),
                )
            )
        )

        self.coin_text = self.add_child(IconText(
            parent = self,
            text = "0",
            icon = self.manager.get_image("map/coin"),
            icon_alignment = "right",
            padding = 4,
            style = ui.Style(
                font = self.manager.get_font("alagard", 16),
                fore_colour = (218, 224, 234),
                alignment = "top-right",
                offset = (self.map.explored_text.style.offset[0] + self.map.style.offset[0], self.map.rect.bottom + 8)
            )
        ))

        self.inventory_ui = self.add_child(InventoryUI(parent = self))

        self.floor: FloorManager = self.manager.get_object("floor-manager")
        self.player: Player = self.manager.get_object("player")

    def update(self) -> None:
        super().update()
        # coin text
        self.coin_text.set_text(f"{self.player.inventory.coins:,}")

class PauseUI(ui.Element):
    def __init__(self, parent: Level) -> None:
        # store the image of the frame paused on when this menu was opened
        self.pause_frame = None

        super().__init__(parent, style = ui.Style(
            position = "absolute",
            size = parent.rect.size,
            visible = False
        ))

        self.main_element = self.add_child(ui.Element(
            parent = self,
            style = ui.Style(
                image = self._draw_background((TILE_SIZE * 3.5, TILE_SIZE * 3.5)),
                # image = draw_background((TILE_SIZE * 3.5, TILE_SIZE * 3.5), pixel_scale = 4, line_thickness = 0),
                alignment = "center-center",
            )
        ))

        button_colours = TextButtonColours()

        self.pause_text = self.main_element.add_child(ui.Text(
            parent = self.main_element,
            text = "Paused",
            style = ui.Style(
                alignment = "top-center",
                font = self.manager.get_font("alagard", 54),
                offset = (0, TILE_SIZE / 3),
                fore_colour = button_colours.colour,
                colour = button_colours.colour_shadow,
                text_shadow = 2
            )
        ))

        self.divider = self.pause_text.add_child(ui.Element(
            parent = self.pause_text,
            style = ui.Style(
                alignment = "bottom-center",
                offset = (0, - TILE_SIZE / 8),
                colour = (26, 30, 36),
                size = (self.main_element.rect.width * 0.8, 4),
            )
        ))

        self.resume_button = self.main_element.add_child(TextButton(
            parent = self.main_element,
            yoffset = self.pause_text.style.offset[1] + self.pause_text.rect.height + TILE_SIZE / 4,
            colours = button_colours,
            text = "Resume",
            on_click = self._on_resume_click
        ))

        self.options_button = self.main_element.add_child(TextButton(
            parent = self.main_element,
            yoffset = self.resume_button.style.offset[1] + self.resume_button.rect.height,
            colours = button_colours,
            text = "Options",
            on_click = self._on_options_click
        ))

        self.exit_button = self.main_element.add_child(TextButton(
            parent = self.main_element,
            yoffset = self.options_button.style.offset[1] + self.options_button.rect.height,
            colours = button_colours,
            text = "Exit",
            on_click = self._on_exit_click
        ))

        self.settings_ui = self.add_child(SettingsUI(self, self.calculate_settings_size(), self.toggle_settings))
        self.in_settings = False
        self.toggle_settings(False)
    
    def toggle_settings(self, override: Optional[bool] = None) -> None:
        """Toggles visibility of settings menu. Will use override value if provided"""
        self.settings_ui.style.visible = override if override != None else not self.settings_ui.style.visible
        self.in_settings = self.settings_ui.style.visible
        if self.settings_ui.style.visible == True:
            self.settings_ui.style.size = self.calculate_settings_size()
            for item in self.settings_ui.get_all_children():
                item.redraw_image()

    def calculate_settings_size(self) -> pygame.Vector2:
        if self.pause_frame == None:
            return pygame.Vector2()
        return pygame.Vector2(self.pause_frame.get_size())

    def _on_resume_click(self) -> None:
        self.parent.toggle_pause()

    def _on_options_click(self) -> None:
        self.toggle_settings()

    def _on_exit_click(self) -> None:
        self.parent.parent.set_screen("menu")

    def _draw_background(self, size: Vec2, border_width: int = 8) -> pygame.Surface:
        surf = pygame.Surface(size)
        surf.fill((37, 44, 55))
        pygame.draw.rect(surf, (26, 30, 36), [0, 0, *size], width = border_width)
        return surf

    def _blur_image(self, image: pygame.Surface, strength: int = 4) -> pygame.Surface:
        return pygame.transform.box_blur(image, strength)

    def on_mouse_down(self, mouse_button: int) -> None:
        if self.in_settings:
            self.settings_ui.on_mouse_down(mouse_button)
        else:
            super().on_mouse_down(mouse_button)

    def toggle(self, pause_frame: pygame.Surface) -> None:
        self.toggle_settings(False)
        self.style.visible = not self.style.visible
        self.pause_frame = pause_frame
        self.style.size = pause_frame.get_size()
        if self.style.visible:
            for item in self.get_all_children():
                item.redraw_image()

    def redraw_image(self) -> None:
        super().redraw_image()

        if self.pause_frame:
            self.image = self._blur_image(self.pause_frame)

        if hasattr(self, "settings_ui") and self.in_settings:
            self.settings_ui.style.size = self.calculate_settings_size()
    
    def update(self) -> None:
        if not self.in_settings:
            super().update()
        else:
            self.settings_ui.update()

    def render(self, surface: pygame.Surface) -> None:
        # save what the screen looks like without me
        self.pause_frame = surface.copy()
        super().render(surface)

class Level(Screen):
    def __init__(self, game: Game, debug_mode: int = 0) -> None:
        super().__init__(parent = game)
        self.game_surface = pygame.Surface(self.rect.size)

        self.manager.add_groups(["render", "update", "collide", "enemy"])
        self.manager.add_object("level", self)

        self.floor_manager = self.add_child(FloorManager(self, room_size = 12))
        self.floor_manager.generate()
        self.player = self.manager.get_object("player")
        self.camera = self.add_child(FollowCameraLayered(self, target_sprite = self.player, follow_speed = 0.1))

        self.debug_mode = 0
        self.paused = False

        self._add_ui_components()

        for _ in range(debug_mode):
            self.cycle_debug()

        self.manager.stop_music()

    def _add_ui_components(self) -> None:
        self.master_ui = ui.Element(
            self,
            style = ui.Style(
                size = self.rect.size,
                alpha = 0
            )
        )

        self.hud_ui = self.master_ui.add_child(HudUI(self.master_ui))
        self.pause_ui = PauseUI(self)

    def cycle_debug(self) -> None:
        """
        Cycles current debug mode.

        - 0: off
        - 1: draw hitboxes
        - 2: draw hitboxes including tiles and room boxes
        - 3: draw z-indexes
        """
        if not IN_DEBUG: return
        self.debug_mode += 1
        if self.debug_mode > 3:
            self.debug_mode = 0

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_ui.toggle(self.game_surface)

    def on_key_down(self, key: int, unicode: str) -> None:
        if key == pygame.K_ESCAPE:
            self.toggle_pause()
            
        elif key == pygame.K_F3:
            self.cycle_debug()

        elif key == pygame.K_EQUALS:
            self.hud_ui.map.increase_scale()

        elif key == pygame.K_MINUS:
            self.hud_ui.map.decrease_scale()

    def on_resize(self, new_res: Vec2) -> None:
        super().on_resize(new_res)
        # remake game surface to new size
        self.game_surface = pygame.Surface(new_res)
        # recalibrate camera
        self.camera.set_screen_size(new_res)

        self.master_ui.style.size = new_res
        for sub_menu in self.master_ui.children:
            sub_menu.style.size = new_res

        self.master_ui.on_resize(new_res)

        if self.paused:
            self.pause_ui.style.size = new_res
            # extra render step to sync up menu
            self.render(pygame.Surface((1, 1)))
            self.pause_ui.on_resize(new_res)

    def on_mouse_down(self, button: int) -> None:
        if self.paused:
            self.pause_ui.on_mouse_down(button)
        else:
            self.master_ui.on_mouse_down(button)

    def on_mouse_up(self, button: int) -> None:
        super().on_mouse_up(button)
        if self.paused:
            self.pause_ui.on_mouse_up(button)
        else:
            self.master_ui.on_mouse_up(button)

    def debug(self) -> None:
        if self.debug_mode == 0: return

        # render hitboxes of anything that has a rect
        for item in self.get_all_children():
            if not hasattr(item, "rect") or item.rect == None: continue
            # ignore self
            if item == self: continue
            # ignore ui elements
            if isinstance(item, ui.Element): continue

            # draw z indexes on debug 3
            if self.debug_mode == 3 and hasattr(item, "z_index"):
                text_pos = self.camera.convert_coords(pygame.Vector2(item.rect.center))
                if self.rect.collidepoint(text_pos):
                    z_text = self.manager.get_font("alagard", 16).render(str(item.z_index), False, (0, 255, 0))
                    self.game_surface.blit(z_text, z_text.get_rect(center = text_pos))

            # ignore tiles unless on debug 2
            if isinstance(item, Tile) and self.debug_mode != 2: continue

            # draw hitboxes
            pygame.draw.rect(self.game_surface, (0, 0, 255), self.camera.convert_rect(item.rect), width = 1)

        # and also draw room rects
        if self.debug_mode == 2:
            for room in self.floor_manager.rooms.values():
                pygame.draw.rect(self.game_surface, (0, 255, 0), self.camera.convert_rect(room.bounding_rect), 1)
                pygame.draw.rect(self.game_surface, (0, 255, 0), self.camera.convert_rect(room.inside_rect), 3)

    def update(self) -> None:
        # check for pause override
        if self.paused:
            self.pause_ui.update()
            return
        
        # update all sprites in update group
        self.manager.groups["update"].update()
        self.master_ui.update()
        self.floor_manager.update()

    def render(self, surface: pygame.Surface) -> None:
        # clear game surface
        self.game_surface.fill((51, 22, 31))

        # render objects with layered camera
        self.camera.render(
            surface = self.game_surface,
            sprite_group = self.manager.groups["render"]
        )

        # draw debug elements
        self.debug()

        # render GUI elements
        self.master_ui.render(self.game_surface)

        # render pause ui
        if self.paused:
            self.pause_ui.render(self.game_surface)

        # render to window
        surface.blit(self.game_surface, (0, 0))

class FollowCameraLayered(Sprite):
    def __init__(self, parent: Node, target_sprite: Sprite, follow_speed: float = 0.1, tolerence: float = 5) -> None:
        super().__init__(parent = parent, groups=["update"])
        self.id = "camera"

        self.target = target_sprite
        self.pos = pygame.Vector2(target_sprite.rect.center)
        self.follow_speed = follow_speed
        self.tolerence = tolerence

        self.set_screen_size(self.parent.rect.size)

        self.offset = pygame.Vector2()

        self.shake_timer = 0
        self.shake_intensity = 0

    def update(self) -> None:
        # move camera closer to target
        self.pos += self.manager.dt * (self.target.rect.center - self.pos) * self.follow_speed

        # implement shake
        if self.shake_timer > 0:
            self.shake_timer -= self.manager.dt
            self.pos += pygame.Vector2(random.randrange(-self.shake_intensity, self.shake_intensity), random.randrange(-self.shake_intensity, self.shake_intensity))

    def set_screen_size(self, new_size: Vec2) -> None:
        """Set new screen size to center camera on"""
        self.half_screen_size = pygame.Vector2(new_size[0] // 2, new_size[1] // 2)

    def convert_coords(self, old_coords: Vec2) -> pygame.Vector2:
        """Converts absolute world coords to scaled coords on screen"""
        return pygame.Vector2(
            old_coords[0] - (int(self.pos.x) - self.half_screen_size.x),
            old_coords[1] - (int(self.pos.y) - self.half_screen_size.y)
        )
    
    def convert_rect(self, rect: pygame.Rect | pygame.FRect) -> pygame.Rect | pygame.FRect:
        """See convert_coords"""
        new = rect.copy()
        new.topleft = self.convert_coords(rect.topleft)
        return new
    
    def shake(self, intensity: float, duration: float) -> None:
        """Shake the camera with `intensity` pixel offset for `duration` frames"""
        self.shake_intensity = intensity
        self.shake_timer = duration

    def render(self, surface: pygame.Surface, sprite_group: pygame.sprite.Group) -> None:
        # render sprites centered on camera position
        self.offset.x = int(self.pos.x) - self.half_screen_size.x
        self.offset.y = int(self.pos.y) - self.half_screen_size.y

        # render sprites sorted in y position and z index
        surface.blits(
            (s.image, (s.rect.x - self.offset.x + s.render_offset[0], s.rect.y - self.offset.y + s.render_offset[1]))
            for s in sorted(sprite_group.sprites(), key = lambda x: (x.z_index, x.rect.centery))
        )