import pygame
from engine import Sprite
from util import parse_spritesheet

class Tile(Sprite):
    def __init__(self, parent, image, pos: tuple[int, int], collider: bool):
        super().__init__(parent = parent, groups=["render"])
        if collider:
            self.add(self.manager.groups["collide"])
        else:
            # floor tile
            self.z_index -= 1

        self.image = image
        self.rect = self.image.get_rect(topleft = pos)
        self.is_wall = collider

class TileSet:
    "Generate an indexed tileset (row then column)"
    def __init__(self, tile_set_image: pygame.Surface, tile_size: int):
        self.tiles = []
        rows = parse_spritesheet(tile_set_image, frame_size = (tile_set_image.get_width(), tile_size), direction = "y")
        for row in rows:
            individual_tiles = parse_spritesheet(row, frame_size = (tile_size, tile_size), direction = "x")
            for tile in individual_tiles:
                self.tiles.append(tile)

        self.map = {}

    def set_map(self, m: dict[str, int]):
        "Creates a map that allows you to access tiles from the get() method using a string to index key"
        self.map = m

    def get(self, key: int | str):
        if isinstance(key, str):
            index = self.map[key]
        else:
            index = key

        return self.tiles[index]