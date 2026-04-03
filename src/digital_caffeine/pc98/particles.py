"""Steam and drip particle systems for PC-98 coffee scene."""

from __future__ import annotations

import math
from dataclasses import dataclass

from digital_caffeine.pc98.palette import CHOCOLATE, CREAM, DEEP_NAVY, WARM_BROWN, WARM_GRAY


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


_STEAM_COLORS_BY_AGE = [
    CREAM,      # 0-9 frames
    WARM_GRAY,  # 10-24
    DEEP_NAVY,  # 25+
]


class SteamSystem:
    """Pool of steam particles that rise from the cup mouth."""

    def __init__(self, count: int, spawn_y: float, x_center: int) -> None:
        self.spawn_y = spawn_y
        self.x_center = x_center
        self.frame = 0
        self.particles: list[SteamParticle] = []
        self._max_age = 40
        for i in range(count):
            p = SteamParticle(
                x=x_center + (i % 5 - 2) * 3.0,
                y=spawn_y - (i * self._max_age / count),
                amplitude=1.5 + (i % 3) * 0.8,
                frequency=0.08 + (i % 4) * 0.02,
                speed=0.5 + (i % 3) * 0.15,
                phase=i * 1.3,
            )
            self.particles.append(p)

    def update(self) -> None:
        self.frame += 1
        for p in self.particles:
            p.y -= p.speed
            drift = math.sin(self.frame * p.frequency + p.phase) * p.amplitude
            p.x = self.x_center + drift + (p.phase % 5 - 2) * 2
            p.age += 1
            if p.age >= self._max_age or p.y < -2:
                p.x = self.x_center + (p.phase % 5 - 2) * 3.0
                p.reset(self.spawn_y, self.x_center)

    def get_draw_list(self) -> list[tuple[int, int, int]]:
        draws = []
        for p in self.particles:
            ix = int(round(p.x))
            iy = int(round(p.y))
            if 0 <= ix < 64 and 0 <= iy < 80:
                if p.age < 10:
                    ci = _STEAM_COLORS_BY_AGE[0]
                elif p.age < 25:
                    ci = _STEAM_COLORS_BY_AGE[1]
                else:
                    ci = _STEAM_COLORS_BY_AGE[2]
                draws.append((ix, iy, ci))
                if 0 <= ix - 1 < 64 and p.age < 20:
                    draws.append((ix - 1, iy, ci))
                if 0 <= ix + 1 < 64 and p.age < 15:
                    draws.append((ix + 1, iy, ci))
        return draws


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
            seed = self.frame * 31 + 17
            if (self.frame // 60) % 5 < 2:  # ~40% chance using different bits
                x = self.x_min + (seed % (self.x_max - self.x_min))
                self._drips.append(DripParticle(x=x, y=float(self.spawn_y)))

    def get_draw_list(self) -> list[tuple[int, int, int]]:
        draws = []
        for d in self._drips:
            if d.active:
                color = CHOCOLATE if d.age < 5 else WARM_BROWN
                draws.append((d.x, int(d.y), color))
        return draws
