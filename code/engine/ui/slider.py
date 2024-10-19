import pygame
from typing import Callable

from .element import Element
from .style import Style
class Slider(Element):
    def __init__(self, parent: Element, style: Style, knob_style: Style, on_change: Callable[[float], None] = lambda _: None, on_unfocus: Callable[[float], None] = lambda _: None):
        self.on_change = on_change
        self.on_unfocus = on_unfocus
        self._value = 0

        self.selected = False

        super().__init__(parent, style)

        self.knob = self.add_child(Element(self, Style(
            size = knob_style.size,
            image = knob_style.image,
            colour = knob_style.colour,
            alignment = "center-left"
        )))

        self._position_knob()
        
    def _position_knob(self) -> None:
        # self.knob.rect.centerx = self.rect.left + self._value * self.rect.width
        self.knob.style.offset = (self._value * self.rect.width, self.knob.style.offset[1])
        self.knob.redraw_image()

    def on_mouse_down(self, mouse_button: int) -> None:
        super().on_mouse_down(mouse_button)
        if mouse_button == 1:
            mouse_pos = self.manager.get_mouse_pos()
            if self.rect.collidepoint(mouse_pos):
                self.selected = True

    def on_mouse_up(self, mouse_button: int) -> None:
        super().on_mouse_up(mouse_button)
        if mouse_button == 1 and self.selected:
            self.selected = False
            self.on_unfocus(self.get_value())

    def set_value(self, value: float) -> None:
        """Set the value of slider, moving the knob"""
        self._value = value
        self._position_knob()

    def get_value(self) -> float:
        """Get the value of slider as a float from 0-1 inclusive"""
        return (self.knob.rect.centerx - self.rect.x) / self.rect.width
    
    def redraw_image(self) -> None:
        super().redraw_image()

    def on_resize(self, new_res: tuple[float, float]) -> None:
        super().on_resize(new_res)
        self._position_knob()

    def render(self, surface: pygame.Surface) -> float:
        super().render(surface)

    def update(self) -> None:
        super().update()

        mouse_pos = self.manager.get_mouse_pos()

        if self.knob.rect.collidepoint(mouse_pos):
            self.manager.set_cursor(pygame.SYSTEM_CURSOR_HAND)

        if self.selected:
            self.knob.rect.centerx = mouse_pos[0]
            if self.knob.rect.centerx < self.rect.x:
                self.knob.rect.centerx = self.rect.x
            if self.knob.rect.centerx > self.rect.right:
                self.knob.rect.centerx = self.rect.right
            self._value = self.get_value()
            self.on_change(self.get_value())