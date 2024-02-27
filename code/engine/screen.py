from .node import Node

class Screen(Node):
    def __init__(self, name: str, parent: Node, reset_on_load: bool = False):
        super().__init__(parent)
        self.name = name
        self.rect = parent.window.get_rect()
        self.reset_on_load = reset_on_load
        
    def on_key_down(self, key):
        pass

    def on_mouse_down(self, button):
        pass

    def on_mouse_scroll(self, dy):
        pass

    def on_resize(self, new_res):
        pass

    def reset(self):
        self.__init__(self.name, self.parent, self.reset_on_load)