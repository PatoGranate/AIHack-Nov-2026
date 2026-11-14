"""Remote worker: lend this machine's cores to a running lab / practice server.

    python worker.py --connect 192.168.1.20:50555 --key SECRET          # every core, 16 tables each
    python worker.py --connect 192.168.1.20:50555 --key SECRET --procs 4 --slots 24

The server must be started with --listen 0.0.0.0:50555 --key SECRET, and both
machines must run the same commit (workers refuse jobs from different code).
Only use this on a network you trust: the key is the only protection.
"""
import argparse
import os
import sys
from multiprocessing import get_context

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from sim.cluster import code_sha, worker_main  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--connect", required=True, help="server host:port")
    ap.add_argument("--key", required=True)
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--slots", type=int, default=16)
    a = ap.parse_args()
    host, port = a.connect.rsplit(":", 1)
    print("worker: %d processes x %d tables, code %s -> %s" % (a.procs, a.slots, code_sha(), a.connect))
    ctx = get_context("spawn")
    procs = [ctx.Process(target=worker_main, args=((host, int(port)), a.key.encode(), a.slots)) for _ in range(a.procs)]
    for p in procs:
        p.start()
    try:
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()


if __name__ == "__main__":
    main()
