from __future__ import annotations

from dataclasses import dataclass
import math
import random


LEVEL_THRESHOLDS = [0, 4, 8, 13, 18, 24, 31, 39, 48, 58]
POST_THRESHOLD_STEP = 11
ENEMY_BRAINS = ("hunter", "flanker", "interceptor", "blocker", "herder")


@dataclass(frozen=True)
class DifficultyProfile:
    level: int
    score: int
    enemy_speed: float
    chase_efficiency: float
    separation_radius: float
    separation_strength: float
    steering_response: float
    spawn_spacing: float
    player_spawn_buffer: float
    spawn_repulsion_frames: int
    spawn_repulsion_strength: float
    flank_weight: float
    player_speed_gain: float
    max_enemies: int
    target_enemy_count: int


def level_for_score(score: int) -> int:
    score = max(0, int(score))
    for index, threshold in enumerate(LEVEL_THRESHOLDS[1:], start=2):
        if score < threshold:
            return index - 1

    overflow = max(0, score - LEVEL_THRESHOLDS[-1])
    return len(LEVEL_THRESHOLDS) + overflow // POST_THRESHOLD_STEP


def score_for_level(level: int) -> int:
    if level <= 1:
        return 0
    if level <= len(LEVEL_THRESHOLDS):
        return LEVEL_THRESHOLDS[level - 1]
    extra_levels = level - len(LEVEL_THRESHOLDS)
    return LEVEL_THRESHOLDS[-1] + extra_levels * POST_THRESHOLD_STEP


def target_enemy_count_for_level(level: int, max_enemies: int) -> int:
    if level <= 1:
        return 1
    target = 1 + level // 2
    if level >= 6:
        target += 1
    if level >= 10:
        target += 1
    return max(1, min(max_enemies, target))


def build_profile(score: int) -> DifficultyProfile:
    level = level_for_score(score)
    flank_weight = 0.0
    if level >= 5:
        flank_weight = 0.12
    if level >= 7:
        flank_weight = 0.22
    if level >= 10:
        flank_weight = 0.34

    max_enemies = min(10, 3 + level // 2)
    target_enemies = target_enemy_count_for_level(level, max_enemies)

    return DifficultyProfile(
        level=level,
        score=max(0, int(score)),
        enemy_speed=min(0.95 + level * 0.17 + score * 0.026, 7.9),
        chase_efficiency=min(0.24 + level * 0.052 + score * 0.0055, 0.92),
        separation_radius=118.0 + level * 7.0,
        separation_strength=1.24 + level * 0.08,
        steering_response=min(0.18 + level * 0.014, 0.34),
        spawn_spacing=190.0 + level * 18.0,
        player_spawn_buffer=170.0 + level * 6.0,
        spawn_repulsion_frames=96,
        spawn_repulsion_strength=1.45 + level * 0.1,
        flank_weight=flank_weight,
        player_speed_gain=0.08 + min(0.22, level * 0.028),
        max_enemies=max_enemies,
        target_enemy_count=target_enemies,
    )


def choose_enemy_brain(level: int, rng=None) -> str:
    rng = rng or random
    weighted_choices = [("hunter", 7)]
    if level >= 2:
        weighted_choices.append(("flanker", 4))
    if level >= 4:
        weighted_choices.append(("interceptor", 4))
    if level >= 5:
        weighted_choices.append(("blocker", 3))
    if level >= 7:
        weighted_choices.append(("herder", 3))

    total_weight = sum(weight for _, weight in weighted_choices)
    roll = rng.uniform(0.0, total_weight)
    running = 0.0
    for brain, weight in weighted_choices:
        running += weight
        if roll <= running:
            return brain
    return weighted_choices[-1][0]


def choose_spawn_point(width, height, size, player_center, enemy_centers, profile, rng=None, samples=20):
    rng = rng or random
    margin = size + 40
    best_candidate = None
    best_score = float("-inf")
    side_counts = _count_sides(width, height, enemy_centers)

    for _ in range(max(8, samples)):
        candidate = _sample_edge_point(width, height, size, margin, rng)
        center = (candidate[0] + size / 2.0, candidate[1] + size / 2.0)
        if _is_spawn_candidate_safe(center, player_center, enemy_centers, profile):
            return candidate
        score = _score_spawn_candidate(center, candidate[2], player_center, enemy_centers, side_counts, profile)
        if score > best_score:
            best_score = score
            best_candidate = candidate
        if score >= 0:
            break

    if best_candidate is None:
        best_candidate = (0, -margin, "top")
    return best_candidate


def _is_spawn_candidate_safe(center, player_center, enemy_centers, profile):
    if math.dist(center, player_center) < profile.player_spawn_buffer:
        return False
    if enemy_centers:
        nearest_enemy_distance = min(math.dist(center, enemy_center) for enemy_center in enemy_centers)
        if nearest_enemy_distance < profile.spawn_spacing:
            return False
    return True


def _sample_edge_point(width, height, size, margin, rng):
    side = rng.choice(("top", "right", "bottom", "left"))
    if side == "top":
        x = rng.randint(0, max(0, width - size))
        y = -margin
    elif side == "right":
        x = width + margin
        y = rng.randint(0, max(0, height - size))
    elif side == "bottom":
        x = rng.randint(0, max(0, width - size))
        y = height + margin
    else:
        x = -margin
        y = rng.randint(0, max(0, height - size))
    return x, y, side


def _score_spawn_candidate(center, side, player_center, enemy_centers, side_counts, profile):
    distance_to_player = math.dist(center, player_center)
    if distance_to_player < profile.player_spawn_buffer:
        return distance_to_player - profile.player_spawn_buffer - 300.0

    nearest_enemy_distance = min((math.dist(center, enemy_center) for enemy_center in enemy_centers), default=profile.spawn_spacing + 80.0)
    spacing_score = nearest_enemy_distance - profile.spawn_spacing
    if nearest_enemy_distance < profile.spawn_spacing:
        spacing_score -= (profile.spawn_spacing - nearest_enemy_distance) * 4.0

    lane_penalty = 0.0
    candidate_vector = (player_center[0] - center[0], player_center[1] - center[1])
    candidate_length = math.hypot(*candidate_vector) or 1.0
    for enemy_center in enemy_centers:
        enemy_vector = (player_center[0] - enemy_center[0], player_center[1] - enemy_center[1])
        enemy_length = math.hypot(*enemy_vector) or 1.0
        dot = (
            candidate_vector[0] * enemy_vector[0] + candidate_vector[1] * enemy_vector[1]
        ) / (candidate_length * enemy_length)
        if dot > 0.965:
            lane_penalty += (dot - 0.965) * 850.0

    side_penalty = side_counts.get(side, 0) * 42.0
    return spacing_score + distance_to_player * 0.22 - lane_penalty - side_penalty


def _count_sides(width, height, enemy_centers):
    counts = {"top": 0, "right": 0, "bottom": 0, "left": 0}
    if not enemy_centers:
        return counts

    horizontal_mid = width / 2.0
    vertical_mid = height / 2.0
    for x, y in enemy_centers:
        if y < 0:
            counts["top"] += 1
        elif y > height:
            counts["bottom"] += 1
        elif x < 0:
            counts["left"] += 1
        elif x > width:
            counts["right"] += 1
        elif abs(x - horizontal_mid) > abs(y - vertical_mid):
            counts["left" if x < horizontal_mid else "right"] += 1
        else:
            counts["top" if y < vertical_mid else "bottom"] += 1
    return counts
