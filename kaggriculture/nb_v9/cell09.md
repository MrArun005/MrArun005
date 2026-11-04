## 6. Failure audit and rejected local optima

The strict-future losses are intentionally not hidden:

```text
episode 90477635 | Seb (allegedly) | seat 1 | margin -2855
episode 90483794 | Seb (allegedly) | seat 1 | margin -5668
```

Both belong to the same six-hand opening family. It is a real
rock-paper-scissors signal:

- old v18 closed loop won only **2/49** current outer cases, and both wins were
  against that family;
- the current v22 route won **44/46**, and both losses were against it;
- changing to v18 at step 96 kept the same win count but broke accumulated
  state, dropping mean margin from `+3,524` to `-3,092`;
- five fixed alternate routes that beat one older episode went **0/2** on later
  episodes;
- targeted strawberry/wool/milk dumping did not improve unknown-seed wins;
- fertilizer dumping went **0/16** because fertilizer is production input.

These are examples of exactly the local optimization this release is trying to
avoid. None is in `main.py`. A future counter should learn a coherent opening
policy before step 0 or a true state-value bridge—not splice a complete route
after its inventory and labor assumptions are already false.
