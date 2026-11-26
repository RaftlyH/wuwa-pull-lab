"""Check the browser calculator against the independent Python implementation."""
import json
from pathlib import Path
import subprocess
import unittest

import numpy as np

from wuwa_pull_lab.analysis import exact_cdf
from wuwa_pull_lab.rules import Rules


ROOT = Path(__file__).resolve().parents[1]


class BrowserEngineTests(unittest.TestCase):
    def test_browser_matches_python_and_simulates(self):
        scenarios = [
            dict(budget=100, pity=pity, guaranteed=guaranteed, copies=copies,
                 runs=10000, seed=42, soft=soft, softStart=66, step=6)
            for pity, guaranteed, copies, soft in [
                (0, False, 1, False), (79, True, 1, False),
                (35, False, 2, True), (79, False, 7, True),
                (0, True, 7, False),
            ]
        ]
        script = """
const assert = require('node:assert/strict');
const engine = require('./docs/engine.js');
const scenarios = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
const results = scenarios.map(s => {
  const r = engine.analyze(s);
  assert.equal(r.exact.length, engine.maximumPulls(s) + 1);
  assert.equal(r.copiesCounts.reduce((a,b)=>a+b,0), s.runs);
  assert.equal(r.empirical[r.horizon], 1);
  for(let i=1;i<r.exact.length;i++) assert(r.exact[i]>=r.exact[i-1]-1e-12);
  for(let i=0;i<r.times.length;i++) {
    assert(r.times[i]>0 && r.times[i]<=r.horizon);
    if(i%s.copies) assert(r.times[i]>r.times[i-1]);
  }
  for(let i=0;i<=r.horizon;i++) assert(Math.abs(r.empirical[i]-r.exact[i])<.035);
  assert.deepEqual(engine.simulate(s), r.times);
  return Array.from(r.exact);
});
const base = scenarios[0];
assert.equal(engine.exactCDF({...base, pity:79, guaranteed:true})[1], 1);
assert.equal(engine.exactCDF({...base, pity:79})[1], .5);
assert.equal(engine.analyze({...base,budget:0}).successes, 0);
assert.equal(engine.analyze({...base,budget:1120}).successes, base.runs);
assert.throws(()=>engine.analyze({...base,pity:80}));
assert.throws(()=>engine.analyze({...base,copies:0}));
assert.throws(()=>engine.analyze({...base,step:NaN}));
assert.equal(engine.probabilities({...base,soft:true})[65], .068);
process.stdout.write(JSON.stringify(results));
"""
        completed = subprocess.run(
            ['node', '-e', script], input=json.dumps(scenarios),
            text=True, capture_output=True, cwd=ROOT, check=True,
        )
        for settings, actual in zip(scenarios, json.loads(completed.stdout)):
            with self.subTest(settings=settings):
                expected = exact_cdf(
                    Rules(settings['soft'], settings['softStart'], settings['step'] / 100),
                    settings['pity'], settings['guaranteed'], settings['copies'],
                )
                np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=1e-12)
