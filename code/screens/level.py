
import pygame
import random, math
from util.constants import *
from engine import Screen, Sprite, Node, ui
from engine.types import Direction
from entity import Player, Enemy
from world import Tile

class HealthBar(ui.Element):
    BAR_PADDING = 4
    def __init__(self, parent, health_colour, shadow_colour, border_colour, background_colour, text_colour):
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

        self.player = self.manager.get_object_from_id("player")

    def update(self):
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

        self.text.set_text(f"{self.player.health}/{self.player.stats.health}")

class HudUI(ui.Element):
    BAR_PADDING = 4
    def __init__(self, parent):
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

class DebugUI(ui.Element):
    def __init__(self, parent):
        super().__init__(parent, style = ui.Style(alpha = 0, visible = False, size = parent.rect.size))

        self.fps = self.add_child(ui.Text(
            parent = self,
            text = "loading fps...",
            style = ui.Style(
                font = self.manager.get_font("alagard", 16),
                fore_colour = (255, 255, 255),
                alignment= "top-left",
                )
            )
        )
        self.position = self.add_child(ui.Text(
            parent = self,
            text = "loading position...",
            style = ui.Style(
                font = self.manager.get_font("alagard", 16),
                fore_colour = (255, 255, 255),
                alignment = "top-left",
                offset = (0, self.fps.rect.bottom),
            )
        ))

        self.update_timer = 0
        
        self.player: Player = self.manager.get_object_from_id("player")

    def update(self):
        self.update_timer += self.manager.dt
        if self.update_timer >= 20:
            self.fps.set_text(f"{round(60 / self.manager.dt)} FPS")
            self.update_timer = 0

        self.position.set_text(f"x: {round(self.player.pos.x)} y: {round(self.player.pos.y)}")

room_directions: list[Direction] = ["left", "right", "up", "down"]
opposite_directions: dict[Direction, Direction] = {"left": "right", "right": "left", "up": "down", "down": "up"}
direction_vector: dict[Direction, tuple[int, int]] = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}

class Room(Node):
    def __init__(self, parent, origin: tuple[int, int], room_size: int, forced_doors: list[Direction] = [], blacklisted_doors: list[Direction] = []):
        super().__init__(parent)

        self.rect = pygame.Rect(*origin, TILE_SIZE * room_size, TILE_SIZE * room_size)
        self.type = type
        self.room_size = room_size
        self.origin = origin # stored as room coords

        self.enemies = []
        self.player: Player = self.manager.get_object_from_id("player")
        self.connections: list[Direction] = []
        self.door_positions: list[tuple[int, int]] = []

        self._activated = False

        self.gen_connections_random(forced_doors, blacklisted_doors)
        self.add_tiles()

    def gen_connections_random(self, forced_doors, blacklisted_doors):
        for dir in forced_doors:
            self.connections.append(dir)

        dv = pygame.Vector2(self.origin) + pygame.Vector2(0.5, 0.5)
        distance_from_origin = dv.magnitude()

        # scale max connections based on distance from the origin
        n_rooms = max(int(4 - distance_from_origin / 2), 0)

        for _ in range(n_rooms):
            con = random.choice(room_directions)
            if con in self.connections or con in blacklisted_doors: continue
            self.connections.append(con)

    def add_tiles(self):
        self.add_doors()
        for n in range(self.room_size):
            s = pygame.Surface((TILE_SIZE, TILE_SIZE))
            s.fill((255, 255, 255))
            self.add_tile(s, (n, 0))
            self.add_tile(s, (n, self.room_size - 1))
            self.add_tile(s, (0, n))
            self.add_tile(s, (self.room_size - 1, n))

    def add_doors(self):
        "Generate the relative positions of 'doors'"
        for connection in self.connections:
            second_offset = ()

            x = y = 0
            # bunch of hard coding
            if connection == "up":
                x = self.room_size // 2
                second_offset = (-1, 0)
            elif connection == "down":
                x = self.room_size // 2
                y = self.room_size - 1
                second_offset = (-1, 0)
            elif connection == "left":
                y = self.room_size // 2
                second_offset = (0, -1)
            elif connection == "right":
                x = self.room_size - 1
                y = self.room_size // 2
                second_offset = (0, -1)

            self.door_positions.append((x, y))
            self.door_positions.append((x + second_offset[0], y + second_offset[1]))

    def add_tile(self, image, relative_position):
        # convert relative grid coords to world coords
        position = pygame.Vector2(self.origin) * TILE_SIZE * self.room_size + pygame.Vector2(relative_position) * TILE_SIZE
        # check if position is in a door
        if relative_position in self.door_positions: return
        # add tile
        Tile(self, image, position)

    def activate(self):
        self._activated = True

    def update(self):
        if self.player.rect.colliderect(self.rect) and not self._activated:
            self.activate()

