import pygame

from typing import Callable

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
    def __init__(self, parent: Element, style: Style, options: list[str], on_change: Callable[[str], None]) -> None:
        super().__init__(parent, style)

        self.selected_box = self.add_child(Text(self, style = style, text = options[0]))

        self.on_change = on_change

        self.options = options

        # for option in options:
        #     self.add_child(Button(self, style = style, on_click = self.on_option_click, click_args = (option,)))

    def on_option_click(self, option: str) -> None:
        print(option)