import pygame
from engine import Screen
from engine.ui import Element, Style, Text, Button
import util

class SettingsUI(Element):
    def __init__(self, parent):
        super().__init__(
            parent = parent,
            style = Style(
                size = parent.rect.size,
                image = util.draw_background(parent.rect.size),
            )
        )

class SettingsScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.ui = SettingsUI(self)

    def on_resize(self, new_res):
        self.ui.style.size = new_res
        self.ui.style.image = util.draw_background(new_res)
        for child in self.ui.get_all_children():
            child.redraw_image()

    def update(self):
        self.ui.update()

    def render(self, window):
        self.ui.render(window)