class FloorManager(Node):
    def __init__(self, parent, room_size = 8):
        super().__init__(parent)
        if room_size % 2 == 1:
            raise ValueError("Room size must be even.")
        self.room_size = room_size

        self.rooms: dict[tuple[int, int], Room] = {}

    def generate(self):
        "Generate a floor"
        connection_stack = []

        self.spawn_room = self._gen_1x1((0, 0))
        for con in self.spawn_room.connections  :
            connection_stack.append((self.spawn_room.origin, con))

        while connection_stack:
            room_pos, connection = connection_stack.pop()
            new_room_offset = direction_vector[connection]
            new_room_pos = room_pos[0] + new_room_offset[0], room_pos[1] + new_room_offset[1]

            if new_room_pos in self.rooms: continue

            new_room = self._gen_1x1(new_room_pos)

            # push new room connections to stack
            for con in new_room.connections:
                connection_stack.append((new_room.origin, con))

        self.player = self.add_child(Player(self, self.spawn_room.rect.center - pygame.Vector2(TILE_SIZE / 2, TILE_SIZE / 2)))

    def _gen_1x1(self, origin) -> Room:
        # look through neighbours and force connections with them
        forced_connections = []
        blacklisted_connections = []
        for direction, vector in direction_vector.items():
            neighbour_pos = origin[0] + vector[0], origin[1] + vector[1]
            if neighbour_pos in self.rooms:
                neighbour_room = self.rooms[neighbour_pos]
                if opposite_directions[direction] in neighbour_room.connections:
                    forced_connections.append(direction)
                else:
                    blacklisted_connections.append(direction)

        room = Room(self, origin, self.room_size, forced_doors = forced_connections, blacklisted_doors = blacklisted_connections)
        self.rooms[origin] = room
        return room

