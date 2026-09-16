"""Enhanced Hyperparameter Optimization with Lévy Flight (Algorithm 1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple

import numpy as np

from lstm_eholf.config import SearchSpace


def gamma_n(z: float) -> float:
    import math

    return float(math.gamma(z))


def levy_sigma(beta: float = 1.5) -> float:
    num = gamma_n(1.0 + beta) * np.sin(np.pi * beta / 2.0)
    den = gamma_n((1.0 + beta) / 2.0) * beta * 2.0 ** ((beta - 1.0) / 2.0)
    return float((num / den) ** (1.0 / beta))


def levy_step(dim: int, beta: float = 1.5, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng()
    sigma_u = levy_sigma(beta)
    u = rng.normal(0.0, sigma_u, size=dim)
    v = rng.normal(0.0, 1.0, size=dim)
    return u / (np.abs(v) ** (1.0 / beta) + 1e-12)


def adaptive_inertia_weight(t: int, t_max: int, aw_min: float = 0.3, aw_max: float = 0.9, gamma: float = 2.0) -> float:
    return aw_min + (aw_max - aw_min) * np.exp(-gamma * t / max(t_max, 1))


def aro_energy(t: int, t_max: int, rng: np.random.Generator) -> float:
    """Original ARO energy factor (non-monotonic)."""
    r = rng.random()
    return 4.0 * (1.0 - t / max(t_max, 1)) * r


@dataclass
class EHOLFResult:
    theta_star: np.ndarray
    fitness_star: float
    history: List[float]
    n_eval: int
    decoded: Dict[str, float]
    iterations: int


class EHOLF:
    """Population search over LSTM hyperparameters.

    variant:
      - ``eholf``: Lévy exploration + AIW exploitation (proposed)
      - ``aro``: original energy-factor ARO
      - ``aro_lf``: ARO + Lévy exploration
      - ``aro_aiw``: ARO energy for switching + AIW exploitation
    """

    def __init__(
        self,
        space: Optional[SearchSpace] = None,
        population: int = 30,
        t_max: int = 100,
        beta: float = 1.5,
        aw_min: float = 0.3,
        aw_max: float = 0.9,
        aw_gamma: float = 2.0,
        seed: int = 0,
        variant: Literal["eholf", "aro", "aro_lf", "aro_aiw"] = "eholf",
        stall: int = 10,
        stall_eps: float = 1e-3,
    ) -> None:
        self.space = space or SearchSpace()
        self.n = population
        self.t_max = t_max
        self.beta = beta
        self.aw_min = aw_min
        self.aw_max = aw_max
        self.aw_gamma = aw_gamma
        self.rng = np.random.default_rng(seed)
        self.variant = variant
        self.stall = stall
        self.stall_eps = stall_eps
        self.lb = np.asarray(self.space.lower(), dtype=np.float64)
        self.ub = np.asarray(self.space.upper(), dtype=np.float64)

    def _sample(self) -> np.ndarray:
        return self.lb + self.rng.random(self.lb.shape) * (self.ub - self.lb)

    def _clip(self, x: np.ndarray) -> np.ndarray:
        return np.minimum(self.ub, np.maximum(self.lb, x))

    def optimize(self, fitness_fn: Callable[[np.ndarray], float]) -> EHOLFResult:
        dim = self.lb.size
        X = np.stack([self._sample() for _ in range(self.n)], axis=0)
        f = np.array([fitness_fn(x) for x in X], dtype=np.float64)
        best_i = int(np.argmin(f))
        theta_star = X[best_i].copy()
        f_star = float(f[best_i])
        history = [f_star]
        n_eval = self.n
        stalled = 0

        for t in range(1, self.t_max + 1):
            aw = adaptive_inertia_weight(t, self.t_max, self.aw_min, self.aw_max, self.aw_gamma)
            for i in range(self.n):
                use_explore = self._should_explore(t)
                k = int(self.rng.integers(0, self.n))
                while k == i:
                    k = int(self.rng.integers(0, self.n))
                if use_explore:
                    if self.variant in ("eholf", "aro_lf"):
                        s = levy_step(dim, self.beta, self.rng)
                        cand = X[i] + s * (X[i] - X[k]) + s * (theta_star - X[i])
                    else:
                        # Gaussian detour foraging (ARO-like)
                        cand = X[i] + self.rng.normal(0.0, 1.0, size=dim) * (X[k] - X[i])
                else:
                    a = int(self.rng.integers(0, self.n))
                    b = int(self.rng.integers(0, self.n))
                    while a == i:
                        a = int(self.rng.integers(0, self.n))
                    while b == i or b == a:
                        b = int(self.rng.integers(0, self.n))
                    if self.variant in ("eholf", "aro_aiw"):
                        cand = theta_star + aw * (X[a] - X[b]) + (1.0 - aw) * self.rng.normal(0.0, 0.1, size=dim)
                    else:
                        cand = theta_star + self.rng.normal(0.0, 1.0, size=dim) * (X[a] - X[b])
                cand = self._clip(cand)
                fc = float(fitness_fn(cand))
                n_eval += 1
                if fc < f[i]:
                    X[i] = cand
                    f[i] = fc
                if f[i] < f_star:
                    theta_star = X[i].copy()
                    f_star = float(f[i])
            history.append(f_star)
            if len(history) >= 2 and abs(history[-2] - history[-1]) < self.stall_eps:
                stalled += 1
            else:
                stalled = 0
            if stalled >= self.stall:
                return EHOLFResult(theta_star, f_star, history, n_eval, self.space.decode(theta_star), t)
        return EHOLFResult(theta_star, f_star, history, n_eval, self.space.decode(theta_star), self.t_max)

    def _should_explore(self, t: int) -> bool:
        if self.variant == "eholf":
            return bool(self.rng.random() < 0.6)
        energy = aro_energy(t, self.t_max, self.rng)
        return energy > 1.0


def exploration_efficiency(initial_acc: float, final_acc: float, iterations: int) -> float:
    return (final_acc - initial_acc) / max(iterations, 1)
