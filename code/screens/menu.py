import pygame
from engine import Screen
from engine.ui import Element, Style, Text, Button
from util import parse_spritesheet

class TextButtonMenu(Button):
    def __init__(self, parent, yoffset, text):
        super().__init__(
            parent = parent,
            style = Style(
                alignment = "top-center",
                offset = (0, yoffset),
                size = (1, 1),
                alpha = 0
                ),
            hover_style=None
            )

        text_size = self.manager.get_font("alagard", 32).size(text)
        self.style.size = text_size[0] + 4, text_size[1] + 4
        self.hover_style.size = self.style.size
        self.redraw_image()

        self.text = self.add_child(Text(
            self,
            Style(
                font = self.manager.get_font("alagard", 32),
                colour = (23, 68, 41),
                fore_colour = (99, 169, 65),
                alignment = "center-center",
                position = "relative",
                text_shadow = True,
            ),
            text
        ))


    def update(self):
        super().update()
        if self.hovering and not self.last_hovering:
            self.text.style.colour = (51, 22, 31)
            self.text.style.fore_colour = (95, 41, 46)
            self.text.redraw_image()
        elif not self.hovering and self.last_hovering:
            self.text.style.colour = (23, 68, 41)
            self.text.style.fore_colour = (99, 169, 65)
            self.text.redraw_image()


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

        self.tree_img = self.master_container.add_child(
            Element(
                self.master_container,
                style = Style(
                    size = (384, 384),
                    image = self.manager.get_image("tree"),
                    stretch_type = "expand",
                    alignment = "bottom-center"
                )
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


        self.play_button = self.master_container.add_child(TextButtonMenu(self.master_container, self.title.rect.bottom + 16, "NEW RUN"))
        self.leaderboard_button = self.master_container.add_child(TextButtonMenu(self.master_container, self.play_button.rect.bottom, "LEADERBOARD"))

    def on_resize(self, new_res):
        # on resize: just recreate menu with new res
        self.__init__(self.parent)

    def render(self, window):
        self.master_container.render(window)

    def update(self):
        self.master_container.update()