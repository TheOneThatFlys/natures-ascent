import pygame

from typing import Optional, Callable

from .element import Element
from .style import Style
from ..types import *

def render_rich_text(font: pygame.font.Font, text: str) -> pygame.Surface:
    """
    Renders a section of rich text.

    Formatting:
    - %(colour) to set colour - defaults to (0, 0, 0).

    e.g. `"%(255, 0, 0)this is red. %(255, 255, 255)this is white."`
    """

    text_sections = []

    current_colour = (0, 0, 0)
    current_section = ""
    index = 0
    # loop through input string
    while index < len(text):
        letter = text[index]
        # add character to current section if not escaping
        if letter != "%":
            current_section += letter
            index += 1
        # if valid escape is used followed by an opening bracket
        elif text[index + 1] == "(":
            # if the previous text section is not empty,
            # render the previous section of text and
            # start a new section
            if current_section != "":
                text_sections.append(font.render(current_section, True, current_colour))
                current_section = ""

            # grab the entire colour escape clause
            # e.g. (255, 0, 0)
            inside_loop_idx = index
            inside_acc = ""
            while inside_loop_idx < len(text):
                inside_loop_idx += 1
                inside_acc += text[inside_loop_idx]
                if text[inside_loop_idx] == ")":
                    break
            else:
                raise ValueError(f"Rich text render of '{text}' failed: missing closing bracket.")

            # create a colour tuple from the string
            current_colour = tuple(map(int, inside_acc.removeprefix("(").removesuffix(")").replace(" ", "").split(",")))
            
            # offset the main loop pointer by the length of the escape clause
            index = inside_loop_idx + 1
        # %% escape
        elif text[index + 1] == "%":
            current_section += "%"
            index += 2
        # invalid escape clause
        else:
            raise ValueError(f"Rich text render of '{text}' failed: % with no opening bracket.")

    # add the last section if it was not already escaped
    if current_section != "":
        text_sections.append(font.render(current_section, True, current_colour))
        current_section = ""

    # create a surface of the max bounds of the text added together
    surf = pygame.Surface((
        sum(s.get_width() for s in text_sections),
        max(s.get_height() for s in text_sections)
    ), pygame.SRCALPHA)

    # render each section of text side by side
    x_offset = 0
    for section in text_sections:
        surf.blit(section, (x_offset, 0))
        x_offset += section.get_width()

    return surf

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

# class RichText(Element):
#     """
#     UI element that displays rich text (only supports colour).
#     """
#     def redraw_image(self) -> None:
#         self.image = render_rich_text(self.style.font, self.text)
#         self.rect = self.image.get_rect()
#         self.calculate_position()

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
                 character_set: Optional[str] = None) -> None:
        
        self.text = initial_text
        self.text_padding = text_padding
        # length in pixels of text
        self.text_length_pixels = 0

        super().__init__(parent, style)

        self.norm_style = style
        self.focused_style = Style.merge(style, focused_style)

        self.show_blinker = show_blinker
        self._blink_timer = 0
        self._blink_interval = 30
        self._blink_activated = False

        self.focused = False

        self.enabled = enabled

        self.on_unfocus = on_unfocus[0]
        self.on_unfocus_args = on_unfocus[1]

        # max allowed num of characters
        self.max_length = max_length
        # allowed characters
        self.character_set = character_set

    def on_mouse_down(self, mouse_button: int) -> None:
        super().on_mouse_down(mouse_button)
        if not self.enabled: return
        mouse_pos = self.manager.get_mouse_pos(self.style.window)
        if self.rect.collidepoint(mouse_pos):
            if not self.focused:
                self.set_style(self.focused_style)

                self.focused = True
                self._blink_activated = True
                self._blink_timer = 0

            # right click deletes text box
            if mouse_button == 3:
                self.text = ""
                self.redraw_image()
        else:
            if self.focused:
                self.set_style(self.norm_style)
                self.focused = False
                self._blink_activated = False

                if self.on_unfocus:
                    self.on_unfocus(*self.on_unfocus_args)

    def on_key_down(self, key: int, unicode: str) -> None:
        super().on_key_down(key, unicode)
        if not self.enabled: return
        pressed_keys = pygame.key.get_pressed()
        if self.focused:
            if key == pygame.K_BACKSPACE:
                if pressed_keys[pygame.K_LCTRL]:
                    self.text = ""
                else:
                    self.text = self.text[:-1]
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
            self._blink_timer += self.manager.dt
            if self._blink_timer >= self._blink_interval:
                self._blink_timer = 0
                self._blink_activated = not self._blink_activated

    def set_text(self, text: str) -> None:
        self.text = text
        self.redraw_image()

    def render(self, window: pygame.Surface) -> None:
        super().render(window)

        if self._blink_activated:
            blink_rect = pygame.Rect(self.rect.x + self.text_length_pixels + self.text_padding[0], self.rect.y + 2, 2, self.rect.height - 4)
            if self.rect.contains(blink_rect):
                pygame.draw.rect(window, self.style.fore_colour, blink_rect)