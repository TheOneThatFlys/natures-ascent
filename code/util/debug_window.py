import pygame

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Game

from engine import Node

class DebugWindow(Node):
    def __init__(self, parent: Node) -> None:
        super().__init__(parent)
        self.window = pygame.Window("Nature's Ascent - Debug", (640, 480))
        self.window.set_icon(self.manager.get_image("menu/tree"))

        self.render_surface = self.window.get_surface()

        game_window = self.manager.get_window("main")
        # move this window to the left of main game
        self.window.position = (game_window.position[0] - self.window.size[0], game_window.position[1])

        self.get_game_data()

        # focus back to main game
        game_window.focus()

    def get_game_data(self) -> dict:
        root = self.manager.game

        print(root.__dict__)

    def update(self) -> None:
        self.render_surface.fill((255, 255, 255))



        self.window.flip()

    def kill(self) -> None:
        self.window.destroy()
