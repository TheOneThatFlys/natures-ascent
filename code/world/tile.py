import pygame
from engine import Sprite, Node
from engine.types import *
from util import parse_spritesheet

class Tile(Sprite):
    def __init__(self, parent: Node, image: pygame.Surface, pos: Vec2, collider: bool) -> None:
        super().__init__(parent = parent, groups=["render"])
        if collider:
            self.add(self.manager.groups["collide"])
        else:
            # floor tile
            self.z_index -= 1

        self.image = image
        self.rect = self.image.get_rect(topleft = pos)
        self.is_wall = collider

class TileSet(DebugExpandable):
    """Generate an indexed tileset (row then column)"""
    def __init__(self, tile_set_image: pygame.Surface, tile_size: int) -> None:
        self.tiles = []
        rows = parse_spritesheet(tile_set_image, frame_size = (tile_set_image.get_width(), tile_size), direction = "y")
        for row in rows:
            individual_tiles = parse_spritesheet(row, frame_size = (tile_size, tile_size), direction = "x")
            for tile in individual_tiles:
                self.tiles.append(tile)

    def get(self, key: int) -> None:
        return self.tiles[key]