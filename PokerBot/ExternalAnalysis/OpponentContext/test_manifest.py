"""Bounded regression checks for the manifest trust boundary; no poker simulation."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oc_parse as P


class ManifestChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.hand = self.root / 'hand.json'
        self.hand.write_text(json.dumps({'ref': 'saturday/r001', 'players': ['A', 'B'], 'hands': []}), encoding='utf-8')
        self.manifest = self.root / 'manifest.csv'
        for key, value in [('POKER', str(self.root / 'PokerBot')), ('GLOBS', [str(self.hand)]), ('PM_MANIFEST', str(self.manifest))]:
            ctx = patch.object(P, key, value)
            ctx.start()
            self.addCleanup(ctx.stop)
        self.write_manifest()

    def write_manifest(self, digest=None, path='hand.json', duplicate=False):
        row = dict(path=path, status='used', sha256=digest or hashlib.sha256(self.hand.read_bytes()).hexdigest())
        with self.manifest.open('w', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=['path', 'status', 'sha256'])
            writer.writeheader()
            writer.writerow(row)
            if duplicate:
                writer.writerow(row)

    def test_matching_manifest_loads(self):
        self.assertEqual(len(P.load_tables()), 1)

    def test_missing_manifest_fails(self):
        self.manifest.unlink()
        with self.assertRaisesRegex(SystemExit, 'manifest is missing'):
            P.load_tables()

    def test_wrong_hash_fails(self):
        self.write_manifest(digest='0' * 64)
        with self.assertRaisesRegex(SystemExit, 'SHA256 differs'):
            P.load_tables()

    def test_changed_bytes_fail_even_if_json_semantics_unchanged(self):
        with self.hand.open('a', encoding='utf-8') as out:
            out.write('\n')
        with self.assertRaisesRegex(SystemExit, 'SHA256 differs'):
            P.load_tables()

    def test_changed_input_set_fails(self):
        self.write_manifest(path='other.json')
        with self.assertRaisesRegex(SystemExit, 'input set differs'):
            P.load_tables()

    def test_duplicate_used_paths_fail(self):
        self.write_manifest(duplicate=True)
        with self.assertRaisesRegex(SystemExit, 'duplicate used paths'):
            P.load_tables()


if __name__ == '__main__':
    unittest.main(verbosity=2)