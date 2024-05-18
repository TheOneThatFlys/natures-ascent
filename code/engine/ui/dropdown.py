import pygame

from typing import Callable, Optional

from .element import Element
from .text import Text
from .style import Style
from .button import Button

class Dropdown(Element):
    """
    Drop down menu ui element.

    Provide a list of strings of options, the first of which will be the default value.

    ``on_change`` is called with parameter of str provided in options array.
    """
    def __init__(self, parent: Element, style: Style, options: list[str], on_change: Callable[[str], None], button_style: Optional[Style] = None, hover_style: Optional[Style] = None) -> None:
        super().__init__(parent, style)
        self.hover_style = hover_style
        self.button_style = button_style if button_style else style

        self.top_button = self.add_child(Button(self, style = Style.from_style(style, alignment = "center-center", offset = (0, 0)), on_click = self._on_top_click))
        self.selected_text = self.add_child(Text(self, style = Style.from_style(style, alignment = "center-center", offset = (0, 0)), text = options[0]))

        self.opened = False

        self.on_change = on_change

        self.str_options = options
        self.dropdown_buttons: list[Button] = []

        self.selected = options[0]

        for i, option in enumerate(options):
            new_y = i * self.button_style.size[1] + self.top_button.rect.height
            button = Button(self, style = Style.from_style(self.button_style, alignment = "top-center", offset = (0, new_y)), on_click = self.on_option_click, click_args = (option,), hover_style = self.hover_style)
            button.add_child(Text(
                parent = button,
                text = option,
                style = Style.from_style(self.button_style, alignment = "center-center", offset = (0, 0))
            ))
            self.add_child(button)
            self.dropdown_buttons.append(button)

        self.set_dropdown_visibility(False)

    def get_selected(self) -> str:
        return self.selected

    def set_dropdown_visibility(self, visible: bool) -> None:
        self.opened = visible
        for button in self.dropdown_buttons:
            button.enabled = visible
            button.style.visible = visible

    def on_mouse_down(self, mouse_button: int) -> None:
        # unselected self if clicked outside the dropdown
        if self.opened:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.dropdown_buttons + [self.top_button]:
                if button.rect.collidepoint(mouse_pos):
                    break
            else:
                self.set_dropdown_visibility(False)
                return
        super().on_mouse_down(mouse_button)

    def _on_top_click(self) -> None:
        self.set_dropdown_visibility(not self.opened)

    def on_option_click(self, option: str) -> None:
        self.set_dropdown_visibility(False)
        self.selected = option
        self.selected_text.set_text(option)
        self.on_change(option)