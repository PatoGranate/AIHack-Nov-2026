# Python path correction and no-jam paired screen

Correction to my earlier environment note: Anaconda Python is available at C:\Anaconda\Anaconda2\python.exe (Python 3.12.3). I verified it by running it directly. The plain python alias remains broken, but there is no need to install Python; the team can use the absolute interpreter path. The reviewer environment was able to run the following bounded local paired screens using 	ools/arena.py (LocalPlayer, so not server process/runtime certification).

- Candidate ggressive_nojam_i.py vs kit/bot.py, 24 tables x 200 hands per field: late seed9201 -28.0 bb/100 (SE17.6); real seed9202 -32.8 (SE11.1); heldout seed9203 -28.9 (SE18.3).
- Repeating the combined candidate on independent seeds was very different: real seed9302 +13.2 (SE14.7); heldout seed9303 -0.6 (SE13.6). This does not support a stable improvement or a stable loss; the first real seed was a strong negative outlier relative to the repeat.
- One-factor screens on real seed9202: no-jam-only, same opens as baseline, +11.1 (SE17.9); wider BTN/CO/HJ opens but retain baseline jamming, +0.8 (SE13.3). These are small/noisy screens. Do not promote.
- Instrumented 1,000-hand run of the no-jam candidate: 228 preflop raises, zero all-in actions, zero raise-to-total-stack actions, zero candidate errors. Syntax parse passed.

The factor screen suggests the combination may interact, but sample size is too small to identify why. Please keep the no-jam work in a separate sandbox candidate and, if continuing, use the direct Anaconda interpreter for a properly paired, larger independent-seed gate with jam invariant, errors, and runtimes reported. Do not change N/live or combine with the N experiment.