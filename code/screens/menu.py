import pygame

from engine import Screen
from engine.ui import Element, Style, Text, Button
import util

from .common import TextButton, TextButtonColours

class Menu(Screen):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        
        self.master_container = Element(
            parent = self,
            style = Style(
                size = self.rect.size,
                image = util.draw_background(self.rect.size),
                colour = (78, 173, 245)
            )
        )

        self.tree_img = self.master_container.add_child(
            Element(
                self.master_container,
                style = Style(
                    size = (384, 384),
                    image = self.manager.get_image("menu/tree"),
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
                    offset = (0, 64),
                    fore_colour = (99, 169, 65),
                    colour = (23, 68, 41),
                    text_shadow = 2,
                    font = self.manager.get_font("alagard", 72),
                )
            )
        )

        button_colours = TextButtonColours(
            colour = (99, 169, 65),
            colour_shadow = (23, 68, 41),
            hover_colour = (95, 41, 46),
            hover_colour_shadow = (51, 22, 31)
        )

        self.play_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.title.rect.bottom + 16,
            text = "New Run",
            on_click = self.parent.set_screen,
            click_args = ["level"],
            colours = button_colours
        ))

        self.leaderboard_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.play_button.rect.bottom,
            text = "Leaderboard",
            enabled = False,
            colours = button_colours
        ))

        self.settings_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.leaderboard_button.rect.bottom,
            text = "Settings",
            on_click = self.parent.set_screen,
            click_args = ["settings"],
            colours = button_colours
        ))
        
        self.exit_button = self.master_container.add_child(TextButton(
            parent = self.master_container,
            yoffset = self.settings_button.rect.bottom,
            text = "Exit",
            text_hover = ":c",
            on_click = self.parent.queue_close,
            colours = button_colours
        ))

        self.secret_button = self.tree_img.add_child(Button(
            parent = self.tree_img,
            style = Style(
                size = (8, 8),
                position = "relative",
                alignment = "center-center",
                visible = False
            ),
            hover_style = None,
            on_click = self._toggle_secret,
            hover_sound = None,
            click_sound = "effect/hit_alt"
        ))

        self.bg_offset = 0
        self.secret_activated = False

        self.manager.play_sound(sound_name = "music/menu", volume = 0.5, loop = True)
            
    def _toggle_secret(self) -> None:
        self.secret_activated = not self.secret_activated

    def on_resize(self, new_res) -> None:
        self.master_container.style.size = new_res
        self.master_container.style.image = util.draw_background(new_res)

        for item in self.master_container.get_all_children():
            item.redraw_image()

    def on_mouse_down(self, button: int) -> None:
        self.master_container.on_mouse_down(button, pygame.mouse.get_pos())

    def render(self, window) -> None:
        self.master_container.render(window)

    def update(self) -> None:
        self.master_container.update()

        if self.secret_activated:
            self.master_container.image = util.draw_background(self.rect.size, offset = self.bg_offset)
            self.bg_offset += 1
            if self.bg_offset >= 14:
                self.bg_offset -= 14