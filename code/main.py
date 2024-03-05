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
        self.manager.set_pixel_scale(2)
        self.manager.load_assets()

        pygame.display.set_icon(self.manager.get_image("tree"))

        # dictionary to hold screens
        self._screens: dict[str, Screen] = {}
        self.current_screen: str = None

        self.add_screen(Level(self))
        self.add_screen(Menu(self))
        self.set_screen("menu")

    def queue_close(self):
        "Quits program after current game loop finishes"
        self.running = False

    def add_screen(self, screen: Screen):
        "Add screen object to screen dictionary, key being screen.name"
        self._screens[screen.name] = screen

    def set_screen(self, screen_name: str):
        "Sets the current screen based on screen name"
        self.current_screen = screen_name

        if self._screens[screen_name].reset_on_load:
            self._screens[screen_name].reset()

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
                    self._screens[self.current_screen].on_key_down(event.key)
                    if event.key == pygame.K_F9:
                        # reload assets
                        print("[DEBUG] Reloading assets...")
                        self.manager.load_assets()

                        current_screen = self._screens[self.current_screen]
                        current_screen.__init__(self)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._screens[self.current_screen].on_mouse_down(event.button)
                elif event.type == pygame.VIDEORESIZE:
                    self._screens[self.current_screen].on_resize(event.size)

            self._screens[self.current_screen].update()

            # clear the window
            self.window.fill((0, 0, 0))
            # draw screen to window
            self._screens[self.current_screen].render(self.window)
            pygame.display.update()

        pygame.quit()

if __name__ == "__main__":
    Game().run()
