# Verified round attribution: version 8 is G

I checked the local Saturday real-round JSON directly. The authoritative `round.version` fields are:

| Round | Version | Chips | bb/100 | Timeouts |
|---|---:|---:|---:|---:|
| r049 | 8 | +267 | +1.335 | 1 |
| r050 | 8 | -6,048 | -30.240 | 1 |
| r051 | 8 | -8,575 | -42.875 | 1 |
| r052 | 8 | +3,684 | +18.420 | 1 |
| r053 | 8 | -6,731 | -33.655 | 0 |

Together these five rounds are -17,403 chips over 5,000 hands (-17.403 bb/100), with four timeouts. Per the user's correction, version 8 is G. Therefore these results belong to G, not N. Please correct the prior status/report and any comparisons that attributed r049-r053 to N. The round JSON identifies numeric version 8; the mapping of that version to G comes from the user's explicit confirmation.

Also, the prior note's version mapping (v7=G, v5=old G) conflicts with the user's correction. Please identify what upload/version event explains the differing labels, and use round-level numeric metadata plus the user-confirmed mapping for analysis going forward.
