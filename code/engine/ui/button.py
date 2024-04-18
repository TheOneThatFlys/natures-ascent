import pygame
from typing import Iterable, Callable, Optional

from ..types import *
from .element import Element
from .style import Style

class Button(Element):
    def __init__(
            self,
            parent: Element,
            style: Style,
            hover_style: Optional[Style] = None,
            on_click: Callable[..., None] = None,
            click_args: Iterable = [],
            hover_sound: Optional[str] = "effect/button_hover",
            click_sound: Optional[str] = "effect/button_click",
            enabled: bool = True) -> None:
        
        super().__init__(parent, style)

        self.normal_style = self.style
        self.hover_style = Style.merge(self.style, hover_style)

        # add dummy function that does nothing if no click event set
        self.on_click = on_click if on_click else self.__do_nothing
        self.click_args = click_args

        self.hover_sound = hover_sound
        self.click_sound = click_sound

        self.hovering = False
        self.last_hovering = self.hovering

        self.enabled = enabled

    def __do_nothing(self) -> None:
        pass # do nothing

    def on_mouse_down(self, mouse_button: int, mouse_pos: Vec2) -> None:
        super().on_mouse_down(mouse_button, mouse_pos)
        if self.rect.collidepoint(mouse_pos) and self.enabled:
            if self.click_sound: self.manager.play_sound(self.click_sound, 0.3)
            self.on_click(*self.click_args)

    def update(self) -> None:
        super().update()

        mouse_pos = self.manager.get_mouse_pos()
        self.last_hovering = self.hovering
        self.clicking = False
        self.hovering = False

        if self.rect.collidepoint(mouse_pos):
            self.hovering = True
            if self.enabled:
                self.set_style(self.hover_style)
                self.manager.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            if self.enabled:
                self.set_style(self.normal_style)

        if not self.last_hovering and self.hovering and self.hover_sound and self.enabled: self.manager.play_sound(self.hover_sound, 0.1)
        