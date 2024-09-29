from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..main import Game

import pygame
import random, pickle, os

from engine import Screen, Sprite, Node, ui, Logger
from engine.types import *
from entity import Player, HealthBar
from item import MeleeWeaponAttack, ItemPool, Coin, Health
from world import FloorManager, Tile, Room, WorldItem, Chest, ItemChest, PickupChest
from util import SaveHelper, AutoSaver, parse_spritesheet
from util.constants import *

from .common import TextButtonColours, TextButton, IconText, PersistantGameData, OverviewData, ItemChestData, PickupChestData, WorldItemData
from .settings import SettingsUI

class HealthBarUI(ui.Element):
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

        self.bar_padding = PIXEL_SCALE
        self.shading_size = PIXEL_SCALE

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
            self.bar_padding,
            self.bar_padding,
            (self.player.health / self.player.stats.health) * (self.rect.width - 2 * self.bar_padding),
            self.rect.height - 2 * self.bar_padding
        )
        
        shadow_rect = health_rect.copy()
        shadow_rect.height = self.shading_size
        shadow_rect.bottom = border_rect.height - self.bar_padding

        shading_rect = health_rect.copy()
        shading_rect.width = self.rect.width - 2 * self.bar_padding

        # only have round right if one max health
        right_radius = 4 if self.player.health == self.player.stats.health else 0

        pygame.draw.rect(self.image, self.border_colour, border_rect, border_radius = 4)
        pygame.draw.rect(self.image, self.background_colour, shading_rect, border_radius = 4)
        pygame.draw.rect(self.image, self.health_colour, health_rect, border_bottom_left_radius = 4, border_top_left_radius = 4, border_bottom_right_radius = right_radius, border_top_right_radius = right_radius)
        pygame.draw.rect(self.image, self.shadow_colour, shadow_rect, border_bottom_left_radius = 4, border_bottom_right_radius = right_radius)
        self.style.image = self.image

        self.text.set_text(f"{int(self.player.health)}/{self.player.stats.health}")

