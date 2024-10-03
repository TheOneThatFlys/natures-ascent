from __future__ import annotations

import pygame
import random
from typing import Literal, Type

from engine.types import *
from engine import Node, Sprite
from entity import Player, Enemy, Slime, TreeBoss
from item import Health, Coin
import util
from util.constants import *

from .tile import Tile, TileSet, TileCollection
from .interactable import ItemChest, PickupChest, PrayerStatue, SpawnPortal

room_directions: list[Direction] = ["left", "right", "up", "down"]
opposite_directions: dict[Direction, Direction] = {"left": "right", "right": "left", "up": "down", "down": "up"}
direction_vector: dict[Direction, Vec2] = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}

# wall, door1, door2
tile_indexes = {
    "left": (5, 9, 4),
    "right": (7, 8, 3),
    "up": (1, 9, 8),
    "down": (11, 4, 3),
}

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
        self.update_alpha()

    def draw_image(self) -> None:
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, BLACK, (TILE_SIZE, TILE_SIZE, self.parent.room_size * TILE_SIZE, self.parent.room_size * TILE_SIZE))
        floor_manager: FloorManager = self.manager.get_object("floor-manager")

        # draw door fades
        for direction in self.parent.connections:
            room_offset = direction_vector[direction]
            neighbour_room = floor_manager.rooms[(self.parent.origin[0] + room_offset[0], self.parent.origin[1] + room_offset[1])]
            # dont draw fades into non existant rooms
            if not neighbour_room.activated: continue

            doors = self.parent.get_door_position(direction)
            for door in doors:
                fade_size = (
                    TILE_SIZE if direction_vector[direction][0] == 0 else TILE_SIZE / self.fade_steps,
                    TILE_SIZE if direction_vector[direction][1] == 0 else TILE_SIZE / self.fade_steps,
                )
                for i in range(self.fade_steps):
                    step_alpha = (1 - i / self.fade_steps) * 255
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
        for position, tile in self.parent.wall_tiles.items():
            mask = pygame.mask.from_surface(tile.image)
            mask_image = mask.to_surface(setcolor = (255, 0, 0, 0), unsetcolor = (0, 0, 0, 255))
            self.image.blit(mask_image, (position[0] * TILE_SIZE, position[1] * TILE_SIZE))

        self.update_alpha()
        
    def update_alpha(self) -> None:
        lerped = (1 - (self.death_timer / self.max_time)) * self.starting_alpha
        self.image.set_alpha(max(lerped, 0))

    def queue_death(self) -> None:
        self.dying = True

    def update(self) -> None:
        if self.dying:
            self.death_timer += self.manager.dt
            self.update_alpha()
            if self.death_timer >= self.max_time:
                self.kill()

                # update neighbour rooms to new overlay fades
                for neighbour in self.parent.get_neighbours():
                    if neighbour.dark_overlay:
                        neighbour.dark_overlay.draw_image()

class TempDoor(Sprite):
    def __init__(self, parent: Room, direction: Direction):
        super().__init__(parent, ["render", "collide"])

        if direction == "right":
            d = "left"
        elif direction == "down":
            d = "up"
        else:
            d = direction
        self.image = self.manager.get_image("world/door_" + d)
        if direction == "right":
            self.image = pygame.transform.flip(self.image, True, False)

        self.rect = self.image.get_rect()
        self.z_index = 2
        bounding_rect = self.parent.bounding_rect
        
        if direction == "up":
            self.rect.centerx = bounding_rect.centerx
            self.rect.bottom = bounding_rect.top
            self.z_index = 0
        elif direction == "down":
            self.rect.centerx = bounding_rect.centerx
            self.rect.top = bounding_rect.bottom
        elif direction == "left":
            self.rect.right = bounding_rect.left
            self.rect.bottom = bounding_rect.centery + TILE_SIZE
        elif direction == "right":
            self.rect.left = bounding_rect.right
            self.rect.bottom = bounding_rect.centery + TILE_SIZE

