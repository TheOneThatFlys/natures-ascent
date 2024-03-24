from dataclasses import dataclass

@dataclass
class EntityStats:
    health: float = 100.0
    contact_damage: float = 0.0
    walk_speed: float = 1
    iframes: int = 60

@dataclass
class PlayerStats(EntityStats):
    pickup_range: float = 128

player_stats = PlayerStats(
    health = 100,
    contact_damage = 0,
    walk_speed = 1.5,
    iframes = 60,
    pickup_range = 128
)

enemy_stats = {
    "slime": EntityStats(
        health = 20,
        contact_damage = 10,
        walk_speed = 0.6,
        iframes = 10
    )
}