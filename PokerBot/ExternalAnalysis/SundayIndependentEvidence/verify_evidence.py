"""Audit published hashes/statistics only. Does not import bots or run matches."""
import hashlib
import json
import math
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    bundle = json.loads((HERE/'dependency_manifest.json').read_text(encoding='utf-8'))
    for path, expected in bundle['source_path_sha256'].items():
        assert sha(HERE/'inputs/PokerBot'/path) == expected, ('input hash', path)
    for audit in bundle['raw_result_audits']:
        directory = HERE/'results'/audit['run']
        summary = json.loads((directory/'summary.json').read_text())
        manifest = directory/'preregistered_manifest.json'
        assert sha(manifest) == summary['manifest_sha256']
        if audit['run'] == 'G_I_N_Sunday_Comparison':
            name = audit['comparison'][0]
            path = directory/(name+'_vs_G_pairs.jsonl')
            expected = summary['comparisons'][name]['primary']
            mean_key, se_key, ci_key = 'difference_bb100', 'paired_se', 'ordinary_t95_CI'
            arm_a, arm_b = 'candidate', 'baseline'
            critical = 2.131449545559323
        elif audit['run'] == 'G_I_Sunday_Confirmation':
            path = directory/'I_vs_G_pairs.jsonl'
            expected = summary['primary']
            mean_key, se_key, ci_key = 'I_minus_G_bb100', 'paired_se', 't95_CI_df63'
            arm_a, arm_b = 'candidate', 'baseline'
            critical = 1.998340542520741
        else:
            path = directory/'paired_tables.jsonl'
            expected = summary['primary']
            mean_key, se_key, ci_key = 'diff_bb100', 'paired_se', 't95_CI'
            arm_a, arm_b = 'pablo_v4', 'G'
            critical = 2.039513446396408
        assert sha(path) == audit['raw_sha256']
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        assert len(rows) == audit['rows']
        assert len({r['seed'] for r in rows}) == len(rows)
        diffs = [(r[arm_a]['chips']-r[arm_b]['chips'])/200 for r in rows]
        mean, se = statistics.mean(diffs), statistics.stdev(diffs)/math.sqrt(len(diffs))
        assert abs(mean-expected[mean_key]) < 1e-10
        assert abs(se-expected[se_key]) < 1e-10
        assert all(abs(a-b) < 1e-9 for a,b in zip([mean-critical*se,mean+critical*se], expected[ci_key]))
        assert all(r[a]['all_seat_errors'] == 0 for r in rows for a in (arm_a, arm_b))
        assert all(sum(r[a]['window_chips'].values()) == r[a]['chips'] for r in rows for a in (arm_a, arm_b))
        print(audit['run'], audit['comparison'], 'PASS', len(rows), 'pairs', 'mean', round(mean,5), 'SE', round(se,5))
    for name in ('G', 'I', 'N'):
        qa = json.loads((HERE/'results/G_I_N_Sunday_Comparison'/('A_v_A_'+name+'.json')).read_text())
        assert qa['result_a'] == qa['result_b']
        assert qa['stats_a']['all_seat_errors'] == qa['stats_b']['all_seat_errors'] == 0
    print('PASS: input hashes, manifest/raw hashes, means/SE/CIs, windows, zero reported errors and G/I/N engine-trajectory A-v-A controls.')


if __name__ == '__main__':
    main()
