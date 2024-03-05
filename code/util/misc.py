import pygame
from engine.types import *

def scale_surface_by(surface: pygame.Surface, scale_factor: float):
    new_size = surface.get_width() * scale_factor, surface.get_height() * scale_factor
    return pygame.transform.scale(surface, new_size)

def get_closest_direction(vector: pygame.Vector2) -> Direction:
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
