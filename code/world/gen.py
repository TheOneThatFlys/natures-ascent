from __future__ import annotations

import pygame
import random
from typing import Literal, Type

from engine.types import *
from engine import Node, Sprite
from entity import Player, Enemy, Slime
from util.constants import *

from .tile import Tile, TileSet

room_directions: list[Direction] = ["left", "right", "up", "down"]
opposite_directions: dict[Direction, Direction] = {"left": "right", "right": "left", "up": "down", "down": "up"}
direction_vector: dict[Direction, Vec2] = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}

class DarkOverlay(Sprite):
    def __init__(self, parent: Room, death_time: int = 10) -> None:
        super().__init__(parent, groups = ["render", "update"])
        self.parent: Room
        self.z_index = 1
        self.image = pygame.Surface(parent.bounding_rect.size, pygame.SRCALPHA)
        self.starting_alpha = 200
        self.fade_steps = TILE_SIZE
        self.rect = parent.bounding_rect.copy()

        self.dying = False
        self.death_timer = 0
        self.max_time = death_time

        self.draw_image()

    def draw_image(self) -> None:
        new_alpha = (1 - (self.death_timer / self.max_time)) * self.starting_alpha
        self.image.fill((0, 0, 0, max(new_alpha, 0)))

        # draw door fades
        for direction in self.parent.connections:
            room_offset = direction_vector[direction]
            neighbour_room = self.parent.parent.rooms[(self.parent.origin[0] + room_offset[0], self.parent.origin[1] + room_offset[1])]
            if not neighbour_room.activated: continue

            doors = self.parent.get_door_position(direction)
            for door in doors:
                fade_size = (
                    TILE_SIZE if direction_vector[direction][0] == 0 else TILE_SIZE / self.fade_steps,
                    TILE_SIZE if direction_vector[direction][1] == 0 else TILE_SIZE / self.fade_steps,
                )
                for i in range(self.fade_steps):
                    step_alpha = (1 - i / self.fade_steps) * (new_alpha)
                    offset = pygame.Vector2(direction_vector[direction]) * TILE_SIZE * (i / self.fade_steps)

                    x = door[0] * (TILE_SIZE) + offset[0]
                    y = door[1] * (TILE_SIZE) + offset[1]

                    # error correction for left and up faces
                    if direction == "left":
                        x = (door[0] + 1) * TILE_SIZE + offset[0] - TILE_SIZE / self.fade_steps
                        y = door[1] * TILE_SIZE + offset[1]
                    elif direction == "up":
                        y = (door[1] + 1) * TILE_SIZE + offset[1] - TILE_SIZE / self.fade_steps

                    self.image.fill((0, 0, 0, max(step_alpha, 0)), [x, y, *fade_size])

        # remove tile spaces
        for x, y in self.parent.wall_tiles.keys():
            self.image.fill((0, 0, 0, 0), [x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE])

    def queue_death(self) -> None:
        self.dying = True

    def update(self) -> None:
        if self.dying:
            self.death_timer += self.manager.dt
            self.draw_image()
            if self.death_timer >= self.max_time:
                self.kill()

                # update neighbour rooms to new overlay fades
                for neighbour in self.parent.get_neighbours():
                    if neighbour.dark_overlay:
                        neighbour.dark_overlay.draw_image()

