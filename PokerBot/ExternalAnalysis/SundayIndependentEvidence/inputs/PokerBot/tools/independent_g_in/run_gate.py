"""One frozen I/N versus G matched-work screen; no policy tuning or release."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import sunday_early_adapt_pilot as H

MODELS = {
    'G': 'submissions/G_v7_final/bot.py',
    'I': 'submissions/I_v9_25ms/bot.py',
    'N': 'submissions/N_v10_tuned/bot.py',
}
EXPECTED = {
    'G': 'b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a',
    'I': 'd45a39b72c0e990efe06c8a233c7f2061f468a5c1f3279924c5ae07fc060f46c',
    'N': '5c2b4b2c0ed3ddd5177fe758959e1c32e3a113f8c500a373f6b5d11d5bb7845f',
}
OPPS = ['tools/independent_ctx_pr11/opponents/sunday_v2/r_' + n + '.py' for n in H.NAMES]
OUT = ROOT / 'ExternalAnalysis/AgentReports/G_I_N_Sunday_Comparison'
SEEDS = {'I': list(range(91100000, 91100016)), 'N': list(range(91200000, 91200016))}
HANDS = 1000
T95 = 2.131449545559323
T975 = 2.489879703472758  # t(.9875,15): Bonferroni two-comparison 95% family coverage


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def agent(path, seed):
    src = (ROOT / path).read_text(encoding='utf-8')
    stop = 'if sims >= P["max_sims"] or now > hard or (now > t_end and sims >= 8):'
    assert src.count(stop) == 1
    assert src.count('DEBUG = False') == 1
    src = src.replace(stop, 'if sims >= 32:').replace('DEBUG = False', 'DEBUG = True')
    module = types.ModuleType('fixed_work_' + path.replace('/', '_'))
    module.__file__ = str(ROOT / path)
    exec(compile(src, module.__file__, 'exec'), module.__dict__)

    class Fixed(module.Agent):
        def __init__(self):
            super().__init__()
            self.window_chips = Counter()
            self.actions = Counter()

        def budget(self):
            return .001

        def act(self, state):
            self.rng.seed(H.decision_seed(seed, state))
            result = super().act(state)
            self.actions[H.window(state['hand_number']) + '|' + state['street'] + '|' + result['action']] += 1
            return result

        def on_hand_end(self, summary):
            super().on_hand_end(summary)
            self.window_chips[H.window(summary['hand_number'])] += summary['stacks'][self.seat] - self.start

    return Fixed


def play(path, seed, hero, hands, record=False):
    order = OPPS.copy()
    random.Random(seed).shuffle(order)
    classes = [H.clone_class(p, seed) for p in order]
    classes.insert(hero, agent(path, seed))
    players = [H.arena.LocalPlayer(cls) for cls in classes]
    try:
        result = H.arena.FixedHandsTable(players, hands=hands, config={'betting': 'no_limit', 'raise_cap': 0}, seed=seed, record=record).play()
        bot = players[hero].agent
        stats = {'chips': result['chips'][hero], 'window_chips': dict(bot.window_chips),
                 'actions': dict(bot.actions), 'all_seat_errors': sum(p.stats.errors for p in players),
                 'player_stats': [p.stats.as_dict() for p in players]}
        return result, stats
    finally:
        for player in players:
            player.close()


def effect(rows, window='all', hands=1000):
    def value(row, arm):
        chips = row[arm]['chips'] if window == 'all' else row[arm]['window_chips'].get(window, 0)
        return chips / 20 / hands * 100
    candidates = [value(row, 'candidate') for row in rows]
    baselines = [value(row, 'baseline') for row in rows]
    diffs = [c - b for c, b in zip(candidates, baselines)]
    mean = statistics.mean(diffs)
    se = statistics.stdev(diffs) / math.sqrt(len(diffs))
    return {'n_pairs': len(diffs), 'candidate_bb100': statistics.mean(candidates),
            'G_bb100': statistics.mean(baselines), 'difference_bb100': mean, 'paired_se': se,
            'ordinary_t95_CI': [mean - T95 * se, mean + T95 * se],
            'two_comparison_bonferroni_t975_CI': [mean - T975 * se, mean + T975 * se],
            'positive_pairs': sum(d > 0 for d in diffs), 'negative_pairs': sum(d < 0 for d in diffs),
            'pair_differences': diffs}


def main():
    for name, path in MODELS.items():
        assert sha(path) == EXPECTED[name], ('frozen model changed', name)
    deps = list(MODELS.values()) + OPPS + [
        'tools/independent_ctx_pr11/opponents/_common.py',
        'tools/independent_ctx_pr11/opponents/sunday_v2/MANIFEST.json',
        'tools/sunday_early_adapt_pilot.py', 'tools/arena.py', 'tools/independent_g_in/run_gate.py',
    ] + [p.relative_to(ROOT).as_posix() for p in (ROOT / 'kit/engine').glob('*.py')]
    OUT.mkdir(parents=True, exist_ok=True)
    mp = OUT / 'preregistered_manifest.json'
    assert not mp.exists(), 'Already preregistered: refuse repeat/overwrite'
    manifest = {
        'created_utc': datetime.now(timezone.utc).isoformat(), 'models': MODELS, 'seeds': SEEDS,
        'comparisons': ['I minus G', 'N minus G'], 'hands_per_arm_table': HANDS,
        'profit_pairs_per_comparison': 16, 'profit_total_table_hands': 64000,
        'A_v_A': 'Each of G/I/N twice at20hands before profit;120additional QA table-hands',
        'hero_seat': 'pair index modulo8: every seat twice in each comparison',
        'field': 'Same seven sunday_v2 clones once per table, same seeded shuffle within pair',
        'work': 'Fixed32MC samples; budget=.001 and RNG per-decision seed for all seats; DEBUG=True in RAM only',
        'frozen_bytes_untouched': True, 'no_parameter_tuning_or_retries': True,
        'primary': 'Unweighted paired mean table bb/100, sample SE and t(df15) intervals',
        'multiplicity': 'Two ordinary95 intervals descriptive; Bonferroni97.5 marginal intervals provide nominal95 family coverage for two fixed comparisons',
        'selection': 'No release from screen. Positive unadjusted95CI alone does not establish selected improvement; require independent confirmation and production runtime.',
        'limits': 'Profile clones approximate action frequencies, not actual policies. Low fixed MC changes production compute behavior. Shared cards cease identical action histories after strategy differences.',
        'hashes': {p: sha(p) for p in deps},
    }
    with mp.open('x', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write('\n')
    print('PREREGISTERED', hashlib.sha256(mp.read_bytes()).hexdigest(), flush=True)
    qa = {}
    for index, (name, path) in enumerate(MODELS.items()):
        seed = 91099900 + index
        a, sa = play(path, seed, index, 20, True)
        b, sb = play(path, seed, index, 20, True)
        # Wall-clock measurements are expected to differ; compare complete engine trajectory and policy data.
        aa = {k: v for k, v in sa.items() if k != 'player_stats'}
        bb = {k: v for k, v in sb.items() if k != 'player_stats'}
        assert a == b and aa == bb and sa['all_seat_errors'] == 0, ('A-v-A failed', name)
        write(OUT / ('A_v_A_' + name + '.json'), {'seed': seed, 'result_a': a, 'result_b': b, 'stats_a': sa, 'stats_b': sb})
        qa[name] = {'full_engine_trajectory_match': True, 'policy_summary_match': True,
                    'trajectory_sha256': hashlib.sha256(json.dumps(a, sort_keys=True).encode()).hexdigest()}
    write(OUT / 'A_v_A_summary.json', qa)
    print('A-v-A PASS G/I/N before profit', flush=True)
    summaries = {}
    for name, seeds in SEEDS.items():
        rows = []
        raw = OUT / (name + '_vs_G_pairs.jsonl')
        with raw.open('x', encoding='utf-8') as f:
            for index, seed in enumerate(seeds):
                hero = index % 8
                _, candidate = play(MODELS[name], seed, hero, HANDS)
                _, baseline = play(MODELS['G'], seed, hero, HANDS)
                order = OPPS.copy()
                random.Random(seed).shuffle(order)
                row = {'comparison': name + ' minus G', 'pair_index': index, 'seed': seed,
                       'hero_seat': hero, 'opponent_order': order, 'candidate': candidate, 'baseline': baseline}
                rows.append(row)
                f.write(json.dumps(row, sort_keys=True) + '\n')
                f.flush()
                print(name, 'pair', index + 1, 'of16', flush=True)
        action_counts = {}
        for arm in ('candidate', 'baseline'):
            count = Counter()
            for row in rows:
                count.update(row[arm]['actions'])
            action_counts[arm] = dict(sorted(count.items()))
        summaries[name] = {'primary': effect(rows),
                           'windows': {w: effect(rows, w, n) for w, n in [('1-50', 50), ('51-200', 150), ('201-1000', 800)]},
                           'all_seat_errors': {arm: sum(row[arm]['all_seat_errors'] for row in rows) for arm in ('candidate', 'baseline')},
                           'action_counts': action_counts, 'raw_sha256': hashlib.sha256(raw.read_bytes()).hexdigest()}
        write(OUT / (name + '_summary.json'), summaries[name])
    summary = {'completed_utc': datetime.now(timezone.utc).isoformat(),
               'manifest_sha256': hashlib.sha256(mp.read_bytes()).hexdigest(),
               'total_table_hands': 64120, 'A_v_A': qa, 'comparisons': summaries}
    write(OUT / 'summary.json', summary)
    text = '# Frozen G/I/N Sunday clone comparison\n\n'
    text += ('One preregistered diagnostic screen. Frozen I and N are each compared to frozen G on16fresh '
             'paired1000-hand tables, hero seats0-7 twice, same seven sunday_v2 clones and seeded shuffle '
             'within each pair.64000profit table-hands plus120A-v-A QA table-hands.\n\n'
             'All three models passed full engine-trajectory/policy-summary A-v-A equality before profit. '
             'Fixed32MC work and per-decision RNG seeding are identical for baseline and challenger. '
             'Original source files were not modified. Production clock/bank stopping is overridden '
             'in RAM only; this is a strategy diagnostic, not exported-artifact runtime certification. '
             'The field reproduces public frequencies imperfectly, not actual opponent strategy/strength.\n\n'
             'Primary endpoints are whole-table paired effects. Ordinary95% t intervals are descriptive; '
             'Bonferroni97.5% marginal intervals account for the two fixed comparisons at nominal95% family coverage. '
             'Window/action analyses are secondary, not alternative selection endpoints. No tuning, retries or '
             'favorable-seed filtering occurred. No release is authorized by this screen.\n\n'
             'Run once: `python tools/independent_g_in/run_gate.py` from PokerBot. '
             'Evidence: `ExternalAnalysis/AgentReports/G_I_N_Sunday_Comparison/` contains pre-run '
             'manifest, full20-hand A-v-A traces, per-pair chips/windows/actions/errors, summary and hashes.\n\n')
    text += '```json\n' + json.dumps(summary, indent=2, sort_keys=True) + '\n```\n'
    (ROOT / 'ExternalAnalysis/G_I_N_Sunday_Comparison.md').write_text(text, encoding='utf-8')
    print('DONE', json.dumps({k: v['primary'] for k, v in summaries.items()}), flush=True)


if __name__ == '__main__':
    main()
