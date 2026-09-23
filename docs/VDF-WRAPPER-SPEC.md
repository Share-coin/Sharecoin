# VDF wrapper parameters: current version and permanence policy

This mirrors docs/BEACON-SPEC.md's structure and reasoning, because it is
the same kind of problem: `vdf-wrapper/sharecoin_vdf_wrapper.py`'s
underlying computation (a Wesolowski VDF over a class group derived from
`getrandombeacon`'s output) is permanent and independently verifiable by
anyone who reruns it. But the *usage conventions* - what discriminant size
and iteration count to use, what real-world delay that implies, what it's
recommended for - live in this document, one person can edit at any time,
and nothing previously stopped that from changing quietly.

## Read this first: what the VDF wrapper does and does not solve

A raw beacon value has two weaknesses, and the wrapper helps with them to different degrees.

1. **Withholding.** The miner who finds the block that completes the window sees the raw
   value first and can discard the block if they dislike it (docs/BEACON-SPEC.md, Version 2).
   If the value only becomes usable after a delay of several block intervals, that miner has
   to decide before they can learn it. To find out they must hold the block for the whole
   delay, and if another miner finds a block at that height in the meantime theirs is
   orphaned. So the delay turns withholding into a mostly blind gamble. In simulation
   (`docs/analysis/beacon_bias_sim.py`; 120 second blocks, a miner with 33% of the hashrate,
   up to 8 candidates evaluated in parallel), a 60 second delay leaves about 70% of the bias,
   5 minutes leaves about 20% and 10 minutes leaves about 5%.
2. **First-mover timing edge.** Whoever validates the window's last block first can read the raw
   value an instant before anyone else, which matters for anything that reacts to it (a bet, a
   front-run trade, an early guess). An equal, non-skippable sequential delay removes that edge
   for every party, including the node operator who saw the winning block first.

What the delay does not do: it does not help against a miner with a majority of the hashrate,
who can hold several blocks privately and out-wait the delay. It assumes nobody can run the VDF
much faster than the reference hardware. And it only helps applications that actually use the
delayed value.

An earlier version of this document said the wrapper does not reduce the bias at all and that
`window_size` is the lever for reducing it. Both were wrong: the window size does not change the
bias, and a long enough delay does reduce it.

## What is and isn't a protocol rule

**Not a protocol rule at all.** Unlike `getrandombeacon`, this tool is not
part of bitcoin-source, not RPC, not consensus-adjacent in any way. It is
an ordinary off-chain script that takes a `getrandombeacon` output as
input. Nothing about it is fixed by the node software; everything below is
this repository's own recommended convention, changeable the same way
BEACON-SPEC.md's conventions are: a new tagged, OpenTimestamped version,
never a silent edit.

The one property that *is* mathematically fixed, regardless of version:
`create_discriminant` derives the class group deterministically from the
`beacon` hex, with no ceremony and no party who could have set it up
maliciously - anyone can rederive the same group from the same beacon
value.

## Version 2 (current, 2026-09-23)

Corrects the "Read this first" section above. The parameters are unchanged (1024 bit
discriminant, 28,500,000 iterations, about 5 minutes on the Pi 5). Five minutes is about 2.5
block intervals. For a use where withholding matters, about 10 minutes (about 57,000,000
iterations, not yet benchmarked here, so measure before relying on it) leaves about 5% of the
bias in simulation at a 33% miner.

## Version 1 (superseded by Version 2)

**Erratum, 2026-09-23:** the "Read this first" section originally published with this version
said the wrapper does not shrink the withholding bias and that `window_size` is the lever. Both
were wrong, see Version 2. The parameters below are unchanged.

| Parameter | Value | Notes |
|---|---|---|
| Discriminant size | 1024 bits | `BQFC_MAX_D_BITS`, chiavdf's own hard ceiling (`src/bqfc.h`) - also the value Chia's own mainnet uses. Not a tunable choice; 2048 (this spec's original draft value) does not work, chiavdf rejects it outright. |
| Iteration count | 28,500,000 | Targets ~5 minutes on the Pi 5 (this project's backup node, used as reference hardware since it is the weakest machine in the deployment - the VPS/Oracle nodes will be faster, making this a conservative, not optimistic, delay estimate). |
| Real-world delay this implies | ~5 minutes on Pi 5 reference hardware | See "Benchmarking status" below for how this was measured. Faster hardware finishes sooner; this is the slow end of the range, deliberately. |

### Benchmarking status

Measured directly on the live Pi 5 backup node (`192.168.1.200`), not
estimated: a real `derive` run against an actual confirmed
`getrandombeacon` window (`start_height=1000, window_size=8`, chain tip at
height 1114 at the time) with `--iterations 5000000` took **52.582
seconds** wall time, end to end, including the real RPC round-trip - a
measured rate of **~95,100 iterations/second**. `28,500,000` iterations
(`300 seconds * 95,100`, rounded) was then chosen to target roughly 5
minutes on this hardware. Independently verifying that same output with
`verify` took 0.134 seconds - confirming the core VDF property directly
(compute: ~53s, verify: ~0.1s), not just asserting it from chiavdf's own
documentation.

This is a single-run measurement on one specific device, not an average
across many runs or devices. Re-benchmark (and bump this to Version 2) if
the reference hardware changes, or if a more rigorous multi-run
measurement is done. `vdf-wrapper/build_vdf.sh`'s own smoke test uses a
much smaller iteration count (100,000) purely to confirm the build works
quickly - that number is not a usable delay and must not be confused with
the calibrated value above.

## Intended applications

Same list as docs/BEACON-SPEC.md (lotteries, NFT/collectible reveals, fair
matchmaking, DAO/committee sortition, delayed-reveal commitments,
oracle/validator subset selection), specifically for the subset of those
where a first-mover timing edge on the raw beacon value would matter (for
example: an on-chain bet that resolves against the beacon, where whoever
sees the winning block first could otherwise act on it before anyone
else). For applications where neither withholding nor first-mover timing matters,
this tool adds delay for no benefit - use the base beacon directly.

## Permanence policy

Identical to docs/BEACON-SPEC.md's: any future change to the values in
this document is a new version (`Version 2`, `Version 3`, ...), never a
silent edit to `Version 1`'s numbers - committed to git history, tagged
(`vdf-wrapper-spec-v1`), and timestamped with
[OpenTimestamps](https://opentimestamps.org/) (`VDF-WRAPPER-SPEC.md.ots`,
committed alongside this file), so anyone can independently verify what
this document said and when, without trusting this repository, GitHub, or
its maintainer. Covered by the same `.github/workflows/spec-timestamp.yml`
automation as docs/BEACON-SPEC.md: re-stamped on change, upgraded to a
completed Bitcoin-anchored proof automatically once a day.