class Room(Node):
    def __init__(self, parent: FloorManager, origin: Vec2, room_size: int, forced_doors: list[Direction] = [], blacklisted_doors: list[Direction] = [], tags: list[str] = [], enemies: dict[Type[Enemy], int] = {}) -> None:
        super().__init__(parent)

        self.bounding_rect = pygame.Rect(origin[0] * TILE_SIZE * room_size, origin[1] * TILE_SIZE * room_size, TILE_SIZE * room_size, TILE_SIZE * room_size)
        self.type = type
        self.room_size = room_size
        self.origin = origin # stored as room coords
        self.tags = tags

        self.connections: list[Direction] = []
        self.door_positions: list[tuple[int, int]] = []

        # store reference to each wall tile
        self.wall_tiles: dict[Vec2, Tile] = {}

        # store each alive enemy
        self.enemies = pygame.sprite.Group()

        # store possible enemies which will be spawned upon room activation
        self._possible_enemies = enemies

        self._activated = False
        self._completed = False

        self.gen_connections_random(forced_doors, blacklisted_doors)

    @property
    def activated(self) -> bool:
        return self._activated
    
    @property
    def completed(self) -> bool:
        return self._completed

    def add_enemies(self) -> None:
        for enemy_type, count in self._possible_enemies.items(): 
            for _ in range(count):
                pos = (
                    random.randint(self.bounding_rect.x + TILE_SIZE, self.bounding_rect.right - 2 * TILE_SIZE),
                    random.randint(self.bounding_rect.y + TILE_SIZE, self.bounding_rect.bottom - 2 * TILE_SIZE)
                )
                
                self.enemies.add(self.add_child(enemy_type(self, pos)))

    def place_in_world(self) -> None:
        "Adds the room's tiles and enemies into the world"
        self.add_tiles()
        self.add_enemies()

        self.dark_overlay = self.add_child(DarkOverlay(self))

    def gen_connections_random(self, forced_doors: list[Vec2], blacklisted_doors: list[Vec2]) -> None:
        for dir in forced_doors:
            self.connections.append(dir)

        dv = pygame.Vector2(self.origin) - pygame.Vector2(self.parent.spawn_room.origin) + pygame.Vector2(0.5, 0.5)
        distance_from_origin = dv.magnitude()

        # scale max connections based on distance from the origin
        n_rooms = max(int(4 - distance_from_origin / 4), 0)

        # limit rooom generation based on target room num
        # in order to have semi consistent room numbers
        if len(self.parent.rooms) < self.parent.target_num:
            n_rooms = max(n_rooms, 1)
        if len(self.parent.rooms) >= self.parent.target_num:
            n_rooms = 0

        for _ in range(n_rooms):
            con = random.choice(room_directions)
            if con in self.connections or con in blacklisted_doors: continue
            self.connections.append(con)  

    def add_tiles(self) -> None:
        self.add_doors()
        temp = pygame.Surface((TILE_SIZE, TILE_SIZE))
        # add walls
        for n in range(self.room_size):
            self.add_tile(temp, (n, 0), True)
            self.add_tile(temp, (n, self.room_size - 1), True)
            self.add_tile(temp, (0, n), True)
            self.add_tile(temp, (self.room_size - 1, n), True)

        # add floors
        for x in range(self.room_size):
            for y in range(self.room_size):
                if (x, y) in self.wall_tiles: continue
                self.add_tile(self.parent.grass_tileset.get(random.randint(0, 3)), (x, y), False)

    def get_door_position(self, direction: Direction) -> tuple[Vec2, Vec2]:
        """Get the relative room coordinates of the doors in the specified direction"""
        second_offset = ()
        x = y = 0
        if direction == "up":
            x = self.room_size // 2
            second_offset = (-1, 0)
        elif direction == "down":
            x = self.room_size // 2
            y = self.room_size - 1
            second_offset = (-1, 0)
        elif direction == "left":
            y = self.room_size // 2
            second_offset = (0, -1)
        elif direction == "right":
            x = self.room_size - 1
            y = self.room_size // 2
            second_offset = (0, -1)

        return (x, y), (x + second_offset[0], y + second_offset[1])

    def add_doors(self) -> None:
        "Generate the relative positions of 'doors'"
        for connection in self.connections:
            door1, door2 = self.get_door_position(connection)

            self.door_positions.append(door1)
            self.door_positions.append(door2)

    def get_neighbours(self) -> list[Room]:
        rooms = []
        for connection in self.connections:
            dv = direction_vector[connection]
            neighbour_pos = self.origin[0] + dv[0], self.origin[1] + dv[1]
            if neighbour_pos in self.parent.rooms:
                rooms.append(self.parent.rooms[neighbour_pos])
        return rooms

    def add_tile(self, image: pygame.Surface, relative_position: Vec2, collider: bool) -> None:
        # convert relative grid coords to world coords
        position = pygame.Vector2(self.origin) * TILE_SIZE * self.room_size + pygame.Vector2(relative_position) * TILE_SIZE
        # check if position is in a door
        if relative_position in self.door_positions and collider == True: return
        # add tile
        tile = Tile(self, image, position, collider)
        if collider: self.wall_tiles[relative_position] = tile
        self.add_child(tile)

    def activate(self) -> None:
        self._activated = True
        self.dark_overlay.queue_death()

    def update(self) -> None:
        if not self._activated:
            player: Player = self.manager.get_object_from_id("player")
            if player.rect.colliderect(self.bounding_rect):
                self.activate()

        if not self._completed and self._activated:
            if len(self.enemies) == 0:
                self._completed = True
            self.enemies.update()

class SpawnRoom(Room):
    def __init__(self, parent: FloorManager, origin: Vec2, room_size: Vec2) -> None:
        super().__init__(parent, origin, room_size, [], [], ["spawn"])

        portal_sprite = self.add_child(Sprite(self, groups = ["render"]))
        portal_sprite.image = pygame.transform.scale(self.manager.get_image("tiles/spawn_portal"), (TILE_SIZE * 6, TILE_SIZE * 6))
        portal_sprite.rect = portal_sprite.image.get_rect(center = self.bounding_rect.center)
        # render above floor and below player
        portal_sprite.z_index = -0.5

    def gen_connections_random(self, __, ___) -> None:
        for _ in range(4):
            con = random.choice(room_directions)
            if con in self.connections: continue
            self.connections.append(con)

    def place_in_world(self) -> None:
        super().place_in_world()
        # remove dark overlay in spawn room
        self.dark_overlay.kill()
        self._activated = True

