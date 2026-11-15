"""Single fresh64-pair I/G confirmation; same diagnostic loader, no tuning."""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

import run_gate as H

ROOT = H.ROOT
OUT = ROOT / 'ExternalAnalysis/AgentReports/G_I_Sunday_Confirmation'
SEEDS = list(range(93100000, 93100064))
T95 = 1.998340542520741


def config(path):
    tree = ast.parse((ROOT / path).read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'P' for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError('No literal P config: ' + path)


def effect(rows, window='all', hands=1000):
    def value(row, arm):
        chips = row[arm]['chips'] if window == 'all' else row[arm]['window_chips'].get(window, 0)
        return chips / 20 / hands * 100
    cs = [value(r, 'candidate') for r in rows]
    bs = [value(r, 'baseline') for r in rows]
    ds = [c-b for c, b in zip(cs, bs)]
    mean = statistics.mean(ds)
    se = statistics.stdev(ds) / math.sqrt(len(ds))
    return {'pairs': len(rows), 'I_bb100': statistics.mean(cs), 'G_bb100': statistics.mean(bs),
            'I_minus_G_bb100': mean, 'paired_se': se, 't95_CI_df63': [mean-T95*se, mean+T95*se],
            'positive_pairs': sum(d > 0 for d in ds), 'negative_pairs': sum(d < 0 for d in ds),
            'zero_pairs': sum(d == 0 for d in ds), 'pair_differences': ds}


def main():
    prior_dir = ROOT / 'ExternalAnalysis/AgentReports/G_I_N_Sunday_Comparison'
    prior = json.loads((prior_dir / 'preregistered_manifest.json').read_text(encoding='utf-8'))
    prior_summary = json.loads((prior_dir / 'summary.json').read_text(encoding='utf-8'))
    for path, expected in prior['hashes'].items():
        assert H.sha(path) == expected, ('prior dependency changed; controls cannot be reused', path)
    assert all(prior_summary['A_v_A'][name]['full_engine_trajectory_match'] for name in ('G', 'I'))
    assert prior_summary['comparisons']['I']['all_seat_errors'] == {'candidate': 0, 'baseline': 0}
    older = {'I': 'tools/cands/srv_I.py', 'G': 'tools/cands/g_matched_srv_i.py'}
    old_expected = {'I': '117adab218b509302b805f5cdf2066054ea60cb1de382082a4ab37fc7ce99b89',
                    'G': '7e7f7c7e68b1af3e27b835dae211190b13d4d84d52f12094b055fe1bfb6fdb4d'}
    deltas = {}
    for name, path in older.items():
        assert H.sha(path) == old_expected[name]
        old, frozen = config(path), config(H.MODELS[name])
        deltas[name] = {k: {'older_matched': old.get(k), 'current_frozen': frozen.get(k)}
                        for k in sorted(set(old) | set(frozen)) if old.get(k) != frozen.get(k)}
        assert set(deltas[name]) <= {'max_ms', 'hard_ms', 'bank', 'max_sims'}
    deps = dict(prior['hashes'])
    for path in list(older.values()) + ['tools/independent_g_in/run_confirmation.py', 'ExternalAnalysis/I_vs_G_Matched_Budget_20261114.md']:
        deps[path] = H.sha(path)
    OUT.mkdir(parents=True, exist_ok=True)
    mp = OUT / 'preregistered_manifest.json'
    assert not mp.exists(), 'Refuse repeat of preregistered confirmation'
    manifest = {'registered_utc': datetime.now(timezone.utc).isoformat(),
                'purpose': 'One independently held-out confirmation of I vs G, selected using earlier evidence; no repeated retry until pass',
                'seeds': SEEDS, 'pairs': 64, 'hands_per_arm': 1000, 'total_table_hands': 128000,
                'hero_seat': 'pair_index modulo8, eight complete seat rotations',
                'candidate': H.MODELS['I'], 'baseline': H.MODELS['G'],
                'work_and_field': 'Unchanged run_gate.py loader: fixed32MC/budget.001/per-decision seeding; seven sunday_v2 clones once, seeded shuffle within each pair',
                'A_v_A': 'No new QA compute; reused exact-byte-checked prior G/I engine-trajectory controls, evidence paths under G_I_N_Sunday_Comparison',
                'primary': 'Unweighted whole-table I-minus-G paired mean; sample SE; single t95CI df63',
                'decision': 'Lower primary bound>0 and zero observed errors supports clone-field strategy improvement only; otherwise no demonstrated improvement and stop. No further retry, tuning or promotion from this alone.',
                'secondary': 'Hand windows1-50,51-200,201-1000 and action counts descriptive; cannot replace primary',
                'older_report_artifact_differences': deltas,
                'older_report_limits': 'Older seven positive blocks used changed runtime/bank copies and clock-stopped MC, real/late/heldout/archive fields and unseeded own MC; they are not the same exact artifact/settings or this frozen deterministic Sunday confirmation. Do not pool effects.',
                'hashes': deps}
    with mp.open('x', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write('\n')
    print('PREREGISTERED', hashlib.sha256(mp.read_bytes()).hexdigest(), 'older config deltas', deltas, flush=True)
    raw = OUT / 'I_vs_G_pairs.jsonl'
    rows = []
    with raw.open('x', encoding='utf-8') as f:
        for index, seed in enumerate(SEEDS):
            _, candidate = H.play(H.MODELS['I'], seed, index % 8, 1000)
            _, baseline = H.play(H.MODELS['G'], seed, index % 8, 1000)
            row = {'pair_index': index, 'seed': seed, 'hero_seat': index % 8,
                   'candidate': candidate, 'baseline': baseline}
            rows.append(row)
            f.write(json.dumps(row, sort_keys=True)+'\n')
            f.flush()
            if (index+1) % 8 == 0:
                print('completed', index+1, 'of64pairs', flush=True)
    errors = {arm: sum(row[arm]['all_seat_errors'] for row in rows) for arm in ('candidate', 'baseline')}
    counts = {}
    for arm in ('candidate', 'baseline'):
        count = Counter()
        for row in rows:
            count.update(row[arm]['actions'])
        counts[arm] = dict(sorted(count.items()))
    primary = effect(rows)
    summary = {'completed_utc': datetime.now(timezone.utc).isoformat(),
               'primary': primary, 'all_seat_errors': errors,
               'clone_field_acceptance_passed': primary['t95_CI_df63'][0] > 0 and sum(errors.values()) == 0,
               'secondary_windows': {w: effect(rows, w, n) for w, n in [('1-50',50), ('51-200',150), ('201-1000',800)]},
               'action_counts': counts, 'raw_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
               'manifest_sha256': hashlib.sha256(mp.read_bytes()).hexdigest(), 'total_table_hands': 128000,
               'new_QA_hands': 0}
    H.write(OUT / 'summary.json', summary)
    text = '# Frozen I versus G: one held-out Sunday confirmation\n\n'
    text += ('A single independently held-out64-pair confirmation was chosen after the earlier exploratory I/G evidence. '
             'No tuning, retries, seed filtering or extra follow-up is part of this run. '
             'All128000table-hands were collected once on fresh seeds93100000-93100063. '
             'All8hero seats appear8times. Same frozen I/G source bytes,32MC diagnostic work, per-decision RNG seeding and sunday_v2 clone field '
             'as the preceding16-pair screen. Prior A-v-A controls were reused only after checking all recorded dependency hashes; no extra QA hands.\n\n'
             'The older seven positive blocks in I_vs_G_Matched_Budget_20261114.md used srv_I and g_matched_srv_i copies with changed runtime/bank settings '
             'and clock-stopped Monte Carlo on real/late/heldout/archive fields. Their hashes differ from the current frozen exports; '
             'effective P differences are recorded in this run manifest. Their effects are not pooled into this fresh primary estimate.\n\n'
             'Primary endpoint is the unweighted whole-table paired I-minus-G effect with one95% t(df63) interval. '
             'This is one fixed held-out comparison, selected before examining its seeds; ordinary95% coverage does not validate unlimited sequential searches. '
             'Early windows/action counts remain descriptive. The required positive lower bound with zero errors provides strategy evidence only in this clone field. '
             'It does not establish real-opponent performance or production-runtime viability; no source deployment is authorized.\n\n')
    verdict = ('The preregistered clone-field strategy criterion passed. Independently validate production caps, bank, exceptions/fallbacks and actual platform limits before any release.'
               if summary['clone_field_acceptance_passed'] else
               'The preregistered criterion did not pass. No demonstrated improvement in this confirmation; retain the G reference and stop this sequence. This does not establish intrinsic inferiority of I.')
    text += '**Readout:** ' + verdict + '\n\n'
    text += 'Run once: `python tools/independent_g_in/run_confirmation.py` from PokerBot. Evidence: `ExternalAnalysis/AgentReports/G_I_Sunday_Confirmation/`.\n\n'
    text += '```json\n' + json.dumps(summary, indent=2, sort_keys=True) + '\n```\n'
    (ROOT / 'ExternalAnalysis/G_I_Sunday_Confirmation.md').write_text(text, encoding='utf-8')
    print('DONE', json.dumps(primary), 'errors', errors, 'acceptance', summary['clone_field_acceptance_passed'], flush=True)


if __name__ == '__main__':
    main()
