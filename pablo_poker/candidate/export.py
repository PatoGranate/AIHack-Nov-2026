"""Build a standalone candidate without changing the live pipeline's bot.py."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def export(params=None):
    src=(HERE/'engine.py').read_text(encoding='utf-8')
    p=json.loads((HERE/'baseline_params.json').read_text())
    p.update(params or {})
    model=json.loads((HERE/'live_model_snapshot.json').read_text())
    src=src.replace('\n# ---------------------------------------------------------------- tables\n',
                    '\nP.update('+repr(p)+')\n# ---------------------------------------------------------------- tables\n',1)
    marker='MODEL = {}    # filled by export_v2.py from data/v3_model.json (tools/build_v3_model.py)'
    if marker not in src:raise ValueError('model marker missing')
    src=src.replace(marker,'MODEL = '+repr(model),1)
    ast.parse(src)
    path=HERE/'bot.py'
    tmp=HERE/'bot.py.tmp'
    tmp.write_text(src,encoding='utf-8')
    tmp.replace(path)
    (HERE/'export_manifest.json').write_text(json.dumps(dict(
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),params=p,
        engine_sha256=hashlib.sha256((HERE/'engine.py').read_bytes()).hexdigest()),indent=2))
    return path


if __name__=='__main__':print(export())
