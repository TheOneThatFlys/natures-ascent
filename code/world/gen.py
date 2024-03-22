import pygame
import random
from engine.types import Direction
from engine import Node
from entity import Player
from util.constants import *

from .tile import Tile

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
        self.id = "floor-manager"
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