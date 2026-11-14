"""Download every hand your team has played in the AI Poker Bots tournament.

    python fetch_hands.py --token YOUR-DATA-TOKEN

Your data token is on the AI Poker Bots page, under "Your table's data", once you're
logged in. It reads your own team's results and nothing else; don't share it.

Saves one JSON file per round in hands/, skipping rounds you already have. Each hand
has every action at your table, the board, every seat's chip result ("results"), your
own cards, and opponents' cards only when they reached showdown.

Event format (in "events"):
    ["post", seat, amount]                 blind posted
    ["act", seat, action, amount]          fold / check / call (chips added) / raise (raise-to total)
    ["board", street, cards]               flop / turn / river, all board cards so far
    ["refund", seat, amount]               uncalled bet returned
    ["win", seat, amount, hand_name]       chips won (hand_name is null if everyone else folded)
"""
import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request


def get(site, path, token):
    req = urllib.request.Request(
        site.rstrip("/") + path,
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": "pokerbots-kit/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("error")
        except Exception:
            msg = None
        raise SystemExit("%s: %s" % (e.code, msg or e.reason))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--token", required=True, help="your team's data token from the AI Poker Bots page")
    ap.add_argument("--site", default="https://imperialaihack.com")
    ap.add_argument("--out", default="hands")
    ap.add_argument("--practice-out", help="optional separate directory for refs containing /practice/")
    a = ap.parse_args()
    res = get(a.site, "/api/poker/results", a.token)
    rounds = res.get("rounds", [])
    team = res.get("team", "your team")
    os.makedirs(a.out, exist_ok=True)
    new = 0
    for rd in rounds:
        out_dir = a.practice_out if a.practice_out and "/practice/" in rd["ref"] else a.out
        os.makedirs(out_dir, exist_ok=True)
        dest = os.path.join(out_dir, rd["ref"].replace("/", "_") + ".json")
        if os.path.exists(dest):
            # Older hand files may predate the round summary metadata. Refresh
            # metadata without replacing the stored hand histories.
            with open(dest, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("round") != rd or data.get("team") != team:
                data["round"] = rd
                data["team"] = team
                with open(dest, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                print("updated metadata", dest)
            continue
        data = get(a.site, "/api/poker/hands?ref=" + urllib.parse.quote(rd["ref"]), a.token)
        data["round"] = rd
        data["team"] = team
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        new += 1
        print("saved", dest, "(%d hands, %+d chips)" % (len(data["hands"]), rd["chips"]))
    print("%s: %d new round(s); %d round refs checked" % (team, new, len(rounds)))


if __name__ == "__main__":
    main()
