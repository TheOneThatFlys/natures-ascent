import pygame
from util.constants import *
from engine import Screen, Sprite
from entity import Player, Enemy
from world import Tile

class Level(Screen):
    def __init__(self, game):
        super().__init__("level", parent = game, reset_on_load = True)
        self.game_surface = pygame.Surface(game.window.get_size())

        self.manager.add_groups(["render", "update", "collide", "enemy"])

        self.player = self.add_child(Player(self, pygame.Vector2(0, 0)))
        self.camera = self.add_child(FollowCameraLayered(self, target_sprite=self.player, follow_speed=0.1))

        self._gen_test_map()

    def _gen_test_map(self, n = 10):
        temp = pygame.Surface((TILE_SIZE, TILE_SIZE))
        temp.fill((255, 255, 255))
        for i in range(n):
            Tile(self, temp, (i * TILE_SIZE, i* TILE_SIZE))
        Enemy(self, (-TILE_SIZE, -TILE_SIZE))

    def on_key_down(self, key):
        if key == pygame.K_r:
            # restart level
            self.__init__()

    def on_resize(self, new_size):
        # remake game surface to new size
        self.game_surface = pygame.Surface(new_size)
        # recalibrate camera
        self.camera.set_screen_size(new_size)

    def reset(self):
        self.__init__(self.parent)

    def update(self):
        # update all sprites in update group
        self.manager.groups["update"].update()

    def render(self, surface: pygame.Surface):
        # clear game surface
        self.game_surface.fill((0, 0, 0))

        # render objects with layered camera
        self.camera.render(
            surface = self.game_surface,
            sprite_group = self.manager.groups["render"]
        )

        # render GUI elements

        # render to window
        surface.blit(self.game_surface, (0, 0))

class FollowCameraLayered(Sprite):
    def __init__(self, level, target_sprite, follow_speed = 2, tolerence = 5):
        super().__init__(parent = level, groups=["update"])
        self.id = "camera"
        self.window = pygame.display.get_surface()

        self.target = target_sprite
        self.pos = pygame.Vector2(target_sprite.rect.center)
        self.follow_divider = 1 / follow_speed
        self.tolerence = tolerence

        self.set_screen_size(self.window.get_size())

        self.offset = pygame.Vector2()

    def update(self):
        # move camera closer to target
        self.pos += self.manager.dt * (self.target.rect.center - self.pos) / self.follow_divider

    def set_screen_size(self, new_size):
        """Set new screen size to center camera on"""
        self.half_screen_size = pygame.Vector2(new_size[0] // 2, new_size[1] // 2)

    def convert_coords(self, old_coords: pygame.Vector2) -> pygame.Vector2:
        """Converts absolute world coords to scaled coords on screen"""
        return pygame.Vector2(
            old_coords.x - (self.pos.x - self.half_screen_size.x),
            old_coords.y - (self.pos.y - self.half_screen_size.y)
        )

    def render(self, surface: pygame.Surface, sprite_group: pygame.sprite.Group):
        # render sprites centered on camera position
        self.offset.x = self.pos.x - self.half_screen_size.x
        self.offset.y = self.pos.y - self.half_screen_size.y

        # render sprites based on y position
        for sprite in sorted(sprite_group.sprites(), key = lambda s: s.rect.centery):
            new_pos = (sprite.rect.x - self.offset.x, sprite.rect.y - self.offset.y)
            surface.blit(sprite.image, new_pos)