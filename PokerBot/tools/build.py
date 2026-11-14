"""Build a self-contained bot: python tools/build.py OUT.py [--params mod] [key=val ...]"""
import sys, os, importlib.util, ast
T = os.path.dirname(os.path.abspath(__file__))

def build(out, overrides=None, params_file=os.path.join(T, "params_base.py")):
    spec = importlib.util.spec_from_file_location("pp", params_file)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    p = dict(m.PARAMS); p.update(overrides or {})
    src = open(os.path.join(T, "src_bot.py")).read()
    ev = open(os.path.join(T, "fasteval.py")).read().split('"""', 2)[2]
    tb = open(os.path.join(T, "preflop_tables.py")).read()
    body = "\n".join("    %r: %r," % (k, v) for k, v in p.items())
    src = src.replace("#@@EVAL@@", ev.strip()).replace("#@@TABLES@@", tb.strip()).replace("    #@@PARAMS@@", body)
    open(out, "w").write(src)
    return p

if __name__ == "__main__":
    ov = {}
    pf = os.path.join(T, "params_base.py")
    args = sys.argv[2:]
    for a in args:
        if a.startswith("--params="): pf = a.split("=", 1)[1]; continue
        k, v = a.split("=", 1); ov[k] = ast.literal_eval(v)
    build(sys.argv[1], ov, pf)
    print("built", sys.argv[1], os.path.getsize(sys.argv[1]), "bytes")
