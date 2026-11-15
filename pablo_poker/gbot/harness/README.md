Copy into a checkout of `main` so that `PokerBot/` and `pablo_poker/` are siblings:

    cp gbot/harness/tdarena.py gbot/harness/td_power.py ../PokerBot/tools/
    cp -r gbot/harness/opponents/* ../PokerBot/tools/opponents/
    cd ../PokerBot
    python tools/tdarena.py ../pablo_poker/gbot/G_profile_tdf.py ../pablo_poker/gbot/G_frozen.py --field td --tables 128 --hands 1000 --seed 31

Fields: td (sunday_v2 clones), td_switch (policy switch at hand 500), td_fb (FieldBot clones; needs
pablo_poker/data/field_model.json, v3_model.json, hs_pool.json, field_skill.json).
