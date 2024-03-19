# TODO:
# - MAKE ASSETS - FEEL POLISHED
# Weapon system - equip & inv
# Rooms
# Generation

from __future__ import annotations

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import pygame
pygame.init()
from typing import Callable
from util.constants import *
from engine import Screen, Manager
from screens import Level, Menu

class Game:
    # main game class that manages screens and pygame events
    def __init__(self):

        self.running = True

        self.dt = 1

        self.window = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        pygame.display.set_caption("Nature's Ascent")

        self.manager = Manager()
        self.manager.set_pixel_scale(PIXEL_SCALE)
        self.manager.load()

        pygame.display.set_icon(self.manager.get_image("menu/tree"))

        # dictionary to hold screens
        self._screens: dict[str, Callable[[Game], None]] = {}
        self.current_screen: str = None
        self.current_screen_instance: Screen = None

        self.add_screen("level", Level)
        self.add_screen("menu", Menu)
        self.set_screen("menu")

    def queue_close(self):
        "Quits program after current game loop finishes"
        self.running = False

    def add_screen(self, name: str, screen: Callable[[Game], None]):
        "Add screen object to screen dictionary, key being screen.name"
        self._screens[name] = screen

    def set_screen(self, screen_name: str):
        "Sets the current screen based on screen name"
        if screen_name == self.current_screen: return
        self.current_screen = screen_name
        self.current_screen_instance = self._screens[screen_name](self)

    def run(self):
        # main loop
        while self.running:
            # maintain constant fps
            self.clock.tick(FPS)
            # calculate dt
            self.manager.update_dt()

            # poll events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.queue_close()

                # delegate certain events to current screen
                elif event.type == pygame.KEYDOWN:
                    self.current_screen_instance.on_key_down(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.current_screen_instance.on_mouse_down(event.button)
                elif event.type == pygame.VIDEORESIZE:
                    self.current_screen_instance.on_resize(event.size)

            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            self.current_screen_instance.update()

            # clear the window
            self.window.fill((0, 0, 0))
            # draw screen to window
            self.current_screen_instance.render(self.window)
            pygame.display.update()

        pygame.quit()

if __name__ == "__main__":
    Game().run()
