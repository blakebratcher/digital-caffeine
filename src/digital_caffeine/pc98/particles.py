"""Steam and drip particle systems for PC-98 coffee scene."""

from __future__ import annotations

import math
from dataclasses import dataclass

from digital_caffeine.pc98.palette import (
    CHOCOLATE,
    CREAM,
    DEEP_NAVY,
    LIGHT_GRAY,
    OFF_WHITE,
    SLATE,
    WARM_BROWN,
    WARM_GRAY,
)
from digital_caffeine.pc98.sprites import SCENE_H, SCENE_W


@dataclass
class SteamParticle:
    """A single rising steam wisp."""

    x: float
    y: float
    amplitude: float
    frequency: float
    speed: float
    phase: float
    age: int = 0

    def reset(self, spawn_y: float, x_center: int) -> None:
        self.y = spawn_y
        self.age = 0


# More nuanced color fade: bright near cup, graceful fade upward
_STEAM_COLORS_BY_AGE = [
    OFF_WHITE,    # 0-5: bright white wisp fresh off the cup
    CREAM,        # 6-12: warm cream
    LIGHT_GRAY,   # 13-20: cooling
    WARM_GRAY,    # 21-30: fading
    SLATE,        # 31-38: almost gone
    DEEP_NAVY,    # 39+: invisible (matches background)
]


class SteamSystem:
    """Pool of steam particles that rise from the cup mouth."""

    def __init__(self, count: int, spawn_y: float, x_center: int) -> None:
        self.spawn_y = spawn_y
        self.x_center = x_center
        self.frame = 0
        self.particles: list[SteamParticle] = []
        self._max_age = 45
        for i in range(count):
            p = SteamParticle(
                x=x_center + (i % 7 - 3) * 2.5,
                y=spawn_y - (i * self._max_age / count),
                amplitude=1.2 + (i % 4) * 0.7,
                frequency=0.06 + (i % 5) * 0.015,
                speed=0.4 + (i % 3) * 0.12,
                phase=i * 1.1,
            )
            self.particles.append(p)

    def update(self) -> None:
        self.frame += 1
        for p in self.particles:
            p.y -= p.speed
            drift = math.sin(self.frame * p.frequency + p.phase) * p.amplitude
            p.x = self.x_center + drift + (p.phase % 7 - 3) * 1.5
            p.age += 1
            if p.age >= self._max_age or p.y < -2:
                p.x = self.x_center + (p.phase % 7 - 3) * 2.5
                p.reset(self.spawn_y, self.x_center)

    def get_draw_list(self) -> list[tuple[int, int, int]]:
        draws = []
        for p in self.particles:
            ix = int(round(p.x))
            iy = int(round(p.y))
            if 0 <= ix < SCENE_W and 0 <= iy < SCENE_H:
                ci = self._color_for_age(p.age)
                draws.append((ix, iy, ci))
                # Wider wisps when young
                if p.age < 25 and 0 <= ix - 1 < SCENE_W:
                    draws.append((ix - 1, iy, ci))
                if p.age < 15 and 0 <= ix + 1 < SCENE_W:
                    draws.append((ix + 1, iy, ci))
                # Extra wide when very fresh
                if p.age < 6:
                    if 0 <= ix - 2 < SCENE_W:
                        draws.append((ix - 2, iy, CREAM))
                    if 0 <= ix + 2 < SCENE_W:
                        draws.append((ix + 2, iy, CREAM))
        return draws

    @staticmethod
    def _color_for_age(age: int) -> int:
        if age < 6:
            return _STEAM_COLORS_BY_AGE[0]
        if age < 13:
            return _STEAM_COLORS_BY_AGE[1]
        if age < 21:
            return _STEAM_COLORS_BY_AGE[2]
        if age < 31:
            return _STEAM_COLORS_BY_AGE[3]
        if age < 39:
            return _STEAM_COLORS_BY_AGE[4]
        return _STEAM_COLORS_BY_AGE[5]


@dataclass
class DripParticle:
    x: int
    y: float
    age: int = 0
    active: bool = True


class DripSystem:
    """Spawns occasional drip particles below the cup."""

    def __init__(self, spawn_y: int, x_min: int, x_max: int) -> None:
        self.spawn_y = spawn_y
        self.x_min = x_min
        self.x_max = x_max
        self.frame = 0
        self._drips: list[DripParticle] = []
        self._spawn_interval = 60
        self._max_age = 10

    def update(self) -> None:
        self.frame += 1
        for d in self._drips:
            if d.active:
                d.y += 1.0
                d.age += 1
                if d.age >= self._max_age:
                    d.active = False
        self._drips = [d for d in self._drips if d.active]
        if self.frame % self._spawn_interval == 0 and len(self._drips) < 2:
            if (self.frame // 60) % 5 < 2:  # ~40% chance
                seed = self.frame * 31 + 17
                x = self.x_min + (seed % (self.x_max - self.x_min))
                self._drips.append(DripParticle(x=x, y=float(self.spawn_y)))

    def get_draw_list(self) -> list[tuple[int, int, int]]:
        draws = []
        for d in self._drips:
            if d.active:
                color = CHOCOLATE if d.age < 5 else WARM_BROWN
                draws.append((d.x, int(d.y), color))
        return draws
