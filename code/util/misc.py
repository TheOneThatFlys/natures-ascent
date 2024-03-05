import pygame

def scale_surface_by(surface: pygame.Surface, scale_factor: float):
    new_size = surface.get_width() * scale_factor, surface.get_height() * scale_factor
    return pygame.transform.scale(surface, new_size)