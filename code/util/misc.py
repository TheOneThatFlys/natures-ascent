import pygame
from engine.types import *

def scale_surface_by(surface: pygame.Surface, scale_factor: float) -> pygame.Surface:
    "Scales a pygame surface by a given factor and returns it (NOT IN PLACE)"
    new_size = surface.get_width() * scale_factor, surface.get_height() * scale_factor
    return pygame.transform.scale(surface, new_size)

def draw_background(screen_size: tuple[int, int], pixel_scale: int = 8, line_thickness: int = 7, offset: int = 0, border_radius: int = 0) -> pygame.Surface:
    "Draw a striped background of given sized and scale onto surface"
    COLOUR_ONE = (37, 44, 55)
    COLOUR_TWO = (26, 30, 36)

    bg = pygame.Surface((screen_size[0] / pixel_scale, screen_size[1] / pixel_scale), pygame.SRCALPHA)
    pygame.draw.rect(bg, COLOUR_TWO, [0, 0, *bg.get_size()])
    pygame.draw.rect(bg, COLOUR_ONE, [line_thickness / 2, line_thickness / 2, bg.get_width() - line_thickness, bg.get_height() - line_thickness])

    n_lines = int((max(screen_size[0], screen_size[1]) + min(screen_size[0], screen_size[1])) / pixel_scale / line_thickness)
    for x in range(n_lines):
        if x % 2 == 0:
            d = x * line_thickness + line_thickness / 2 + offset
            e = line_thickness
            pygame.draw.line(bg, COLOUR_TWO, (d + e, -e), (-e, d + e), line_thickness)

    if border_radius > 0:
        mask = pygame.Surface(bg.get_size())
        pygame.draw.rect(mask, (255, 255, 255), [0, 0, *mask.get_size()], border_radius = border_radius)
        mask.set_colorkey((0, 0, 0))
        mask = pygame.mask.from_surface(mask)
        bg = mask.to_surface(setsurface = bg, unsetcolor = None)

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