class Room(Node):
    def __init__(self, parent: FloorManager, origin: Vec2, room_size: int, forced_doors: list[Direction] = [], blacklisted_doors: list[Direction] = [], tags: list[str] = [], enemies: dict[Type[Enemy], int] = {}) -> None:
        super().__init__(parent)

        self.bounding_rect = pygame.Rect(origin[0] * TILE_SIZE * room_size, origin[1] * TILE_SIZE * room_size, TILE_SIZE * room_size, TILE_SIZE * room_size)
        self.inside_rect = pygame.Rect(self.bounding_rect.x + TILE_SIZE, self.bounding_rect.y + TILE_SIZE, self.bounding_rect.width - 2 * TILE_SIZE, self.bounding_rect.height - 2 * TILE_SIZE)
        self.room_size = room_size
        self.origin = origin # stored as room coords
        self.tags = tags

        self.connections: list[Direction] = []
        self.door_positions: list[tuple[int, int]] = []

        # store reference to each wall tile and floor tile
        self.wall_tiles: dict[Vec2, Tile] = {}
        self.floor_tiles: dict[Vec2, Tile] = {}

        # store each alive enemy
        self.enemies = pygame.sprite.Group()
        # store doors that appear when player arrives
        self.temp_doors = pygame.sprite.Group()
        # store wall tiles
        self.collide_sprites = pygame.sprite.Group() 

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
        generate_pos = lambda: (
            random.randint(self.bounding_rect.x + TILE_SIZE, self.bounding_rect.right - 2 * TILE_SIZE),
            random.randint(self.bounding_rect.y + TILE_SIZE, self.bounding_rect.bottom - 2 * TILE_SIZE)
        )
        for enemy_type, count in self._possible_enemies.items(): 
            for _ in range(count):
                # add an enemy
                e = self.add_child(enemy_type(self, generate_pos()))
                self.enemies.add(e)

                # if enemy is not completly in bounds, i.e colliding with a wall, generate a new position
                while not self.inside_rect.contains(e.rect):
                    e.rect.center = generate_pos()
                    e.spawn_indicator.rect.center = e.rect.center

    def place_in_world(self) -> None:
        """Adds the room's tiles and enemies into the world"""
        self.add_tiles()
        self.optimise_tiles()

        self.dark_overlay = self.add_child(DarkOverlay(self))
        self.player: Player = self.manager.get_object("player")

    def gen_connections_random(self, forced_doors: list[Vec2], blacklisted_doors: list[Vec2]) -> None:
        for dir in forced_doors:
            self.connections.append(dir)

        dv = pygame.Vector2(self.origin) - pygame.Vector2(self.parent.spawn_room.origin) + pygame.Vector2(0.5, 0.5)
        distance_from_origin = dv.magnitude()

        # scale max connections based on distance from the origin
        n_rooms = max(4 - int(distance_from_origin / 4), 0)

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
        last_index = self.room_size - 1
        first_door, second_door = int(self.room_size / 2) - 1, int(self.room_size / 2)
        for direction in room_directions:
            for i in range(1, self.room_size - 1):
                index = tile_indexes[direction][0]
                if direction in self.connections:
                    if i in (first_door, second_door): continue
                    if i == first_door - 1:
                        index = tile_indexes[direction][1]
                    elif i == second_door + 1:
                        index = tile_indexes[direction][2]

                match direction:
                    case "left":
                        position = (0, i)
                    case "right":
                        position = (last_index, i)
                    case "up":
                        position = (i, 0)
                    case "down":
                        position = (i, last_index)
                            
                self.add_tile(self.parent.wall_tileset.get(index), position, True)

            # corners
            self.add_tile(self.parent.wall_tileset.get(0), (0, 0), True)
            self.add_tile(self.parent.wall_tileset.get(2), (last_index, 0), True)
            self.add_tile(self.parent.wall_tileset.get(12), (last_index, last_index), True)
            self.add_tile(self.parent.wall_tileset.get(10), (0, last_index), True)

        # add floors
        for x in range(self.room_size):
            for y in range(self.room_size):
                self.add_tile(self.parent.grass_tileset.get(random.randint(0, 3)), (x, y), False)

    def optimise_tiles(self) -> None:
        """Combine tiles into a single sprite for faster rendering"""
        self.add_child(TileCollection(self, self.floor_tiles.values(), z_index = -1))
        self.add_child(TileCollection(self, self.wall_tiles.values(), z_index = -0.1))

        # kill original tiles
        for tile in self.floor_tiles.values():
            tile.kill()
        for tile in self.wall_tiles.values():
            tile.remove(self.manager.groups["render"])
        #del self.floor_tiles
        #del self.wall_tiles

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

    def get_neighbours(self) -> list[Room]:
        rooms = []
        for connection in self.connections:
            dv = direction_vector[connection]
            neighbour_pos = self.origin[0] + dv[0], self.origin[1] + dv[1]
            if neighbour_pos in self.parent.rooms:
                rooms.append(self.parent.rooms[neighbour_pos])
        return rooms

    def room_to_world_coord(self, room_coord: Vec2) -> Vec2:
        """Convert a room based coord into a world pixel coordinate."""
        return pygame.Vector2(self.origin) * TILE_SIZE * self.room_size + pygame.Vector2(room_coord) * TILE_SIZE

    def add_tile(self, image: pygame.Surface, relative_position: Vec2, collider: bool) -> None:
        # convert relative grid coords to world coords
        position = self.room_to_world_coord(relative_position)
        # add tile
        tile = Tile(self, image, position, collider)
        if collider:
            self.wall_tiles[relative_position] = tile
            self.collide_sprites.add(tile)
        else:
            self.floor_tiles[relative_position] = tile
        self.add_child(tile)

    def activate(self) -> None:
        self._activated = True
        self.dark_overlay.queue_death()
        self.add_enemies()

        for direction in room_directions:
            if direction in self.connections:
                self.temp_doors.add(self.add_child(TempDoor(self, direction)))

        self.manager.play_sound("effect/door_close", 0.5)

    def on_completion(self) -> None:
        level = self.manager.get_object("level")
        # randomly decide if health or chest should spawn
        itempool = self.manager.get_object("itempool")
        if random.random() < ITEM_SPAWN_CHANCE and not itempool.is_empty():
            level.add_child(ItemChest(level, self.bounding_rect.center, itempool.roll()))
        else:
            loot_table = {
                (Health, 1): 1,
                (Coin, 10): 2,
            }
            pickup_type, n = util.choose_weighted(loot_table)
            level.add_child(PickupChest(level, self.bounding_rect.center, pickup_type, n))

    def force_completion(self) -> None:
        self._possible_enemies = {}
        self._activated = True
        self._completed = True
        self.dark_overlay.queue_death()

    def update(self) -> None:
        if not self._activated:
            if self.bounding_rect.contains(self.player.rect):
                self.activate()

        if not self._completed and self._activated:
            if len(self.enemies) == 0:
                self._completed = True
                self.on_completion()
                # remove doors
                for sprite in self.temp_doors:
                    sprite.kill()

