"""Run from this folder: python -m streamlit run app.py"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from rules import Rules, maximum_pulls
from simulator import simulate
from analysis import exact_cdf, empirical_cdf, threshold

st.set_page_config(page_title='WuWa Pull Lab', page_icon='🌊', layout='wide')
st.title('WuWa Pull Lab')
st.caption('Featured Resonator banner · simulation and probability analysis')
st.info('Model estimates, not exact in-game odds. Default: 0.8% base rate + 80-pull hard pity, '
        '50/50 and featured guarantee. The actual per-pull soft-pity curve is not verified here. '
        'Optional soft pity is an illustrative assumption.')

with st.sidebar:
    st.header('Your starting point')
    with st.form('analysis_form'):
        budget = st.number_input('Available pulls', 0, 1120, 100)
        pity = st.slider('Pulls since your last five-star', 0, 79, 0)
        guaranteed = st.checkbox('Next five-star is guaranteed featured')
        copies = st.slider('Additional featured copies wanted', 1, 7, 1)
        runs = st.selectbox('Simulation trials', [1000, 10000, 50000], index=1)
        seed = st.number_input('Random seed', 0, 2147483647, 42)
        st.caption('Same inputs and seed reproduce the same simulation.')
        soft = st.checkbox('Use an illustrative soft-pity curve')
        soft_start = st.slider('Assumed soft-pity starting pull', 2, 79, 66)
        step = st.slider('Assumed increase per pull (percentage points)', 0.0, 20.0, 6.0, 0.5)
        submitted = st.form_submit_button('Run analysis', type='primary')

@st.cache_data(show_spinner=False)
def calculate(pity, guaranteed, copies, runs, seed, soft, soft_start, step):
    rules = Rules(soft, soft_start, step / 100)
    times = simulate(rules, pity, guaranteed, copies, runs, seed)
    exact = exact_cdf(rules, pity, guaranteed, copies)
    alternative = exact_cdf(rules, pity, not guaranteed, copies)
    return times, exact, alternative, rules.probabilities()

if submitted or 'settings' not in st.session_state:
    st.session_state.settings = (int(budget), pity, guaranteed, copies, runs, int(seed), soft, soft_start, step)

budget, pity, guaranteed, copies, runs, seed, soft, soft_start, step = st.session_state.settings
with st.spinner('Simulating pulls and calculating exact model probabilities…'):
    times, exact, alternative, rates = calculate(pity, guaranteed, copies, runs, seed, soft, soft_start, step)
horizon = len(exact) - 1
completion = times[:, -1]
simulated = empirical_cdf(completion, horizon)
b = min(budget, horizon)
successes = int(np.sum(completion <= budget))
# Wilson interval behaves sensibly even when all trials succeed or fail.
p = successes / runs
z = 1.96
denominator = 1 + z*z/runs
center = (p + z*z/(2*runs)) / denominator
margin = z*np.sqrt(p*(1-p)/runs + z*z/(4*runs*runs)) / denominator
exact_mean = float(np.sum(1 - exact[:-1]))

st.subheader(f'{budget} pulls · {pity} pity · {copies} additional copy/copies')
st.caption(f"{'Guaranteed' if guaranteed else '50/50'} starting state · {runs:,} trials · "
           f"{'Illustrative soft pity' if soft else 'Simplified base rate + hard pity'} · "
           'Press Run analysis to apply changed sidebar settings.')
a, bcol, c, d = st.columns(4)
a.metric('Success • exact model', f'{exact[b]:.2%}')
bcol.metric('Success • simulation', f'{p:.2%}')
c.metric('Mean pulls to goal • exact model', f'{exact_mean:.1f}')
d.metric('Hard guarantee from your state', f'{horizon} pulls')
st.caption(f'Simulation 95% Wilson interval: {max(0, center-margin):.2%}–{min(1, center+margin):.2%}. '
           'This measures sampling uncertainty, not uncertainty in the assumed game rules. '
           'Mean pulls uses complete trials, including those exceeding your budget.')

chart_tab, outcomes_tab, rules_tab = st.tabs(['Probability dashboard', 'Trials and exports', 'Pity model and sources'])
with chart_tab:
    x = np.arange(horizon + 1)
    fig = go.Figure()
    fig.add_scatter(x=x, y=exact, name='Exact model', mode='lines')
    fig.add_scatter(x=x, y=simulated, name='Simulation', mode='lines', line=dict(dash='dot'))
    fig.add_scatter(x=x, y=alternative[np.minimum(x, len(alternative)-1)],
                    name='Opposite starting guarantee', mode='lines', line=dict(dash='dash'))
    fig.add_vline(x=budget, line_dash='dash', annotation_text='Your budget')
    fig.update_layout(title='Chance of reaching your copy goal', xaxis_title='Additional pulls',
                      yaxis_title='Success probability', yaxis_tickformat='.0%', yaxis_range=[0, 1.01])
    st.plotly_chart(fig, width='stretch')
    thresholds = pd.DataFrame({'Success probability': ['50%', '90%', '95%', '99%'],
                               'Additional pulls (exact model)': [threshold(exact, q) for q in [.5, .9, .95, .99]]})
    st.dataframe(thresholds, hide_index=True, width='stretch')
    left, right = st.columns(2)
    with left:
        hist = px.histogram(pd.DataFrame({'Additional pulls': completion}), x='Additional pulls', nbins=50,
                            title='Pulls needed to reach the goal • all trials')
        hist.add_vline(x=budget, line_dash='dash')
        st.plotly_chart(hist, width='stretch')
    with right:
        achieved = np.sum(times <= budget, axis=1)
        counts = np.bincount(achieved, minlength=copies + 1)
        dist = pd.DataFrame({'Featured copies': np.arange(copies + 1), 'Probability': counts / runs})
        fig2 = px.bar(dist, x='Featured copies', y='Probability', title='Copies obtained within your budget')
        fig2.update_yaxes(tickformat='.0%')
        st.plotly_chart(fig2, width='stretch')
        st.caption('Capped at your selected copy goal; that bar includes trials that could obtain more.')
with outcomes_tab:
    curves = pd.DataFrame({'additional_pulls': np.arange(horizon + 1), 'exact_model_probability': exact,
                           'simulated_probability': simulated})
    trials = pd.DataFrame(times, columns=[f'pull_for_copy_{i+1}' for i in range(copies)])
    trials.insert(0, 'trial', np.arange(1, runs + 1))
    trials['goal_reached_within_budget'] = completion <= budget
    trials['copies_within_budget_capped_at_goal'] = np.sum(times <= budget, axis=1)
    st.dataframe(trials.head(100), hide_index=True)
    st.download_button('Download all trials (CSV)', trials.to_csv(index=False), 'wuwa_trials.csv', 'text/csv')
    st.download_button('Download probability curve (CSV)', curves.to_csv(index=False), 'wuwa_curve.csv', 'text/csv')
    st.download_button('Download settings (JSON)', pd.Series(dict(budget=budget, pity=pity, guaranteed=guaranteed,
                       copies=copies, runs=runs, seed=seed, illustrative_soft_pity=soft,
                       soft_start=soft_start, step_percentage_points=step)).to_json(indent=2),
                       'wuwa_settings.json', 'application/json')
with rules_tab:
    st.write('A five-star resets pity. Losing the 50/50 guarantees the next five-star is featured; '
             'obtaining the featured Resonator clears that guarantee. Copies here mean additional copies, '
             'not Resonance Chain level. Trials stop at your selected goal.')
    st.warning('Neither model is a verified reproduction of the game. The simplified model omits soft pity. '
               'The optional model adds an editable linear increase; its defaults (pull 66, +6 percentage points) '
               'are illustrative, not an official or fitted formula. The published 1.8% aggregate rate '
               'does not by itself identify a unique per-pull curve.')
    st.write('“Exact” means exact for the selected mathematical model. It does not mean exact game odds. '
             'The calculation propagates probability through states of pity, guarantee, and copies obtained; '
             'the simulation independently samples random pulls.')
    st.markdown('[Kuro Games: Convene Details](https://wutheringwaves.kurogames.com/en/main/news/detail/758) · '
                '[Official Korean rules](https://wutheringwaves.kurogames.com/kr/main/news/detail/763)')
    st.caption('Check current in-game banner details before applying these assumptions to a banner. '
               'Four-star outcomes, weapon banners, coral refunds and store purchases are outside this model.')
    fig3 = px.line(x=np.arange(1, 81), y=rates,
                   labels={'x': 'Pull since last five-star', 'y': 'Assumed five-star probability'})
    fig3.update_yaxes(tickformat='.0%')
    st.plotly_chart(fig3, width='stretch')
