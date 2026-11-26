"""Probability assumptions, separated from simulation code for easy editing."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Rules:
    # These defaults are a simplified base-rate + hard-pity model.
    # They do NOT reproduce the game's undisclosed per-pull soft-pity curve.
    soft_pity: bool = False
    soft_start: int = 66
    soft_step: float = 0.06

    def probabilities(self):
        """Index 0 means the first pull after a five-star; index 79 is hard pity."""
        pulls = np.arange(1, 81)
        rates = np.full(80, 0.008)
        if self.soft_pity:
            # An editable, illustrative assumption, NOT a verified WuWa formula.
            rates += np.maximum(0, pulls - self.soft_start + 1) * self.soft_step
        rates = np.clip(rates, 0, 1)
        rates[-1] = 1.0
        return rates


def validate(pity, copies):
    if not 0 <= pity <= 79:
        raise ValueError('Starting pity must be between 0 and 79.')
    if not 1 <= copies <= 7:
        raise ValueError('Target additional copies must be between 1 and 7.')


def maximum_pulls(pity, guaranteed, copies):
    validate(pity, copies)
    return 160 * copies - pity - (80 if guaranteed else 0)
