"""Public-history only cold starts; no historical team profiles used."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pokerbot.behavior_profile import BehaviorProfile
from pokerbot.opponent_evidence import hand_counts


def main():
    rows=[]
    for r in ('052','053','054'):
        d=json.loads((ROOT/'hands/external/WBot'/('saturday_r'+r+'.json')).read_text())
        labels=['WBot' if i==d['seat'] else 'seat:'+str(i) for i in range(len(d['players']))]
        profiles={label:BehaviorProfile() for label in labels if label!='WBot'}
        for i,h in enumerate(d['hands'],1):
            counts=hand_counts(h,labels)
            for label,profile in profiles.items():profile.update(counts[label])
            if i in (25,100,250,1000):
                for label,profile in profiles.items():
                    seat=int(label.split(':')[1])
                    rows.append(dict(round=d['ref'],hand=i,seat=seat,
                        # True name is an evaluation label only; tagger never sees it.
                        label_only=d['players'][seat],**profile.summary()))
    path=ROOT/'sunday/cold_profile_replay.json';path.write_text(json.dumps(dict(
        status='descriptive_public_history_replay_not_profit_validation',historical_names_used=False,rows=rows),indent=2))
    for row in rows:
        if row['hand']==1000:print(row['round'],row['seat'],row['label_only'],row['tags'],'drift',row['regime_change_suspected'])


if __name__=='__main__':main()
