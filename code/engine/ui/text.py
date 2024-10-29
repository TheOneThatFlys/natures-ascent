import pygame
from typing import Optional, Callable

try:
    import pyperclip
    clipboard = pyperclip
except ImportError:
    clipboard = None

from .element import Element
from .style import Style
from ..types import *

class Text(Element):
    """
    UI element that displays text.
    """
    def __init__(self, parent: Element, style: Style, text: str = "") -> None:
        self.text = text
        super().__init__(parent, style)

    def set_text(self, text: str) -> None:
        self.text = text
        self.redraw_image()

    def redraw_image(self) -> None:
        self.image = self.style.font.render(self.text, self.style.antialiasing, self.style.fore_colour)

        if self.style.text_shadow:
            base_img = pygame.Surface((self.image.get_width() + self.style.text_shadow, self.image.get_height() + self.style.text_shadow), pygame.SRCALPHA)
            shadow_image = self.style.font.render(self.text, self.style.antialiasing, self.style.colour)

            base_img.blit(shadow_image, (0, self.style.text_shadow))
            base_img.blit(self.image, (0, 0))
            self.image = base_img

        self.rect = self.image.get_rect()
        self.calculate_position()

class TextBox(Element):
    """
    UI element that enables use to type into a text field.
    """
    def __init__(self,
            parent: Element,
            style: Style,
            focused_style: Optional[Style] = None,
            initial_text: str = "",
            text_padding: Vec2 = (0, 2),
            show_blinker: bool = True,
            enabled: bool = True,
            on_unfocus: tuple[Callable[..., None], list] = (None, []),
            max_length: int = 999,
            character_set: Optional[str] = None
        ) -> None:
        
        self.text = initial_text
        self.text_padding = text_padding
        # length in pixels of text
        self.text_length_pixels = 0

        super().__init__(parent, style)

        self.norm_style = style
        self.focused_style = Style.merge(style, focused_style)

        self.show_blinker = show_blinker
        self._blinker = self.add_child(Element(
            parent = self,
            style = Style(
                visible = False,
                size = (2, self.rect.height - 4),
                alignment = "center-left",
                offset = (self.text_padding[0], 0),
                colour = self.style.fore_colour,
            )
        ))
        self._blink_timer = 0
        self._blink_interval = 30

        self.focused = False

        self.enabled = enabled

        self.on_unfocus = on_unfocus[0]
        self.on_unfocus_args = on_unfocus[1]

        # max allowed num of characters
        self.max_length = max_length
        # allowed characters
        self.character_set = character_set

    def unfocus(self):
        self.set_style(self.norm_style)
        self.focused = False
        self._blinker.style.visible = False

        if self.on_unfocus:
            self.on_unfocus(*self.on_unfocus_args)

    def focus(self):
        if not self.focused:
            self.set_style(self.focused_style)

            self.focused = True
            self._blinker.style.visible = True
            self._blink_timer = 0

    def on_mouse_down(self, mouse_button: int) -> None:
        super().on_mouse_down(mouse_button)
        if not self.enabled: return
        mouse_pos = self.manager.get_mouse_pos(self.style.window)
        if self.rect.collidepoint(mouse_pos):
            self.focus()
            # right click deletes text box
            if mouse_button == 3:
                self.text = ""
                self.redraw_image()
        else:
            if self.focused:
                self.unfocus()

    def on_key_down(self, key: int, unicode: str) -> None:
        super().on_key_down(key, unicode)
        if not self.enabled: return
        pressed_keys = pygame.key.get_pressed()
        if self.focused:
            # deletion
            if key == pygame.K_BACKSPACE:
                # delete whole word when pressing ctrl
                if pressed_keys[pygame.K_LCTRL]:
                    self.text = " ".join(self.text.split(" ")[:-1])
                else:
                    self.text = self.text[:-1]
            # copy and paste (if available)
            elif pressed_keys[pygame.K_LCTRL] and clipboard != None:
                if key == pygame.K_c:
                    clipboard.copy(self.text)
                elif key == pygame.K_v:
                    self.text += clipboard.paste()
            # enter
            elif key == pygame.K_RETURN:
                self.unfocus()
            elif len(self.text) < self.max_length:
                if (self.character_set and unicode in self.character_set) or self.character_set == None:
                    self.text += unicode
            self.redraw_image()

    def redraw_image(self) -> None:
        if self.style.image:
            self.image = self.style.image.copy()
        else:
            self.image = pygame.Surface(self.style.size)
            self.image.fill(self.style.colour)

        font_s = self.style.font.render(self.text, self.style.antialiasing, self.style.fore_colour)
        font_r = font_s.get_rect(left = self.text_padding[0], bottom = self.image.get_height() - self.text_padding[1])

        self.text_length_pixels = font_r.width

        self.image.blit(font_s, font_r)

        self.rect = self.image.get_rect()
        self.calculate_position()

    def update(self) -> None:
        super().update()
        if not self.enabled: return

        mouse_pos = self.manager.get_mouse_pos(self.style.window)
        if self.rect.collidepoint(mouse_pos):
            self.manager.set_cursor(pygame.SYSTEM_CURSOR_IBEAM)

        if self.focused:
            # cycle blinker
            self._blink_timer += self.manager.dt
            
            # move blinker
            new_offset = self.text_padding[0] + self.text_length_pixels
            if self._blinker.style.offset[0] != new_offset:
                self._blinker.style.offset = (new_offset, 0)
                self._blinker.calculate_position()

            if self._blink_timer >= self._blink_interval:
                self._blink_timer = 0
                self._blinker.style.visible = not self._blinker.style.visible

            # check if blinker is offbounds
            if not self.rect.contains(self._blinker.rect):
                self._blinker.style.visible = False
            
    def set_text(self, text: str) -> None:
        self.text = text
        self.redraw_image()