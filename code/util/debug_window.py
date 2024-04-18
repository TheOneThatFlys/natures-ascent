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

        # focus back to main game
        self.manager.game.window.focus()

    def kill(self) -> None:
        self.window.destroy()
