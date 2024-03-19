import pygame
from engine.types import *

def scale_surface_by(surface: pygame.Surface, scale_factor: float) -> pygame.Surface:
    "Scales a pygame surface by a given factor and returns it (NOT IN PLACE)"
    new_size = surface.get_width() * scale_factor, surface.get_height() * scale_factor
    return pygame.transform.scale(surface, new_size)

def draw_background(screen_size: tuple[int, int], pixel_scale: int = 8, line_thickness: int = 7) -> pygame.Surface:
    "Draw a striped background of given sized and scale onto surface"
    COLOUR_ONE = (37, 44, 55)
    COLOUR_TWO = (26, 30, 36)

    bg = pygame.Surface((screen_size[0] / pixel_scale, screen_size[1] / pixel_scale))
    bg.fill(COLOUR_ONE)

    n_lines = int((max(screen_size[0], screen_size[1]) + min(screen_size[0], screen_size[1])) / pixel_scale / line_thickness)
    for x in range(n_lines):
        if x % 2 == 0:
            d = x * line_thickness + line_thickness / 2
            e = line_thickness
            pygame.draw.line(bg, COLOUR_TWO, (d + e, -e), (-e, d + e), line_thickness)

    width, height = bg.get_size()
    pygame.draw.line(bg, COLOUR_TWO, (0, 0), (width, 0), line_thickness)
    pygame.draw.line(bg, COLOUR_TWO, (0, 0), (0, height), line_thickness)
    pygame.draw.line(bg, COLOUR_TWO, (width - 1, 0), (width - 1, height), line_thickness)
    pygame.draw.line(bg, COLOUR_TWO, (0, height - 1), (width, height - 1), line_thickness)

    return pygame.transform.scale(bg, screen_size)

def get_closest_direction(vector: pygame.Vector2) -> Direction:
    "Returns the closest cardinal direction of a vector"
    # return right if its a 0 vector
    if vector.magnitude() == 0: return "right"

    # get most influential component:
    # x is more important
    if abs(vector.x) > abs(vector.y):
        if vector.x > 0:
            return "right"
        else:
            return "left"
    
    # y is more important (or equal)
    else:
        if vector.y > 0:
            return "down"
        else:
            return "up"
