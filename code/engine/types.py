from typing import Literal
import pygame

Alignment = Literal["top-left", "top-right", "bottom-left", "bottom-right", "center-left", "center-right", "top-center", "bottom-center", "center-center"]
Position = Literal["absolute", "relative"]
Colour = pygame.Color | tuple[int, int, int]
StretchType = Literal["skew", "expand", "none", "fit"]