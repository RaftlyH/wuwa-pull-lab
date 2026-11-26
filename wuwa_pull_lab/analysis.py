"""Exact state probabilities, independent of the Monte Carlo implementation."""
import numpy as np
from .rules import Rules, maximum_pulls


def exact_cdf(rules: Rules, pity=0, guaranteed=False, copies=1):
    horizon = maximum_pulls(pity, guaranteed, copies)
    rates = rules.probabilities()
    # state[copies obtained, guarantee flag, pulls since last five-star]
    state = np.zeros((copies, 2, 80))
    state[0, int(guaranteed), pity] = 1.0
    cdf = np.zeros(horizon + 1)
    completed = 0.0
    for pull in range(1, horizon + 1):
        nxt = np.zeros_like(state)
        # No five-star: pity increases by one, everything else stays the same.
        nxt[:, :, 1:] = (state * (1 - rates))[:, :, :-1]
        hits = (state * rates).sum(axis=2)
        # Unguaranteed five-stars split evenly; guaranteed five-stars all win.
        wins = hits[:, 0] * 0.5 + hits[:, 1]
        nxt[:, 1, 0] += hits[:, 0] * 0.5
        nxt[1:, 0, 0] += wins[:-1]
        completed += wins[-1]
        cdf[pull] = completed
        state = nxt
    return np.clip(cdf, 0, 1)


def empirical_cdf(completion_times, horizon):
    return np.cumsum(np.bincount(completion_times, minlength=horizon + 1)) / len(completion_times)


def threshold(cdf, probability):
    found = np.flatnonzero(cdf >= probability - 1e-12)
    return int(found[0]) if len(found) else None
