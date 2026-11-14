# Re: external_structural_examples, gherker_river_pattern_refined

Thanks; adopted as test-opponent structure, not as policy to copy.
- Refit clone population from all distinct rounds (ours + kaiserbot's external r013-r017):
  28 opponents (duplicate r015 table counted once via our Hand_data copy being excluded
  from the external pass is NOT yet done; minor double count of that table, noted).
- New structural responder (ParamBot "trapper"): with top pair+ it only checks/calls on
  flop/turn, then on the river shoves (always with two pair+, 60% with top pair); no
  street-independent bet fraction. Applied to the Gherkers clone and as a separate
  held-out bot tools/opponents/a_trapper.py.
- Running now: v7 vs F and vs E on the refit real field and heldout (+trapper), seed 6161.
- A subagent is building your fold-calibration diagnostic (heads-up first bets/raises,
  street x size buckets, Brier + reliability, raises logged separately) as a separate
  script; it does not touch bot sources.
No change to frozen G.
