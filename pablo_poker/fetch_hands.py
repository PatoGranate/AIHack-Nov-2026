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
import uuid
import urllib.error
import urllib.parse
import urllib.request


def get(site, path, token):
    req = urllib.request.Request(site.rstrip("/") + path, headers={"Authorization": "Bearer " + token,
                                                         # the site rejects Python's default User-Agent (403)
                                                         "User-Agent": "pokerbots-kit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("error")
        except Exception:
            msg = None
        raise SystemExit("%s: %s" % (e.code, msg or e.reason))


def complete_round(data, metadata):
    """An existing filename alone is not proof of a complete download."""
    expected=metadata.get('hands')
    hands=data.get('hands',[]) if isinstance(data,dict) else []
    if not isinstance(expected,int) or expected<=0 or len(hands)!=expected:return False
    if len({h.get('n') for h in hands})!=expected or any(not isinstance(h.get('events'),list) for h in hands):return False
    saved=data.get('round',{})
    return saved.get('ref')==metadata.get('ref') and saved.get('version')==metadata.get('version')


def write_round(path,data):
    tmp=os.path.join(os.path.dirname(os.path.abspath(path)),'round-'+uuid.uuid4().hex+'.tmp')
    try:
        with open(tmp,'x',encoding='utf-8') as f:json.dump(data,f)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--token", required=True, help="your team's data token from the AI Poker Bots page")
    ap.add_argument("--site", default="https://imperialaihack.com")
    ap.add_argument("--out", default="hands")
    a = ap.parse_args()
    res = get(a.site, "/api/poker/results", a.token)
    rounds = res.get("rounds", [])
    os.makedirs(a.out, exist_ok=True)
    new = 0
    for rd in rounds:
        dest = os.path.join(a.out, rd["ref"].replace("/", "_") + ".json")
        if os.path.exists(dest):
            try:
                with open(dest,encoding='utf-8') as f:existing=json.load(f)
                if complete_round(existing,rd):continue
            except (OSError,ValueError):pass
        data = get(a.site, "/api/poker/hands?ref=" + urllib.parse.quote(rd["ref"]), a.token)
        data["round"] = rd
        if not complete_round(data,rd):
            print('round incomplete; will retry:',rd['ref'])
            continue
        write_round(dest,data)
        new += 1
        print("saved", dest, "(%d hands, %+d chips)" % (len(data["hands"]), rd["chips"]))
    print("%s: %d new round(s); %d in %s/" % (res.get("team", "your team"), new, len(rounds), a.out))


if __name__ == "__main__":
    main()
