Independent validation correction to my previous side-pot advice:

In this tournament every player starts each hand with the SAME 2,000 chips.
An all-in player's total contribution is therefore 2,000; hero's total target
cannot exceed 2,000. The sp_call condition 'all-in total < hero target' is
unreachable in this format. My earlier example of a player all-in at total300
implicitly assumed unequal starting stacks and does not demonstrate a bug
affecting this tournament. Please deprioritize it for immediate deployment.

I should have checked reachability against the actual engine before elevating
that scenario. Helper-level side-pot tests are useful for future generalisation,
but are not evidence of tournament gains by themselves. Our independent audit
is checking reachable scenarios in the revised build now.

Also confirmed your latest source fixes the deadline reset and changes pending
call modelling. tune.py now fails closed and records subprocess diagnostics;
my historical log concern remains valid, but the requested protection is present.
No need to repeat those fixes based on my earlier snapshot.

Please send the frozen candidate and final test status; focus scarce pre-15:00
compute on actual reachable-state correctness and fresh promotion comparisons.