class FloorManager(Node):
    def __init__(self, parent: Node, room_size: int = 8, target_num: int = 8) -> None:
        super().__init__(parent)
        if room_size % 2 == 1:
            raise ValueError("Room size must be even.")
        self.id = "floor-manager"
        self.room_size = room_size
        self.target_num = target_num

        self.wall_tileset = TileSet(pygame.transform.scale_by(self.manager.get_image("tiles/wall_tiles"), 2), TILE_SIZE)
        self.grass_tileset = TileSet(pygame.transform.scale_by(self.manager.get_image("tiles/grass_tiles"), 2), TILE_SIZE)

        self.rooms: dict[Vec2, Room] = {}

    def generate(self) -> None:
        "Generate a floor"
        connection_stack = []

        spawn_room_origin = (0, 0)

        self.spawn_room = self.add_child(SpawnRoom(self, spawn_room_origin, self.room_size))
        self.rooms[spawn_room_origin] = self.spawn_room
        for con in self.spawn_room.connections:
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

        self.player = self.add_child(Player(self, self.spawn_room.bounding_rect.center - pygame.Vector2(TILE_SIZE / 2, TILE_SIZE)))

        for _, room in self.rooms.items():
            room.place_in_world()

        self.calculate_textures()

    def _get_type_of_tile(self, wall_tiles: dict[Vec2, Tile], all_tiles: dict[Vec2, Tile] , coord: Vec2) -> Literal["wall", "floor", "world"]:
        return "wall" if coord in wall_tiles else "floor" if coord in all_tiles else "world"

    def calculate_textures(self) -> None:
        # not proud of this code, but it works(?)
        all_tiles = {}
        wall_tiles = {}

        for item in self.get_all_children():
            if isinstance(item, Tile):
                scaled_coords = (item.rect.x // TILE_SIZE, item.rect.y // TILE_SIZE)
                all_tiles[scaled_coords] = item
                if item.is_wall:
                    wall_tiles[scaled_coords] = item

        for coord, tile in wall_tiles.items():
            left_pos = coord[0] - 1, coord[1]
            right_pos = coord[0] + 1, coord[1]
            up_pos = coord[0], coord[1] - 1
            down_pos = coord[0], coord[1] + 1

            top_left_pos = coord[0] - 1, coord[1] - 1
            top_right_pos = coord[0] + 1, coord[1] - 1
            bottom_left_pos = coord[0] - 1, coord[1] + 1
            bottom_right_pos = coord[0] + 1, coord[1] + 1

            left_tile = self._get_type_of_tile(wall_tiles, all_tiles, left_pos)
            right_tile = self._get_type_of_tile(wall_tiles, all_tiles, right_pos)
            up_tile = self._get_type_of_tile(wall_tiles, all_tiles, up_pos)
            down_tile = self._get_type_of_tile(wall_tiles, all_tiles, down_pos)
            top_left_tile = self._get_type_of_tile(wall_tiles, all_tiles, top_left_pos)
            top_right_tile = self._get_type_of_tile(wall_tiles, all_tiles, top_right_pos)
            bottom_left_tile = self._get_type_of_tile(wall_tiles, all_tiles, bottom_left_pos)
            bottom_right_tile = self._get_type_of_tile(wall_tiles, all_tiles, bottom_right_pos)

            tile_index = 14
            # weird inner bits
            if top_left_tile == "floor":
                tile_index = 12
            elif top_right_tile == "floor":
                tile_index = 10
            elif bottom_left_tile == "floor":
                tile_index = 2
            elif bottom_right_tile == "floor":
                tile_index = 0

            # straight walls
            if left_tile == "wall" and right_tile == "wall":
                if down_tile == "floor":
                    tile_index = 1
                elif up_tile == "floor":
                    tile_index = 11

            elif up_tile == "wall" and down_tile == "wall":
                if left_tile == "floor":
                    tile_index = 7
                elif right_tile == "floor":
                    tile_index = 5
            # corners
            elif down_tile == "wall" and right_tile == "wall":
                if up_tile == "floor" and left_tile == "floor":
                    tile_index = 3
                else:
                    tile_index = 0

            elif down_tile == "wall" and left_tile == "wall":
                if up_tile == "floor" and right_tile == "floor":
                    tile_index = 4
                else:
                    tile_index = 2

            elif up_tile == "wall" and right_tile == "wall":
                if down_tile == "floor" and left_tile == "floor":
                    tile_index = 8
                else:
                    tile_index = 10

            elif up_tile == "wall" and left_tile == "wall":
                if down_tile == "floor" and right_tile == "floor":
                    tile_index = 9
                else:
                    tile_index = 12

            tile.image = self.wall_tileset.get(tile_index)

    def _gen_1x1(self, origin: Vec2, tags: list[str] = []) -> Room:
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

        room = Room(
            parent = self,
            origin = origin,
            room_size = self.room_size,
            forced_doors = forced_connections,
            blacklisted_doors = blacklisted_connections,
            enemies = {Slime: 3},
            tags = tags,
        )

        self.rooms[origin] = room
        self.add_child(room)
        return room
    
    def update(self) -> None:
        for _, room in self.rooms.items():
            room.update()
