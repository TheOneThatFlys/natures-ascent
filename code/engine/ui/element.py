from __future__ import annotations

import pygame
from typing import TypeVar
from ..node import Node
from ..types import *
from .style import Style

T = TypeVar("T", bound = "Element")

class Element(Node):
    """
    Base UI element.
    
    Can be displayed as a coloured rectangle or an image.
    """
    def __init__(self, parent: Element | Node, style: Style) -> None:
        super().__init__(parent)

        self.style = style

        self.redraw_image()

    def calculate_position(self) -> None:
        "Moves element rect based on style"
        if self.style.position == "relative":
            base_rect = self.parent.rect
        elif self.style.position == "absolute":
            base_rect = self.manager.game.display_surface.get_rect()
        else:
            raise TypeError(f"Unknown position type: {self.style.position}")

        y_alignment, x_alignment = self.style.alignment.split("-")

        if x_alignment == "left":
            self.rect.x = base_rect.x + self.style.offset[0]
        elif x_alignment == "right":
            self.rect.right = base_rect.right - self.style.offset[0]
        elif x_alignment == "center":
            self.rect.centerx = base_rect.centerx + self.style.offset[0]
        else:
            raise TypeError(f"Unknown x alignment type: {x_alignment}")

        if y_alignment == "top":
            self.rect.y = base_rect.y + self.style.offset[1]
        elif y_alignment == "bottom":
            self.rect.bottom = base_rect.bottom - self.style.offset[1]
        elif y_alignment == "center":
            self.rect.centery = base_rect.centery + self.style.offset[1]
        else:
            raise TypeError(f"Unknown y alignment type: {y_alignment}")

    def redraw_image(self) -> None:
        self.image = pygame.Surface(self.style.size, pygame.SRCALPHA)
        self.image.set_alpha(self.style.alpha)

        if self.style.image:
            # if no size provided
            if self.style.size == (0, 0):
                self.image = self.style.image

            else:
                if self.style.stretch_type == "none":
                    self.image.blit(self.style.image, (0, 0))
                elif self.style.stretch_type == "expand":
                    # enlarge the image to the biggest it can fit inside element
                    # without distorting it
                    if self.style.image.get_width() == 0:
                        x_factor = 0
                    else:
                        x_factor = self.image.get_width() / self.style.image.get_width()
                    if self.style.image.get_height() == 0:
                        y_factor = 0
                    else:
                        y_factor = self.image.get_height() / self.style.image.get_height()
                    scale_factor = min(x_factor, y_factor)

                    self.image.blit(pygame.transform.scale(self.style.image, (self.style.image.get_width() * scale_factor, self.style.image.get_height() * scale_factor)), (0, 0))
                elif self.style.stretch_type == "skew":
                    # expand the image to fit the bounds
                    self.image = pygame.transform.scale(self.style.image, self.style.size)
                elif self.style.stretch_type == "fit":
                    # image is native resolution
                    self.image = self.style.image
                else:
                    raise TypeError(f"Unknown image stretch type: {self.style.stretch_type}")
        else:
            self.image.fill(self.style.colour)

        self.rect = self.image.get_rect()
        self.calculate_position()

    def on_mouse_down(self, mouse_button: int) -> None:
        for child in self.children:
            child.on_mouse_down(mouse_button)

    def on_mouse_up(self, mouse_button: int) -> None:
        for child in self.children:
            child.on_mouse_up(mouse_button)

    def on_key_down(self, key: int, unicode: str) -> None:
        for child in self.children:
            child.on_key_down(key, unicode)

    def on_scroll(self, dx: int, dy: int) -> None:
        for child in self.children:
            child.on_scroll(dx, dy)

    def on_resize(self, new_res: Vec2) -> None:
        self.redraw_image()
        for child in self.children:
            child.on_resize(new_res)

    def set_style(self, new_style: Style) -> None:
        if self.style != new_style:
            self.style = new_style
            self.redraw_image()

    def render(self, window: pygame.Surface) -> None:
        # draw self then render children
        if not self.style.visible: return
        if self.style.alpha > 0:
            window.blit(self.image, self.rect)

        for child in self.children:
            child.render(window)

    def update(self) -> None:
        for child in self.children:
            child.update()

    def add_child(self, child: T) -> T:
        c = super().add_child(child)
        if c.parent != self:
            raise TypeError(f"Type mismatch: child must be initialised with correct parent ({self} : {c.parent})")
        return c
    
    def get_all_children(self) -> list[Element]:
        return super().get_all_children()