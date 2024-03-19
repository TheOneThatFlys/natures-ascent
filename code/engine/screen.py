from .node import Node

class Screen(Node):
    def __init__(self, parent: Node):
        super().__init__(parent)
        self.rect = parent.window.get_rect()
        
    def on_key_down(self, key):
        pass

    def on_mouse_down(self, button):
        pass

    def on_mouse_scroll(self, dy):
        pass

    def on_resize(self, new_res):
        pass