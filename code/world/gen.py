import pygame
import random
from typing import Literal

from engine.types import Direction
from engine import Node, Sprite
from entity import Player
from util.constants import *

from .tile import Tile, TileSet

room_directions: list[Direction] = ["left", "right", "up", "down"]
opposite_directions: dict[Direction, Direction] = {"left": "right", "right": "left", "up": "down", "down": "up"}
direction_vector: dict[Direction, tuple[int, int]] = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}

class Room(Node):
    def __init__(self, parent, origin: tuple[int, int], room_size: int, forced_doors: list[Direction] = [], blacklisted_doors: list[Direction] = [], tags = []):
        super().__init__(parent)

        self.bounding_rect = pygame.Rect(origin[0] * TILE_SIZE * room_size, origin[1] * TILE_SIZE * room_size, TILE_SIZE * room_size, TILE_SIZE * room_size)
        self.type = type
        self.room_size = room_size
        self.origin = origin # stored as room coords
        self.tags = tags

        self.enemies = []
        self.connections: list[Direction] = []
        self.door_positions: list[tuple[int, int]] = []

        self._activated = False

        self.gen_connections_random(forced_doors, blacklisted_doors)
        self.add_tiles()

    @property
    def activated(self) -> bool:
        return self._activated

    def gen_connections_random(self, forced_doors, blacklisted_doors):
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

    def add_tiles(self):
        self.add_doors()
        temp = pygame.Surface((TILE_SIZE, TILE_SIZE))
        # add walls
        for n in range(self.room_size):
            self.add_tile(temp, (n, 0), True)
            self.add_tile(temp, (n, self.room_size - 1), True)
            self.add_tile(temp, (0, n), True)
            self.add_tile(temp, (self.room_size - 1, n), True)

        # add floors
        for x in range(1, self.room_size - 1):
            for y in range(1, self.room_size - 1):
                self.add_tile(self.parent.grass_tileset.get(random.randint(0, 3)), (x, y), False)
        for pos in self.door_positions:
            self.add_tile(self.parent.grass_tileset.get(random.randint(0, 3)), pos, False)

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

    def add_tile(self, image: pygame.Surface, relative_position: tuple[int, int], collider: bool):
        # convert relative grid coords to world coords
        position = pygame.Vector2(self.origin) * TILE_SIZE * self.room_size + pygame.Vector2(relative_position) * TILE_SIZE
        # check if position is in a door
        if relative_position in self.door_positions and collider == True: return
        # add tile
        tile = Tile(self, image, position, collider)
        self.add_child(tile)

    def activate(self):
        self._activated = True

    def update(self):
        if not self._activated:
            player: Player = self.manager.get_object_from_id("player")
            if player.rect.colliderect(self.bounding_rect):
                self.activate()

class SpawnRoom(Room):
    def __init__(self, parent, origin, room_size):
        super().__init__(parent, origin, room_size, [], [], ["spawn"])

        portal_sprite = self.add_child(Sprite(self, groups = ["render"]))
        portal_sprite.image = pygame.transform.scale(self.manager.get_image("tiles/spawn_portal"), (TILE_SIZE * 6, TILE_SIZE * 6))
        portal_sprite.rect = portal_sprite.image.get_rect(center = self.bounding_rect.center)
        portal_sprite.z_index = -0.5

    def gen_connections_random(self, __, ___):
        for _ in range(4):
            con = random.choice(room_directions)
            if con in self.connections: continue
            self.connections.append(con)

class FloorManager(Node):
    def __init__(self, parent, room_size = 8, target_num = 8):
        super().__init__(parent)
        if room_size % 2 == 1:
            raise ValueError("Room size must be even.")
        self.id = "floor-manager"
        self.room_size = room_size
        self.target_num = target_num

        self.wall_tileset = TileSet(pygame.transform.scale_by(self.manager.get_image("tiles/wall_tiles"), 2), TILE_SIZE)
        self.grass_tileset = TileSet(pygame.transform.scale_by(self.manager.get_image("tiles/grass_tiles"), 2), TILE_SIZE)

        self.rooms: dict[tuple[int, int], Room] = {}

    def generate(self):
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

        self.calculate_textures()

        self.player = self.add_child(Player(self, self.spawn_room.bounding_rect.center - pygame.Vector2(TILE_SIZE / 2, TILE_SIZE)))

    def _get_type_of_tile(self, wall_tiles, all_tiles, coord: tuple[int, int]) -> Literal["wall", "floor", "world"]:
        return "wall" if coord in wall_tiles else "floor" if coord in all_tiles else "world"

    def calculate_textures(self):
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

    def _gen_1x1(self, origin, tags = []) -> Room:
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

        room = Room(self, origin, self.room_size, forced_doors = forced_connections, blacklisted_doors = blacklisted_connections, tags = tags)
        self.rooms[origin] = room
        self.add_child(room)
        return room
    
    def update(self):
        for _, room in self.rooms.items():
            room.update()
