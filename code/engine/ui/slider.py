import pygame
from typing import Callable
from .element import Element
from .style import Style
class Slider(Element):
    def __init__(self, parent: Element, style: Style, knob_style: Style, on_change: Callable[[float], None] = lambda _: None):
        self.knob_style = knob_style
        self.on_change = on_change
        self.knob_image = self._resolve_knob_image()
        self.knob_rect = self.knob_image.get_rect()
        self._value = 0

        self.selected = False

        super().__init__(parent, style)

    def _resolve_knob_image(self) -> pygame.Surface:
        if self.knob_style.image:
            self.knob_style.size = self.knob_style.image.get_size()
            return self.knob_style.image
        else:
            s = pygame.Surface(self.knob_style.size)
            s.fill(self.knob_style.colour)
            return s

    def _position_knob(self) -> None:
        self.knob_rect.centery = self.rect.centery + self.knob_style.offset[0]
        self.knob_rect.centerx = self.rect.left + self._value * self.rect.width + self.knob_style.offset[1]

    def on_mouse_down(self, mouse_button: int) -> None:
        super().on_mouse_down(mouse_button)
        if mouse_button == 1:
            mouse_pos = self.manager.get_mouse_pos()
            if self.rect.collidepoint(mouse_pos):
                self.selected = True

    def on_mouse_up(self, mouse_button: int) -> None:
        super().on_mouse_up(mouse_button)
        if mouse_button == 1: self.selected = False

    def set_value(self, value: float) -> None:
        """Set the value of slider, moving the knob"""
        self._value = value
        self._position_knob()

    def get_value(self) -> float:
        """Get the value of slider as a float from 0-1 inclusive"""
        return (self.knob_rect.centerx - self.rect.x) / self.rect.width
    
    def redraw_image(self) -> None:
        super().redraw_image()
        self._position_knob()

    def render(self, surface: pygame.Surface) -> float:
        super().render(surface)

        surface.blit(self.knob_image, self.knob_rect)

    def update(self) -> None:
        super().update()

        mouse_pos = self.manager.get_mouse_pos()

        if self.knob_rect.collidepoint(mouse_pos):
            self.manager.set_cursor(pygame.SYSTEM_CURSOR_HAND)

        if self.selected:
            self.knob_rect.centerx = mouse_pos[0]
            if self.knob_rect.centerx < self.rect.x:
                self.knob_rect.centerx = self.rect.x
            if self.knob_rect.centerx > self.rect.right:
                self.knob_rect.centerx = self.rect.right
            self._value = self.get_value()
            self.on_change(self.get_value())