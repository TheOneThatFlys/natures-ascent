import pygame

from typing import TYPE_CHECKING, Any

from engine import Node, Logger, Manager, Screen
from engine.ui import *
from engine.types import *

class DebugWindow(Screen):
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

        self.font = pygame.font.SysFont("Consolas", 11)
        self.line_height = self.font.size("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!£$%^&*()[]-=_+;':,./<>?")[1]
        self.tab_length = self.font.size("  ")[0]

        self.text_colour = (0, 0, 0)
        self.line_colour_1 = (255, 255, 255)
        self.line_colour_2 = (200, 200, 200)

        self.expanded_folders: set[Node] = set()
        self.folder_buttons: dict[Node, pygame.Rect] = []

        self.scroll_offset = 0

    def get_game_data(self) -> dict:
        """Traverse through the whole game and extract every node and its values"""
        raise NotImplementedError()

    def render_line(self, text: str, tab_index) -> pygame.Rect:
        position = pygame.Vector2(tab_index * self.tab_length, self.current_line * self.line_height + self.scroll_offset)
        self.current_line += 1
        if position.y < -50 or position.y > self.window.size[1]:
            return None
        text_surf = self.font.render(text, True, self.text_colour)
        self.render_surface.blit(text_surf, position)
        return text_surf.get_rect(topleft = position)

    def render_lists(self) -> dict:
        ALLOWED_REC = (Node, Manager)
        seen = []
        def __rec_render(d: dict, tab_index) -> None:
            for k, v in d.items():
                if k == "parent" or k == "manager" or v in seen: continue
                if isinstance(v, ALLOWED_REC):
                    seen.append(v)
                    bounding_rect = self.render_line(f"----folder---- ({k})", tab_index)
                    if bounding_rect: self.folder_buttons[v] = bounding_rect
                    if v in self.expanded_folders:
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

    def update(self) -> None:
        self.render_surface.fill((255, 255, 255))
        self.render_lists()
        self.window.flip()

    def on_resize(self, new_size: Vec2):
        pass

    def kill(self) -> None:
        self.window.destroy()