class Level(Screen):
    def __init__(self, game, debug_enabled = False):
        super().__init__(parent = game)
        self.game_surface = pygame.Surface(game.window.get_size())

        self.manager.add_groups(["render", "update", "collide", "enemy"])
        self.manager.add_object("level", self)

        self.floor_manager = self.add_child(FloorManager(self, room_size = 10))
        self.floor_manager.generate()
        self.player = self.manager.get_object_from_id("player")
        self.camera = self.add_child(FollowCameraLayered(self, target_sprite = self.player, follow_speed = 0.1))

        self.debug_enabled = False

        self._add_ui_components()
        # self._gen_test_map()

        if debug_enabled:
            self.toggle_debug()

        self.manager.stop_music()

    def _add_ui_components(self):
        self.master_ui = ui.Element(
            self,
            style = ui.Style(
                size = self.rect.size,
                alpha = 0
            )
        )

        self.debug_ui = self.master_ui.add_child(DebugUI(self.master_ui))
        self.hud_ui = self.master_ui.add_child(HudUI(self.master_ui))

    def toggle_debug(self):
        self.debug_ui.style.visible = not self.debug_ui.style.visible
        self.debug_enabled = not self.debug_enabled

    # TEMP ---------------------!!
    def _gen_test_map(self, n = 10):
        for i in range(n):
            self.add_child(Tile(self, pygame.transform.scale(self.manager.get_image("tiles/wood"), (TILE_SIZE, TILE_SIZE)), (i * TILE_SIZE, n * TILE_SIZE)))
            self.add_child(Tile(self, pygame.transform.scale(self.manager.get_image("tiles/wood"), (TILE_SIZE, TILE_SIZE)), (i * TILE_SIZE, 0)))
            self.add_child(Tile(self, pygame.transform.scale(self.manager.get_image("tiles/wood"), (TILE_SIZE, TILE_SIZE)), (n * TILE_SIZE, i * TILE_SIZE)))
            self.add_child(Tile(self, pygame.transform.scale(self.manager.get_image("tiles/wood"), (TILE_SIZE, TILE_SIZE)), (0, i * TILE_SIZE)))
        self.add_child(Enemy(self, (TILE_SIZE, TILE_SIZE * 4)))

    def on_key_down(self, key):
        if key == pygame.K_r:
            # restart level
            self.TEMP_reset()
        elif key == pygame.K_ESCAPE:
            self.parent.set_screen("menu")
        elif key == pygame.K_F3:
            self.toggle_debug()

    def on_resize(self, new_size):
        # remake game surface to new size
        self.game_surface = pygame.Surface(new_size)
        # recalibrate camera
        self.camera.set_screen_size(new_size)
        self.master_ui.style.size = new_size
        self.debug_ui.style.size = new_size
        self.hud_ui.style.size = new_size
        for item in self.master_ui.get_all_children():
            item.redraw_image()

    def TEMP_reset(self):
        self.__init__(self.parent, self.debug_enabled)

    def debug(self):
        # render hitboxes of anything that has a rect
        for entity in self.get_all_children():
            if not hasattr(entity, "rect"): continue
            # ignore self
            if entity == self: continue

            scaled_pos_start = self.camera.convert_coords(pygame.Vector2(entity.rect.topleft))
            scaled_pos_end = scaled_pos_start + pygame.Vector2(entity.rect.size)
            pygame.draw.line(self.game_surface, (0, 0, 255), scaled_pos_start, (scaled_pos_start.x, scaled_pos_end.y))
            pygame.draw.line(self.game_surface, (0, 0, 255), scaled_pos_start, (scaled_pos_end.x, scaled_pos_start.y))
            pygame.draw.line(self.game_surface, (0, 0, 255), scaled_pos_end, (scaled_pos_start.x, scaled_pos_end.y))
            pygame.draw.line(self.game_surface, (0, 0, 255), scaled_pos_end, (scaled_pos_end.x, scaled_pos_start.y))

    def update(self):
        # update all sprites in update group
        self.manager.groups["update"].update()
        self.master_ui.update()

    def render(self, surface: pygame.Surface):
        # clear game surface
        self.game_surface.fill((30, 31, 33))

        # render objects with layered camera
        self.camera.render(
            surface = self.game_surface,
            sprite_group = self.manager.groups["render"]
        )

        # render GUI elements
        self.master_ui.render(self.game_surface)

        if self.debug_enabled:
            self.debug()

        # render to window
        surface.blit(self.game_surface, (0, 0))

class FollowCameraLayered(Sprite):
    def __init__(self, level, target_sprite, follow_speed = 2, tolerence = 5):
        super().__init__(parent = level, groups=["update"])
        self.id = "camera"
        self.window = pygame.display.get_surface()

        self.target = target_sprite
        self.pos = pygame.Vector2(target_sprite.rect.center)
        self.follow_divider = 1 / follow_speed
        self.tolerence = tolerence

        self.set_screen_size(self.window.get_size())

        self.offset = pygame.Vector2()

    def update(self):
        # move camera closer to target
        self.pos += self.manager.dt * (self.target.rect.center - self.pos) / self.follow_divider

    def set_screen_size(self, new_size):
        """Set new screen size to center camera on"""
        self.half_screen_size = pygame.Vector2(new_size[0] // 2, new_size[1] // 2)

    def convert_coords(self, old_coords: pygame.Vector2) -> pygame.Vector2:
        """Converts absolute world coords to scaled coords on screen"""
        return pygame.Vector2(
            old_coords.x - (self.pos.x - self.half_screen_size.x),
            old_coords.y - (self.pos.y - self.half_screen_size.y)
        )

    def render(self, surface: pygame.Surface, sprite_group: pygame.sprite.Group):
        # render sprites centered on camera position
        self.offset.x = self.pos.x - self.half_screen_size.x
        self.offset.y = self.pos.y - self.half_screen_size.y

        # render sprites based on y position
        for sprite in sorted(sprite_group.sprites(), key = lambda s: s.rect.centery):
            new_pos = (sprite.rect.x - self.offset.x + sprite.render_offset[0], sprite.rect.y - self.offset.y + sprite.render_offset[1])
            surface.blit(sprite.image, new_pos)