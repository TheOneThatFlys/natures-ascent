from dataclasses import dataclass

@dataclass
class EntityStats:
    health: float = 100.0
    contact_damage: float = 0.0
    walk_speed: float = 1
    iframes: int = 0

@dataclass
class EnemyStats(EntityStats):
    notice_range: float = 256
    attention_span: float = 0
    value: int = 0
    enter_sound: str = "effect/enemy_enter"

@dataclass
class PlayerStats(EntityStats):
    pickup_range: float = 128

player_stats = PlayerStats(
    health = 100,
    contact_damage = 0,
    walk_speed = 1.5,
    iframes = 60,
    pickup_range = 128,
)

enemy_stats = {
    "slime": EnemyStats(
        health = 20,
        contact_damage = 10,
        walk_speed = 0.6,
        iframes = 10,
        notice_range = 256,
        attention_span = 30,
        value = 3
    ),
    "tree_boss": EnemyStats(
        health = 300,
        contact_damage = 20,
        walk_speed = 0.3,
        iframes = 10,
        value = 40,
        enter_sound="effect/boss_enter"
    )
}