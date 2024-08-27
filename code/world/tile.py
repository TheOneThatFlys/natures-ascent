import pygame, random
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
        self._tiles = []
        rows = parse_spritesheet(tile_set_image, frame_size = (tile_set_image.get_width(), tile_size), direction = "y")
        for row in rows:
            individual_tiles = parse_spritesheet(row, frame_size = (tile_size, tile_size), direction = "x")
            for tile in individual_tiles:
                self._tiles.append(tile)

    def get(self, key: int) -> None:
        return self._tiles[key]

class TileCollection(Sprite):
    """Collect a set of tiles into a single surface which is faster to render."""
    def __init__(self, parent: Node, tiles: list[Tile], z_index: float = 0):
        super().__init__(parent = parent, groups=["render"], z_index = z_index)
        # get min and max bounds
        min_coord = pygame.Vector2(
            min(tiles, key = lambda t: t.rect.x).rect.x,
            min(tiles, key = lambda t: t.rect.y).rect.y
        )
        max_coord = pygame.Vector2(
            max(tiles, key = lambda t: t.rect.right).rect.right,
            max(tiles, key = lambda t: t.rect.bottom).rect.bottom
        )

        self.image = pygame.Surface((max_coord.x - min_coord.x, max_coord.y - min_coord.y), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft = min_coord)

        for tile in tiles:
            self.image.blit(tile.image, (tile.rect.x - min_coord.x, tile.rect.y - min_coord.y))