class SpawnRoom(Room):
    def __init__(self, parent: FloorManager, origin: Vec2, room_size: Vec2) -> None:
        super().__init__(parent, origin, room_size, [], [], ["spawn"])
        self.spawn_portal = self.add_child(SpawnPortal(self, self.bounding_rect.center))
        # force completion without activating room clear
        self._activated = True
        self._completed = True

    def gen_connections_random(self, __, ___) -> None:
        for _ in range(4):
            con = random.choice(room_directions)
            if con in self.connections: continue
            self.connections.append(con)

    def activate(self) -> None:
        pass

    def place_in_world(self) -> None:
        super().place_in_world()
        # remove dark overlay in spawn room
        self.dark_overlay.kill()
        self._activated = True

class SpecialRoom(Room):
    def __init__(self, room: Room) -> None:
        super().__init__(
            parent = room.parent,
            origin = room.origin,
            room_size = room.room_size,
            forced_doors = room.connections,
            blacklisted_doors = [direction for direction in room_directions if direction not in room.connections],
            tags = [],
            enemies = {}
        )
        self.parent.remove_child(room)

class BossRoom(SpecialRoom):
    def __init__(self, room: Room, boss: Type[Enemy]) -> None:
        super().__init__(room)
        self._possible_enemies = {boss: 1}
        self.tags.append("boss")

    def add_enemies(self) -> None:
        for enemy_type, v in self._possible_enemies.items():
            for _ in range(v):
                e = self.add_child(enemy_type(self, self.bounding_rect.center))
                self.enemies.add(e)

