import pygame

from typing import TYPE_CHECKING, Any

from engine import Node, Logger, Manager, Screen
from engine.ui import *
from engine.types import *

class DebugWindow(Screen):
    ALLOWED_REC = (Node, Manager, Style, list, tuple)
    def __init__(self, parent: Node) -> None:
        super().__init__(parent)
        self.window = pygame.Window("Nature's Ascent - Debug", (640, 480))
        self.window.set_icon(self.manager.get_image("menu/tree"))
        self.window.resizable = True

        self.render_surface = self.window.get_surface()

        game_window = self.manager.get_window("main")
        # move this window to the left of main game
        self.window.position = (game_window.position[0] - self.window.size[0], game_window.position[1])

        # focus back to main game
        game_window.focus()

        self.font = pygame.font.SysFont("Consolas", 12)
        # pygame.font.Font.size() doesn't seem to calculate the right height so use this hardcoded value instead
        self.line_height = 15

        self.tab_length = self.font.size("      ")[0]
        self.padding_left = 4
        self.padding_top = 4

        self.text_colour = (255, 255, 255)
        self.background_colour = (40, 42, 54)
        self.background_colour_2 = (33, 34, 44)

        self.expanded_folders: set[Node] = set()
        self.folder_buttons: dict[Node, pygame.Rect] = []

        self.scroll_offset = 0

    def get_game_data(self) -> dict:
        """Traverse through the whole game and extract every node and its values"""
        raise NotImplementedError()

    def render_line(self, text: str, tab_index) -> pygame.Rect:
        position = pygame.Vector2(
            tab_index * self.tab_length + self.padding_left,
            self.current_line * self.line_height + self.scroll_offset + self.padding_top
        )
        self.current_line += 1
        if position.y < -50 or position.y > self.window.size[1]:
            return None
        
        # draw text
        text_surf = self.font.render(text, True, self.text_colour)
        self.render_surface.blit(text_surf, position)
        return text_surf.get_rect(topleft = position)

    def render_folder(self, folder_name: str, folder_value: Node, tab_index: int) -> pygame.Rect:
        icon = "▾" if folder_value in self.expanded_folders else "▸"
        return self.render_line(f"{icon} {folder_name}", tab_index)

    def __group_dict_items(self, dict_items: list[tuple]) -> list[tuple]:
        return map(lambda x: (x[0], tuple(x[1])) if isinstance(x[1], list) else x, sorted(dict_items, key = lambda str_val: isinstance(str_val[1], self.ALLOWED_REC)))

    def render_lists(self) -> dict:
        seen = list()
        def __rec_render(d: dict, tab_index) -> None:
            for k, v in self.__group_dict_items(d.items()):
                if k == "parent" or v in seen: continue
                if isinstance(v, self.ALLOWED_REC):
                    seen.append(v)
                    bounding_rect = self.render_folder(k, v, tab_index)
                    if bounding_rect: self.folder_buttons[v] = bounding_rect
                    if v in self.expanded_folders:
                        if isinstance(v, (list, tuple)):
                            __rec_render({i: v for i, v in enumerate(v)}, tab_index + 1)
                        else:
                            __rec_render(v.__dict__, tab_index + 1)
                else:
                    self.render_line(f"{k} = {v}", tab_index)

        self.current_line = 0
        self.folder_buttons = {}
        __rec_render(self.manager.game.__dict__, 0)

    def on_mouse_down(self, button: int) -> None:
        mouse_pos = self.manager.get_mouse_pos("debug")
        for node, rect in self.folder_buttons.items():
            if rect.collidepoint(mouse_pos):
                if node in self.expanded_folders:
                    self.expanded_folders.remove(node)
                else:
                    self.expanded_folders.add(node)

    def on_scroll(self, dx: int, dy: int) -> None:
        self.scroll_offset += dy * 20
        if self.scroll_offset > 0:
            self.scroll_offset = 0

    def update(self) -> None:
        self.render_surface.fill(self.background_colour)
        self.render_lists()

        self.window.flip()

    def on_resize(self, new_size: Vec2):
        pass

    def kill(self) -> None:
        self.window.destroy()