class MapUI(ui.Element):
    def __init__(self, parent: Node, style: ui.Style, scale = 32) -> None:
        super().__init__(parent, style = style)

        self.floor_manager: FloorManager = self.manager.get_object("floor-manager")
        self.player: Player = self.manager.get_object("player")
        self.scale = scale

        self.border_size = PIXEL_SCALE

        self.border_colour = UI_DARKBROWN
        self.background_colour = UI_BROWN
        self.room_colour = UI_LIGHTBROWN
        self.unactivated_colour = UI_DARKBROWN

        self.spawn_icon, self.boss_icon, self.done_icon, self.player_icon, self.upgrade_icon = parse_spritesheet(self.manager.get_image("map/icons", 0.5), assume_square=True)

        self.update_map()

        self.explored_text = self.add_child(IconText(
            parent = self,
            text = "0/0",
            icon = self.manager.get_image("map/explored", 0.5),
            icon_alignment = "right",
            padding = 4,
            style = ui.Style(
                font = self.manager.get_font("alagard", 16),
                fore_colour = TEXT_WHITE,
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
        elif "upgrade" in room.tags and room.activated:
            return self.upgrade_icon
        elif room.activated and len(room.enemies) == 0:
            return self.done_icon
        return pygame.Surface((0, 0))

    def update_map(self) -> None:
        self.map_surf = pygame.Surface((self.style.size[0] - self.border_size * 2, self.style.size[1] - self.border_size * 2))
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
        self.image.blit(self.map_surf, (self.border_size, self.border_size))
        self.style.image = self.image

        # explored text
        rooms_completed, total_rooms = self.floor_manager.get_completion_status()
        self.explored_text.set_text(f"{rooms_completed}/{total_rooms}")

class InventoryUI(ui.Element):
    def __init__(self, parent: ui.Element) -> None:
        super().__init__(parent, ui.Style(
            alignment = "bottom-left",
            alpha = 0,
            offset = (16, 16),
        ))

        self.border = 4
        self.padding = 4

        self.primary_size = 96 + (self.border + self.padding) * 2
        self.spell_size = 48 + (self.border + self.padding) * 2

        self.primary_slot = self.add_child(ui.Element(
            parent = self,
            style = ui.Style(
                image = self._draw_slot_image(self.primary_size),
                alignment = "bottom-left"
            )
        ))

        self.spell_slot = self.primary_slot.add_child(ui.Element(
            parent = self.primary_slot,
            style = ui.Style(
                image = self._draw_slot_image(self.spell_size),
                alignment = "top-left",
                offset = (0, -self.spell_size - 8)
            )
        ))

        self.spell_cd_overlay = self.spell_slot.add_child(ui.Element(
            parent = self.spell_slot,
            style = ui.Style(
                size = (self.spell_size - 2 * self.border, self.spell_size - 2 * self.border),
                offset = (4, 4),
                alignment = "bottom-left",
                alpha = 100,
                colour = LIGHTGRAY
            )
        ))

        # store icon key and upgrade
        self.prev_p_state: tuple[str, int] = ("", 0)
        self.prev_s_state: tuple[str, int] = ("", 0)

        self.player: Player = self.manager.get_object("player")

    def _draw_slot_image(self, size: int, icon_key: str = "", n_upgrades: int = 0) -> pygame.Surface:
        slot_image = pygame.Surface((size, size))
        # space around image
        extra_space = self.border + self.padding
        # background
        slot_image.fill(UI_BROWN)
        pygame.draw.rect(slot_image, UI_DARKBROWN, (0, 0, size , size), self.border)

        # icon
        if icon_key:
            icon = self.manager.get_image(icon_key)
            icon = pygame.transform.scale(icon, (size - extra_space * 2, size - extra_space * 2))
            slot_image.blit(icon, (extra_space, extra_space))

        # calculate upgrade space
        u_border = self.border // 2
        u_width = u_border * 2 + PIXEL_SCALE * 2
        u_height = size
        uicon_size = u_width
        u_image = pygame.Surface((u_width, u_height), pygame.SRCALPHA)
        for i in range(3):
            uicon_image = pygame.Surface((uicon_size, uicon_size), pygame.SRCALPHA)
            pygame.draw.rect(uicon_image, PLAYER_GREEN if i < n_upgrades else UI_BROWN, (u_border, u_border, *(uicon_size - u_border * 2,)*2))
            pygame.draw.rect(uicon_image, UI_DARKBROWN, (0, 0, uicon_size, uicon_size), u_border)

            u_image.blit(uicon_image, uicon_image.get_rect(bottom = u_height - i * (uicon_size + self.padding)))

        image = pygame.Surface((u_width + size + self.padding, size), pygame.SRCALPHA)
        image.blit(slot_image, (0, 0))
        image.blit(u_image, (size + self.padding, 0))

        return image

    def update(self) -> None:
        primary = self.player.inventory.primary
        spell = self.player.inventory.spell
        cur_p_state = (primary.icon_key, primary.upgrade_level) if primary else ("", 0)
        cur_s_state = (spell.icon_key, spell.upgrade_level) if spell else ("", 0)

        should_redraw = False
        if cur_p_state != self.prev_p_state:
            self.prev_p_state = cur_p_state
            should_redraw = True

        if cur_s_state != self.prev_s_state:
            self.prev_s_state = cur_s_state
            should_redraw = True

        if should_redraw:
            self.primary_slot.style.image = self._draw_slot_image(self.primary_size, *cur_p_state)
            self.primary_slot.redraw_image()

            self.spell_slot.style.image = self._draw_slot_image(self.spell_size, *cur_s_state)
            self.spell_slot.redraw_image()

        # calculate cooldown progress
        if cur_s_state[0] != "": 
            height = self.player.spell_cd / self.player.inventory.spell.cooldown_time * (self.spell_size - 2 * self.border)
        else:
            height = 0
        self.spell_cd_overlay.style.size = (self.spell_size - 2 * self.border, height)
        self.spell_cd_overlay.redraw_image()

class HudUI(ui.Element):
    def __init__(self, parent: Node) -> None:
        super().__init__(parent, style = ui.Style(alpha = 0, visible = True, size = parent.rect.size))

        self.health_bar = self.add_child(
            HealthBarUI(
                self,
                health_colour = PLAYER_GREEN,
                shadow_colour = PLAYER_DARKGREEN,
                border_colour = UI_DARKBROWN,
                background_colour = UI_BROWN,
                text_colour = UI_DARKBROWN
            )
        )

        self.map = self.add_child(
            MapUI(
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
            icon = self.manager.get_image("map/coin", 0.5),
            icon_alignment = "right",
            padding = 4,
            style = ui.Style(
                font = self.manager.get_font("alagard", 16),
                fore_colour = TEXT_WHITE,
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

        self.pause_text = self.main_element.add_child(ui.Text(
            parent = self.main_element,
            text = "Paused",
            style = ui.Style(
                alignment = "top-center",
                font = self.manager.get_font("alagard", 48),
                offset = (0, TILE_SIZE / 3),
                fore_colour = TEXT_GREEN,
                colour = TEXT_DARKGREEN,
                text_shadow = 3
            )
        ))

        self.divider = self.pause_text.add_child(ui.Element(
            parent = self.pause_text,
            style = ui.Style(
                alignment = "bottom-center",
                offset = (0, - TILE_SIZE / 8),
                colour = BG_DARKNAVY,
                size = (self.main_element.rect.width * 0.8, 4),
            )
        ))

        button_colours = TextButtonColours()

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
            self.settings_ui.on_resize(self.settings_ui.style.size)

    def calculate_settings_size(self) -> pygame.Vector2:
        if self.pause_frame == None:
            return pygame.Vector2(STARTUP_SCREEN_SIZE)
        return pygame.Vector2(self.pause_frame.get_size())

    def _on_resume_click(self) -> None:
        self.parent.toggle_pause()

    def _on_options_click(self) -> None:
        self.toggle_settings()

    def _on_exit_click(self) -> None:
        self.parent.run_autosaver.force_save()
        self.parent.parent.set_screen("menu")

    def _draw_background(self, size: Vec2, border_width: int = 8) -> pygame.Surface:
        surf = pygame.Surface(size)
        surf.fill(BG_NAVY)
        pygame.draw.rect(surf, BG_DARKNAVY, [0, 0, *size], width = border_width)
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
    def __init__(self, game: Game, load_from_file: bool = False) -> None:
        super().__init__(parent = game)
        game_data = None
        if load_from_file and os.path.exists(RUN_SAVE_PATH):
            try:
                game_data: PersistantGameData = pickle.loads(SaveHelper.load_file(RUN_SAVE_PATH, True))
            except pickle.UnpicklingError as e:
                Logger.warn("Error unpickling run data - save data may be corrupted")
                game_data = None

        self.game_surface = pygame.Surface(self.rect.size)

        self.manager.add_groups(["render", "update", "collide", "enemy", "interact"])
        self.manager.add_object("level", self)

        self.item_pool = self.add_child(ItemPool(self))
        self.floor_manager = self.add_child(FloorManager(self, room_size = 12))
        self.floor_manager.generate(game_data.seed if game_data else None)
        self.player: Player = self.manager.get_object("player")
        self.camera = self.add_child(FollowCameraLayered(self, target_sprite = self.player, follow_speed = 0.1))

        self.debug_mode = 0
        self.paused = False

        self.time_in_run = 0
        self.player_hits = 0

        self._add_ui_components()

        if game_data:
            self.load_from_data(game_data)

        self._data_update_counter = 0
        self.run_autosaver = AutoSaver(self, RUN_SAVE_PATH, 60 * 30) # autosave run data every 30 seconds (only noticeable through crashes)
        self.run_autosaver.data = self.get_game_data_encoded()

        self.run_autosaver.force_save()

        self.manager.play_music("music/forest")

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

    def get_game_data(self) -> PersistantGameData:
        world_items = []
        for w_item in [x for x in self.manager.groups["interact"] if isinstance(x, WorldItem)]:
            id = self.item_pool.get_item_id(w_item.item)
            world_items.append(WorldItemData(
                item_id = id,
                upgrade = w_item.item.upgrade_level,
                position = w_item.rect.center
            ))

        item_chests = []
        pickup_chests = []
        for x in self.manager.groups["interact"]:
            if isinstance(x, ItemChest):
                item_chests.append(ItemChestData(
                    position = x.rect.center,
                    item_id = self.item_pool.get_item_id(x.held_item)
                ))
            elif isinstance(x, PickupChest):
                pickup_chests.append(PickupChestData(
                    position = x.rect.center,
                    number = x.number,
                    type = "coin" if isinstance(x, Coin) else "health"
                ))

        p_weapon = self.player.inventory.primary
        s_weapon = self.player.inventory.spell

        return PersistantGameData(
            player_position = self.player.rect.center,
            player_health = self.player.health,
            player_iframes = self.player.iframes,
            weapon_id = self.item_pool.get_item_id(p_weapon),
            spell_id = self.item_pool.get_item_id(s_weapon),
            weapon_upgrade = p_weapon.upgrade_level if p_weapon else 0,
            spell_upgrade = s_weapon.upgrade_level if s_weapon else 0,
            coins = self.player.inventory.coins,
            seed = self.floor_manager.seed,
            time = self.time_in_run,
            player_hits = self.player_hits,
            rooms_discovered = [coord for (coord, room) in self.floor_manager.rooms.items() if room.activated],
            rooms_cleared = [coord for (coord, room) in self.floor_manager.rooms.items() if room.completed],
            coin_pickups = [x.rect.center for x in self.children if isinstance(x, Coin)],
            health_pickups = [x.rect.center for x in self.children if isinstance(x, Health)],
            opened_chests = [x.rect.center for x in self.children if isinstance(x, Chest) and x.opened],
            found_ids = self.item_pool.found_items,
            world_items = world_items,
            item_chests = item_chests,
            pickup_chests = pickup_chests
        )
    
    def get_game_data_encoded(self) -> None:
        data = self.get_game_data()
        return SaveHelper.encode_data(pickle.dumps(data))

    def load_from_data(self, data: PersistantGameData) -> None:
        # load player info
        self.player.rect.center = data.player_position
        self.player.health = data.player_health
        self.player.iframes = data.player_iframes
        self.player.inventory.coins = data.coins
        
        # set player weapons
        if data.weapon_id == -1:
            self.player.inventory.remove_weapon(0)
        else:
            self.player.inventory.set_weapon(0, self.item_pool.get_item(data.weapon_id))
            self.player.inventory.primary.upgrade(data.weapon_upgrade)

        if data.spell_id == -1:
            self.player.inventory.remove_weapon(1)
        else:
            self.player.inventory.set_weapon(1, self.item_pool.get_item(data.spell_id))
            self.player.inventory.spell.upgrade(data.spell_upgrade)

        # load room states
        for room_coord in data.rooms_discovered:
            room = self.floor_manager.rooms[room_coord]
            if room_coord in data.rooms_cleared:
                room.force_completion()
            else:
                room.activate()

        # load run time
        self.time_in_run = data.time
        # load score
        self.player_hits = data.player_hits

        # set camera position
        self.camera.pos = pygame.Vector2(data.player_position)

        # add pickups
        for pos in data.coin_pickups:
            self.add_child(Coin(self, pos, 0))
        for pos in data.health_pickups:
            self.add_child(Health(self, pos))

        # add chests
        for pos in data.opened_chests:
            chest = self.add_child(Chest(self, pos))
            chest.open()

        for chest_data in data.item_chests:
            item = self.item_pool.get_item(chest_data.item_id)
            self.add_child(ItemChest(self, chest_data.position, item))
        
        for chest_data in data.pickup_chests:
            pickup = Coin if chest_data.type == "coin" else Health
            self.add_child(PickupChest(self, chest_data.position, pickup, chest_data.number))

        # add items
        for item_data in data.world_items:
            item = self.add_child(self.item_pool.get_item(item_data.item_id)(self))
            item.upgrade(item_data.upgrade)
            self.add_child(WorldItem(self, item_data.position, item))
        self.item_pool.restore_from_found(data.found_ids)

    def get_overview_data(self) -> OverviewData:
        return OverviewData(
            score = self.calculate_score(),
            time = self.time_in_run,
            game_data = self.get_game_data(),
            completed = self.is_completed()
        )
    
    def calculate_score(self) -> int:
        return int(SCORE_INITIAL + self.player_hits * SCORE_DAMAGE + self.player.inventory.coins * SCORE_COIN + self.time_in_run * SCORE_PER_SECOND) + (SCORE_COMPLETION if self.is_completed() else 0)

    def is_completed(self) -> bool:
        rooms_completed, total_rooms = self.floor_manager.get_completion_status()
        return rooms_completed == total_rooms

    def can_autosave(self) -> bool:
        current_room = self.floor_manager.get_room_at_world_pos(self.player.rect.center)
        return current_room.completed

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
        if key == self.manager.keybinds["pause"]:
            self.toggle_pause()

        if self.paused:
            self.pause_ui.on_key_down(key, unicode)
            return
            
        if key == self.manager.keybinds["map-zoom-in"]:
            self.hud_ui.map.increase_scale()

        elif key == self.manager.keybinds["map-zoom-out"]:
            self.hud_ui.map.decrease_scale()

        elif key == pygame.K_F3 and IN_DEBUG:
            self.cycle_debug()

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

    def on_scroll(self, dx: int, dy: int) -> None:
        if self.paused:
            self.pause_ui.on_scroll(dx, dy)
        else:
            self.master_ui.on_scroll(dx, dy)

    def debug(self) -> None:
        if self.debug_mode == 0: return

        # render hitboxes of anything that has a rect
        for item in self.get_all_children():
            if not hasattr(item, "rect") or item.rect == None: continue
            # ignore self
            if item == self: continue
            # ignore specific elements
            if isinstance(item, (ui.Element, HealthBar)): continue

            # draw z indexes on debug 3
            if self.debug_mode == 3 and hasattr(item, "z_index"):
                text_pos = self.camera.convert_coords(pygame.Vector2(item.rect.center))
                if self.rect.collidepoint(text_pos):
                    z_text = self.manager.get_font("alagard", 16).render(str(item.z_index), False, GREEN)
                    self.game_surface.blit(z_text, z_text.get_rect(center = text_pos))

            # ignore tiles unless on debug 2
            if isinstance(item, Tile) and self.debug_mode != 2: continue

            # draw active damage hitboxes
            outline_colour = RED if isinstance(item, MeleeWeaponAttack) and item.in_hit_frames() else BLUE

            # draw collision boxes
            pygame.draw.rect(self.game_surface, outline_colour, self.camera.convert_rect(item.rect), width = 1)
            # draw hitboxes
            if hasattr(item, "hitbox"):
                pygame.draw.rect(self.game_surface, RED, self.camera.convert_rect(item.hitbox), width = 1)
            # draw facing directions
            if hasattr(item, "direction") and isinstance(item.direction, float):
                end = item.rect.center + pygame.Vector2(32, 0).rotate(-item.direction)
                pygame.draw.line(self.game_surface, RED, self.camera.convert_coords(item.rect.center), self.camera.convert_coords(end), 1)

        # and also draw room rects
        if self.debug_mode == 2:
            for room in self.floor_manager.rooms.values():
                pygame.draw.rect(self.game_surface, GREEN, self.camera.convert_rect(room.bounding_rect), 1)
                pygame.draw.rect(self.game_surface, GREEN, self.camera.convert_rect(room.inside_rect), 3)

    def update(self) -> None:
        # check for pause override
        if self.paused:
            self.pause_ui.update()
            return
        
        # update all sprites in update group
        self.manager.groups["update"].update()
        self.master_ui.update()
        self.floor_manager.update()

        # update run data every 0.5 seconds
        self.run_autosaver.update()
        self._data_update_counter += self.manager.dt
        if self._data_update_counter > 30 and self.can_autosave():
            self.run_autosaver.data = self.get_game_data_encoded()
            self._data_update_counter = 0

        # add run time
        self.time_in_run += self.manager.dt / 60

    def render(self, surface: pygame.Surface) -> None:
        # clear game surface, which also fills in walls
        self.game_surface.fill(UI_DARKBROWN)

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