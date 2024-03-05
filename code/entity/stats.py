from dataclasses import dataclass

@dataclass
class EntityStats:
    health: float = 100.0
    contact_damage: float = 0.0
    walk_speed: float = 1
    iframes: int = 60