class UpgradeRoom(SpecialRoom):
    def __init__(self, room: Room) -> None:
        super().__init__(room)
        self.tags.append("upgrade")
        self.statue = self.add_child(PrayerStatue(self, (self.bounding_rect.centerx, self.bounding_rect.centery - TILE_SIZE * 1)))
        # add collider for statue base
        s = self.add_child(Sprite(self, groups = ["collide"]))
        s.rect = pygame.Rect(0, 0, TILE_SIZE * 2, TILE_SIZE * 2 + 4)
        s.rect.bottom = self.statue.rect.bottom
        s.rect.centerx = self.statue.rect.centerx
        
    def activate(self) -> None:
        self._activated = True
        self.dark_overlay.queue_death()

    def on_completion(self) -> None:
        pass # remove chest spawn

class FloorManager(Node):
    def __init__(self, parent: Node, room_size: int = 8, target_num: int = 8) -> None:
        super().__init__(parent)
        if room_size % 2 == 1:
            raise ValueError("Room size must be even.")
        self.id = "floor-manager"
        self.room_size = room_size
        self.target_num = target_num

        self.wall_tileset = TileSet(self.manager.get_image("world/wall_tiles"), TILE_SIZE)
        self.grass_tileset = TileSet(self.manager.get_image("world/grass_tiles"), TILE_SIZE)

        self.rooms: dict[Vec2, Room] = {}

    def generate(self, seed: float | None = None) -> None:
        """Generate a floor from given seed. If the seed None, a random seed is generated"""
        self.seed = seed if seed else random.random()
        random.seed(self.seed)
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

            new_room = self._create_room(new_room_pos)

            # push new room connections to stack
            for con in new_room.connections:
                connection_stack.append((new_room.origin, con))

        # create boss room
        furthest_room = max([room for room in self.rooms.values() if len(room.connections) == 1], key = lambda room: pygame.Vector2(room.origin).magnitude())
        self.rooms[furthest_room.origin] = self.add_child(BossRoom(furthest_room, boss = TreeBoss))

        # create upgrade room
        # find a random room that is not special
        room = random.choice([room for room in self.rooms.values() if not isinstance(room, (SpecialRoom, SpawnRoom))])
        self.rooms[room.origin] = self.add_child(UpgradeRoom(room))

        self.player = self.add_child(Player(self, self.spawn_room.bounding_rect.center - pygame.Vector2(TILE_SIZE / 2, TILE_SIZE)))

        for room in self.rooms.values():
            room.place_in_world()
            room.dark_overlay.draw_image()

    def _get_type_of_tile(self, wall_tiles: dict[Vec2, Tile], all_tiles: dict[Vec2, Tile] , coord: Vec2) -> Literal["wall", "floor", "world"]:
        return "wall" if coord in wall_tiles else "floor" if coord in all_tiles else "world"

    def _create_room(self, origin: Vec2, tags: list[str] = []) -> Room:
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
    
    def get_room_at_world_pos(self, world_position: Vec2) -> Room:
        return self.rooms[(world_position[0] // self.room_size // TILE_SIZE, world_position[1] // self.room_size // TILE_SIZE)]

    def get_completion_status(self) -> tuple[int, int]:
        """Returns `(n. rooms completed, total rooms)`"""
        return len(list(filter(lambda coord_room: coord_room[1].activated and coord_room[1].completed, self.rooms.items()))), len(self.rooms)

    def update(self) -> None:
        for _, room in self.rooms.items():
            room.update()
