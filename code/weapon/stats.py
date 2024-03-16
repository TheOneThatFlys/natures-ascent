from dataclasses import dataclass

@dataclass
class WeaponStats:
    size: tuple[int, int] = (100, 50)
    damage: float = 5.0
    attack_time: int = 40
    knockback: float = 4.0