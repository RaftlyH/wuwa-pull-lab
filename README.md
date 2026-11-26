# WuWa Pull Lab

A Python + Streamlit + Plotly learning project for featured Resonator pulls.

## Start on Windows

Install Python 3.10 or later first. Extract this ZIP, then open a terminal **inside the folder containing app.py**. In VS Code, open that folder and choose Terminal > New Terminal.

Run these commands one at a time (do not type the code-block labels):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address localhost
```

The first command creates an environment folder. The second installs the dependencies into it. The third launches the dashboard in your browser, normally at http://localhost:8501. No account or API key is needed. Installation requires internet; calculations run locally. Stop the app with Ctrl+C in its terminal. To launch it again, use only the third command. You do not need to activate the environment or change PowerShell execution policies.

If Windows cannot find `python`, try `py` for the first command. Check that the terminal is in the extracted project folder if it cannot find requirements.txt or app.py. Do not name your files streamlit.py, numpy.py, or plotly.py.

macOS/Linux equivalents:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address localhost
```

## Using the dashboard

1. Set available pulls and pity (pulls SINCE your last five-star, 0–79).
2. Check the guarantee box only if your next five-star is guaranteed featured.
3. Select **additional copies**, not Resonance Chain level. One copy means obtaining the character once.
4. Choose the trial count and press Run analysis. Settings take effect on submission.
5. Explore probability curves, budget thresholds, complete-trial histograms, and copy counts. Hover/zoom with Plotly. Export trial results, curves and settings from Trials and exports.

The fixed random seed reproduces a simulation; change it to obtain another sample. A pull budget of zero has zero success probability. Large goals and trial counts take longer.

## Probability assumptions — read before interpreting the numbers

This is an educational model, **not a verified calculator of exact in-game odds**.

The featured Resonator rules used are a 0.8% base five-star rate, a five-star at latest on pull 80, a 50/50 when not guaranteed, and a featured guarantee after an off-banner five-star. A five-star resets pity. Featured acquisition clears guarantee. A goal of n additional copies needs at most `160*n - starting_pity - (80 if guaranteed else 0)` additional pulls.

Sources to check against current in-game details:
- Kuro Games, Convene Details: https://wutheringwaves.kurogames.com/en/main/news/detail/758
- Official Korean rules (same banner family): https://wutheringwaves.kurogames.com/kr/main/news/detail/763

The published aggregate five-star rate (1.8% including guarantees) is **not** the probability to apply independently on every pull. The per-pull soft-pity curve has not been verified for this project.

Two selectable models:
- **Default simplified model:** 0.8% on pulls 1–79; 100% on pull 80. This intentionally omits soft pity and does not reproduce the published aggregate rate.
- **Illustrative soft pity:** editable linear increase starting on the selected pull; rates are capped at 100%, with pull 80 always guaranteed. Defaults of pull 66 and +6 percentage points per pull are illustrative assumptions, not official rules or a fitted estimate. On pull 66 the default illustrative chance is 6.8%, on 67 it is 12.8%, etc.

For an accurately calibrated game calculator, replace the rates in `wuwa_pull_lab/rules.py` with a sourced or carefully fitted probability table, document the data and uncertainty, and rerun the validation. Public banner rules supply configuration data; trial CSVs are generated simulations, not real player histories.

## How the calculations work

- `wuwa_pull_lab/simulator.py` uses NumPy random draws. Each trial continues until the entire goal is reached, even beyond the user's budget. This avoids averaging only lucky, successful-within-budget trials.
- `wuwa_pull_lab/analysis.py` propagates state probabilities over pity, guarantee and copy count. Completed goals become absorbing outcomes. The cumulative probability of completion is computed without sampling error.
- “Exact model” means exact for these assumptions (up to floating-point rounding), **not exact game odds**.
- Success probability means completing the entire selected goal within the available pulls.
- Mean pulls is the unconditional mean to complete the goal, not the average among only trials within the budget.
- The Wilson interval quantifies Monte Carlo sampling uncertainty only. It cannot validate assumed game rules.
- The copy chart is capped at the target; trials stop there, so its final bar includes outcomes that could produce more copies if pulling continued.
- The opposite-guarantee curve changes only the initial guarantee flag; other inputs stay fixed. Its displayed range follows the selected scenario's guarantee bound.
- Four-star outcomes, weapons, store purchases and coral refunds are excluded. They are not needed to model the selected five-star goal under these assumptions.

## Files and learning order

| File | Purpose |
|---|---|
| wuwa_pull_lab/rules.py | Probability table and input validation; start reading here |
| wuwa_pull_lab/simulator.py | Vectorized random pulls and pity/guarantee transitions |
| wuwa_pull_lab/analysis.py | Independent exact probability calculation |
| app.py | Inputs, charts, summaries, CSV/JSON exports |
| requirements.txt | Packages to install |
| tests/test_probability.py | Boundary cases and independent simulation checks |

The `wuwa_pull_lab/` package holds the calculation code, while `app.py` stays at the project root as the dashboard entry point. Local environments and generated Python caches are excluded from Git by `.gitignore`.

## Validate

From the project folder:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover first-pull probabilities, hard pity, guarantees, multiple copies, cumulative probabilities, reproducibility, invalid pity, and Monte Carlo agreement with exact calculations.

Documentation: https://docs.streamlit.io/ and https://plotly.com/python/
