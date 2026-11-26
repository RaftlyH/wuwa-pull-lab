"""Monte Carlo simulation. Every trial runs all the way to the copy goal."""
import numpy as np
from rules import Rules, maximum_pulls


def simulate(rules: Rules, pity=0, guaranteed=False, copies=1,
             runs=10000, seed=42):
    horizon = maximum_pulls(pity, guaranteed, copies)
    if runs < 1:
        raise ValueError('Runs must be positive.')
    rng = np.random.default_rng(seed)
    rates = rules.probabilities()
    pity_counts = np.full(runs, pity, dtype=np.int16)
    guarantees = np.full(runs, guaranteed, dtype=bool)
    obtained = np.zeros(runs, dtype=np.int8)
    # One column for each target copy; values are additional pulls needed.
    times = np.zeros((runs, copies), dtype=np.int16)

    for pull in range(1, horizon + 1):
        active = np.flatnonzero(obtained < copies)
        if not len(active):
            break
        five_star = rng.random(len(active)) < rates[pity_counts[active]]
        pity_counts[active] += 1
        hits = active[five_star]
        pity_counts[hits] = 0
        featured = guarantees[hits] | (rng.random(len(hits)) < 0.5)
        winners = hits[featured]
        times[winners, obtained[winners]] = pull
        obtained[winners] += 1
        # Every off-banner five-star sets guarantee; every featured one clears it.
        guarantees[hits] = ~featured

    if np.any(times == 0):
        raise RuntimeError('A trial exceeded the hard guarantee bound.')
    return times
