import pygame
from engine import Screen
from engine.ui import Element, Style, Text, Button
from util import parse_spritesheet

class Menu(Screen):
    def __init__(self, parent):
        super().__init__("menu", parent)
        
        self.master_container = Element(
            parent = self,
            style = Style(
                size = self.rect.size,
                colour = (15,15,15)
            )
        )

        self.title = self.master_container.add_child(
            Text(
                parent = self.master_container,
                text = "Nature's Ascent",
                style = Style(
                    alignment = "top-center",
                    offset = (0, 100),
                    fore_colour = (99, 169, 65),
                    colour = (23, 68, 41),
                    text_shadow = True,
                    font = self.manager.get_font("alagard", 72),
                )
            )
        )

        self.tree_img = self.master_container.add_child(
            Element(
                self,
                style = Style(
                    size = (384, 384),
                    image = self.manager.get_image("tree"),
                    stretch_type = "expand",
                    alignment = "bottom-center"
                )
            )
        )

        play_norm, play_hover = parse_spritesheet(self.manager.get_image("playbutton"), frame_count=2)
        self.play_button = self.master_container.add_child(
            Button(
                parent = self.master_container,
                style = Style(
                    alignment = "top-center",
                    position = "absolute",
                    offset = (0, self.title.rect.bottom + (self.tree_img.rect.y - self.title.rect.bottom) / 2 - 48),
                    size = (96, 96),
                    image = play_norm,
                    stretch_type = "expand",
                ),
                hover_style = Style(
                    image = play_hover,
                ),
                on_click = self.parent.set_screen,
                click_args = ("level",),
            )
        )

    def on_resize(self, new_res):
        # on resize: just recreate menu with new res
        self.__init__(self.parent)

    def render(self, window):
        self.master_container.render(window)

    def update(self):
        self.master_container.update()