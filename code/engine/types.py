from typing import Literal

Alignment = Literal["top-left", "top-right", "bottom-left", "bottom-right", "center-left", "center-right", "top-center", "bottom-center", "center-center"]
Position = Literal["absolute", "relative"]
Colour = tuple[int, int, int]
StretchType = Literal["skew", "expand", "none"]
Direction = Literal["up", "down", "left", "right"]
Vec2 = tuple[float, float]
WindowMode = Literal["windowed", "borderless", "fullscreen"]

class DebugExpandable:
    """Inherit from this to make a class be expandable in the debug menu."""
    pass