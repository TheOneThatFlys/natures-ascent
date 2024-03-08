import pygame, time, os

class Font():
    def __init__(self, font_path: str):
        self._fonts = {}
        self.path = font_path

    def get(self, font_size: int) -> pygame.font.Font:
        # if font already cached, then return cached font
        if font_size in self._fonts:
            return self._fonts[font_size]
        
        # else create a new font and add to the cache
        new_font = pygame.font.Font(self.path, font_size)
        self._fonts[font_size] = new_font
        return new_font

class Manager():
    def __init__(self, fps: int = 60):
        # stores groups
        self.groups: dict[str, pygame.sprite.Group] = {}
        # stores objects of interest
        self.objects: dict = {}
        # stores loaded assets
        self.assets: dict = {"image": {}, "sound": {}, "font": {}}

        self.fps: int = fps
        self.dt = 1
        self._last_time = time.time()
        self._load_scale = 1

    def update_dt(self) -> None:
        "Updates delta time for current frame. Should be called every frame"
        now_time = time.time()
        self.dt = self.fps * (now_time - self._last_time)
        self._last_time = now_time

    def add_object(self, id, node):
        self.objects[id] = node
        return node

    def get_object_from_id(self, id: str):
        return self.objects[id]

    def add_groups(self, names: list[str]):
        for name in names:
            self.groups[name] = pygame.sprite.Group()

    def cleanup(self):
        "Call this when switching scenes to avoid memory buildup."
        self.groups = {}
        self.objects = {}

    def set_pixel_scale(self, scale: int):
        "Set scale for loading assets"
        self._load_scale = scale

    def load_assets(self):
        """
        Loads all supported files in ./assets

        Assets folder must contain image, font, sound sub directories

        Supported files:
        - png
        - ttf
        - mp3
        """

        # clear assets in case this function was called multiple times
        self.assets = {"image": {}, "sound": {}, "font": {}}

        # maps folder name to extension
        ext_dir_map = {
            "png": "image",
            "ttf": "font",
            "mp3": "sound",
        }

        for dirpath, dirnames, filenames in os.walk("assets"):
            # go through each file
            for filename in filenames:

                fullpath = os.path.join(dirpath, filename)
                extension = os.path.splitext(filename)[1][1:]
                loaded_asset = None

                if extension == "png":
                    loaded_asset = pygame.image.load(fullpath).convert_alpha()
                    # scale asset up
                    loaded_asset = pygame.transform.scale(
                        loaded_asset,
                        (
                            loaded_asset.get_width() * self._load_scale,
                            loaded_asset.get_height() * self._load_scale
                        )
                    )
                
                elif extension == "ttf":
                    loaded_asset = Font(fullpath)

                elif extension == "mp3":
                    loaded_asset = pygame.mixer.Sound(fullpath)

                if loaded_asset:
                    key = fullpath.removeprefix(os.path.join("assets", ext_dir_map[extension]) + "\\").removesuffix("." + extension)
                    key = key.replace("\\", "/")
                    self.assets[ext_dir_map[extension]][key] = loaded_asset

    def get_image(self, name: str) -> pygame.Surface:
        return self.assets["image"][name]
    
    def get_font(self, name: str, size: int) -> pygame.font.Font:
        return self.assets["font"][name].get(size)
    
    def get_sound(self, name: str) -> pygame.mixer.Sound:
        return self.assets["sound"][name]
    
    def play_sound(self, *, sound_object: pygame.mixer.Sound = None, sound_name: str = None, volume: float = 1.0):
        if sound_object:
            s = sound_object
        elif sound_name:
            s = self.get_sound(sound_name)
        else:
            raise TypeError("Manager.play_sound() requires either sound object or sound name arguement")
        s.set_volume(volume)
        s.play()


