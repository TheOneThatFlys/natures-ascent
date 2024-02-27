import pygame, time

class Manager():
    def __init__(self, fps: int = 60):
        # stores groups
        self.groups: dict[str, pygame.sprite.Group] = {}
        # stores objects of interest
        self.objects: dict = {}
        self.fps: int = fps
        self.dt = 1
        self._last_time = time.time()

    def update_dt(self) -> None:
        "Updates delta time for current frame.\nShould be called every frame"
        now_time = time.time()
        self._dt = (now_time - self._last_time) * self.fps
        self._last_time = now_time

    def add_object(self, id, node) -> None:
        self.objects[id] = node

    def get_object_from_id(self, id: str):
        return self.objects[id]

    def add_groups(self, names: list[str]):
        for name in names:
            self.groups[name] = pygame.sprite.Group()

    def cleanup(self):
        "Call this when switching scenes to avoid memory buildup."
        self.groups = {}
        self.objects = {}

    def load_assets(self):
        pass