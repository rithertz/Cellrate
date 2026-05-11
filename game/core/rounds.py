from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


FPS = 60


class RoundPhase(str, Enum):
    INTRO = "INTRO"
    ACTIVE = "ACTIVE"
    GEMSTONE = "GEMSTONE"
    LEVEL_COMPLETE = "LEVEL_COMPLETE"
    GAME_OVER = "GAME_OVER"


@dataclass(frozen=True)
class MechanicFlags:
    wraparound: bool = False
    speed_zones: bool = False
    magnetic_coins: bool = False
    trap_coins: bool = False
    invincibility_pickup: bool = False


@dataclass(frozen=True)
class LevelRuleSet:
    level: int
    active_frames: int
    gemstone_frames: int
    intro_frames: int
    complete_frames: int
    coin_count: int
    enemy_cap: int
    enemy_count: int
    enemy_classes: tuple[str, ...]
    mechanics: MechanicFlags
    reinforcement_schedule: tuple[tuple[int, str], ...] = ()
    zone_count: int = 0
    magnetic_coin_ratio: float = 0.0
    trap_coin_ratio: float = 0.0
    invincibility_spawn_chance: float = 0.0
    trap_slow_frames: int = FPS * 3
    trap_slow_factor: float = 0.72
    base_enemy_speed: float = 2.15
    separation_radius: float = 112.0
    separation_strength: float = 1.2
    steering_response: float = 0.18


@dataclass
class LevelState:
    level: int = 1
    phase: RoundPhase = RoundPhase.INTRO
    phase_timer: int = 0
    points: int = 0
    coins_collected_round: int = 0
    coins_collected_round_total: int = 0
    gemstones_collected: int = 0
    total_real_coins: int = 0
    run_start_ticks: int = 0
    highest_level_reached: int = 1
    run_outcome: str = "ACTIVE"

    @property
    def multiplier(self) -> int:
        return self.level


@dataclass(frozen=True)
class BotCollectibleInfo:
    kind: str
    center: tuple[float, float]
    dangerous: bool
    value: int
    magnetism: float = 0.0


@dataclass(frozen=True)
class BotEnemyInfo:
    kind: str
    center: tuple[float, float]


@dataclass(frozen=True)
class BotZoneInfo:
    rect: tuple[int, int, int, int]
    multiplier: float


@dataclass(frozen=True)
class BotWorldState:
    phase: RoundPhase
    bounds: tuple[int, int]
    wraparound: bool
    level: int
    phase_timer: int
    invulnerability_frames: int
    pending_reinforcements: tuple[int, ...]
    collectibles: tuple[BotCollectibleInfo, ...]
    enemies: tuple[BotEnemyInfo, ...]
    zones: tuple[BotZoneInfo, ...]


def gemstone_bonus_for_level(level: int) -> int:
    return 10 + max(0, level - 1) * 5


def build_level_briefing(level: int) -> tuple[str, ...]:
    lines = []
    if level == 1:
        lines.append("Classic chase layout with a slow one-by-one enemy trickle.")
    if level >= 2:
        lines.append("Wraparound edges let you escape or ambush through the opposite side.")
    if level >= 3:
        lines.append("Speed zones now boost or slow anything that crosses them.")
    if level >= 4:
        lines.append("Magnetic coins and trap coins punish greedy routes.")
    if level >= 5:
        lines.append("Invincibility pickups can appear for emergency recovery.")
    return tuple(lines)


def build_level_rules(level: int) -> LevelRuleSet:
    level = max(1, int(level))
    mechanics = MechanicFlags(
        wraparound=level >= 2,
        speed_zones=level >= 3,
        magnetic_coins=level >= 4,
        trap_coins=level >= 4,
        invincibility_pickup=level >= 5,
    )

    enemy_count = 0
    enemy_classes = ("standard",)
    reinforcement_schedule: tuple[tuple[int, str], ...] = ()
    if level >= 2:
        enemy_classes += ("interceptor",)
    if level >= 3:
        enemy_classes += ("warden",)
    if level == 1:
        enemy_count = 0
        reinforcement_schedule = (
            (2, "standard"),
            (6 * FPS, "standard"),
            (12 * FPS, "standard"),
        )
    elif level == 2:
        reinforcement_schedule = (
            (2, "standard"),
            (7 * FPS, "interceptor"),
            (13 * FPS, "standard"),
        )
    elif level == 3:
        reinforcement_schedule = (
            (2, "standard"),
            (5 * FPS, "interceptor"),
            (9 * FPS, "warden"),
            (13 * FPS, "standard"),
        )
    elif level >= 4:
        schedule = [(2, enemy_classes[0])]
        cadence = max(120, 6 * FPS - level * 24)
        for index in range(1, min(7, 3 + level)):
            kind = enemy_classes[min(index, len(enemy_classes) - 1)]
            schedule.append((2 + index * cadence, kind))
        reinforcement_schedule = tuple(schedule)

    return LevelRuleSet(
        level=level,
        active_frames=18 * FPS,
        gemstone_frames=5 * FPS,
        intro_frames=2 * FPS,
        complete_frames=0,
        coin_count=10 + level * 2,
        enemy_cap=3 if level == 1 else min(7, 3 + level),
        enemy_count=enemy_count,
        enemy_classes=enemy_classes,
        mechanics=mechanics,
        reinforcement_schedule=reinforcement_schedule,
        zone_count=0 if level < 3 else (4 if level == 3 else min(5, 2 + level // 2)),
        magnetic_coin_ratio=0.0 if level < 4 else 0.34,
        trap_coin_ratio=0.0 if level < 4 else 0.16,
        invincibility_spawn_chance=0.0 if level < 5 else min(0.55, 0.18 + level * 0.04),
        base_enemy_speed=1.7 + level * 0.19,
        separation_radius=110.0 + level * 10.0,
        separation_strength=1.12 + level * 0.08,
        steering_response=min(0.12 + level * 0.02, 0.34),
    )
