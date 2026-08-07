## 7. Frozen artifact and reproducibility boundary

The final agent is **18,609 bytes**, contains 719 actions, uses
only the Python standard library, and has SHA-256:

`62fb5a5f66f0011092a2b51e3192879ba583d5d815d761f176091c615657147a`

The same bytes were imported and rerun on all 46 strict-future cases. Every
candidate reward, opponent reward, and win flag matched the selected research
policy exactly (`46/46` game rows).

The public Notebook embeds the production artifact and reproduces its byte
hash, compilation, archive membership, official price cliffs, and action-schema
smoke test. The Notebook image's installed game package is printed explicitly;
the reported replay research uses the official 1.32.4 schema rather than
treating a potentially lagged Notebook image as a score benchmark. The
multi-gigabyte replay download and route screen are summarized rather than
embedded. Episode boundaries, source artifact, rejected variants, and
fixed-vs-future result are reported so the scientific claim is narrower than
the submission claim.

Limitations remain:

- replay opponents do not react;
- an exact deterministic copy has symmetric logic;
- field/labor behavior is still mostly a complete route;
- public meta decay can occur within hours;
- `44/46` is not a promise of an official LB score.
