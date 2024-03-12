import pygame
from util.constants import *
from engine import Screen, Sprite, ui
from entity import Player, Enemy
from world import Tile

class DebugUI(ui.Element):
    def __init__(self, parent):
        super().__init__(parent, style = ui.Style(alpha = 0, visible = False, size = parent.rect.size))

        self.fps = self.add_child(ui.Text(
            parent = self,
            text = "LOADING FPS",
            style = ui.Style(
                font = self.manager.get_font("alagard", 32),
                fore_colour = (255, 255, 255),
                alignment= "top-left",
                )
            )
        )

        self.update_timer = 0

    def update(self):
        self.update_timer += self.manager.dt
        if self.update_timer >= 20:
            self.fps.set_text(f"{round(60 / self.manager.dt)} FPS")
            self.update_timer = 0

class HudUI(ui.Element):
    BAR_PADDING = 4
    def __init__(self, parent):
        super().__init__(parent, style = ui.Style(alpha = 0, visible = True, size = parent.rect.size))

        self.health_bar = self.add_child(ui.Element(
            parent = self,
            style = ui.Style(
                alignment = "top-right",
                image = pygame.Surface((256, 32)),
                stretch_type = "none",
                offset = (16, 16),
                colour = (0, 0, 0),
                fore_colour = (60, 222, 34)
                )
            ))

        self.cached_values = {"player.health": -1, "player.stats.health": -1}

    def update(self):
        # player health bar
        player: Player = self.manager.get_object_from_id("player")
        
        # cache values to prevent ui updates every frame
        if player.health != self.cached_values["player.health"] or player.stats.health != self.cached_values["player.stats.health"]:

            self.health_bar.image = pygame.Surface(self.health_bar.image.get_size(), pygame.SRCALPHA)
            border_rect = self.health_bar.image.get_rect()
            
            health_rect = pygame.Rect(
                self.BAR_PADDING,
                self.BAR_PADDING,
                (player.health / player.stats.health) * (self.health_bar.rect.width - 2 * self.BAR_PADDING),
                self.health_bar.rect.height - 2 * self.BAR_PADDING
                )

            shading_rect = health_rect.copy()
            shading_rect.width = self.health_bar.rect.width - 2 * self.BAR_PADDING

            pygame.draw.rect(self.health_bar.image, (0, 0, 0), border_rect, border_radius = 4)
            pygame.draw.rect(self.health_bar.image, (15, 15, 15), shading_rect, border_radius = 4)
            pygame.draw.rect(self.health_bar.image, self.health_bar.style.fore_colour, health_rect, border_radius = 4)

            # re-cache values
            self.cached_values["player.health"] = player.health
            self.cached_values["player.stats.health"] = player.stats.health

            pygame.display.get_surface().blit(self.health_bar.image, (0, 0))

class Level(Screen):
    def __init__(self, game):
        super().__init__("level", parent = game, reset_on_load = True)
        self.game_surface = pygame.Surface(game.window.get_size())

        self.manager.add_groups(["render", "update", "collide", "enemy"])

        self.player = self.add_child(Player(self, pygame.Vector2(-TILE_SIZE, 0)))
        self.camera = self.add_child(FollowCameraLayered(self, target_sprite=self.player, follow_speed=0.1))

        self._add_ui_components()
        self._gen_test_map()

    def _add_ui_components(self):
        self.master_ui = ui.Element(
            self,
            style = ui.Style(
                size = self.rect.size,
                alpha = 0
            )
        )

        self.debug_ui = self.master_ui.add_child(DebugUI(self.master_ui))
        self.hud_ui = self.master_ui.add_child(HudUI(self.master_ui))

    def toggle_debug(self):
        self.debug_ui.style.visible = not self.debug_ui.style.visible

    def _gen_test_map(self, n = 10):
        temp = pygame.Surface((TILE_SIZE, TILE_SIZE))
        temp.fill((255, 255, 255))
        for i in range(n):
            self.add_child(Tile(self, temp, (i * TILE_SIZE, i* TILE_SIZE)))
        self.add_child(Enemy(self, (-TILE_SIZE, -TILE_SIZE)))

    def on_key_down(self, key):
        if key == pygame.K_r:
            # restart level
            self.reset()
        elif key == pygame.K_F3:
            self.toggle_debug()

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
        self.master_ui.update()

    def render(self, surface: pygame.Surface):
        # clear game surface
        self.game_surface.fill((30, 31, 33))

        # render objects with layered camera
        self.camera.render(
            surface = self.game_surface,
            sprite_group = self.manager.groups["render"]
        )

        # render GUI elements
        self.master_ui.render(self.game_surface)

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