# Beacon parameters: current version and permanence policy

The `getrandombeacon` RPC's underlying data is permanent and independently
verifiable (any node can recompute it from `mix_hash` values it has already
validated, no trust in the maintainer required). But the *usage
conventions* around it, what window size to use, how long to wait, what
it's recommended for, live in documentation and demo code that one person
controls and can edit at any time. Nothing previously stopped that from
changing quietly, with no record of what the guidance used to say.

This file is the fix: a single, dedicated, versioned place for those
conventions, timestamped independently of this repository.

## What is and isn't a protocol rule

**Fixed by the protocol** (true for every caller, cannot be changed without
a consensus-level fork):

- `getrandombeacon start_height [window_size]` only returns a value once
  every block in `[start_height, start_height + window_size - 1]` is on the
  active chain. It errors out, naming exactly how many more blocks are
  needed, if the window isn't fully confirmed yet.
- `window_size` must be between 2 and 10000. `window_size=1` is rejected by
  the RPC itself. This is a historical safeguard, not a security boundary:
  see the erratum under Version 2, a window of 1 is no easier to bias than a
  window of 8.
- The value itself is the SHA-256 of the `mix_hash` values of that window's
  blocks, concatenated in order. Any node can recompute it independently
  from data it has already validated.
- If `window_size` is omitted, the RPC itself defaults to **100**.

**Not fixed by the protocol** (caller/application choices, documented here
only as recommendations):

- What window size to actually use.
- How many blocks ahead of "now" to lock in a target height.
- What the result is recommended to be used for.

Nothing enforces these at the consensus level. Any application can call
`getrandombeacon` with whatever parameters it wants. The table below
records what this repository's own reference implementations currently
use, so that changing them later means a new tagged version of this file,
not a silent edit.

## Version 2 (current, 2026-09-23)

This version corrects Version 1's security claims. It does not change any
parameter. Version 1 said a larger window bounds a miner's influence more
tightly and that `window_size=1` gives "zero protection". Both were wrong.
The miner who finds the block that completes the window sees the finished value
before deciding whether to publish it, whatever the window size, and can discard
the block and try again (losing that block's reward). The window size does not
change how much that is worth. The size of the bias depends on the miner's share
of the hashrate, and nothing else.

What a miner with share `a` of the hashrate can do, when the outcome they want
has probability `q` by chance:

    P(get the outcome they want) = q / (1 - a(1 - q))
    most they can multiply their odds by = 1 / (1 - a)

| Hashrate share a | Coin flip (q = 0.5) | 100-entrant raffle, chance to win vs fair |
|---|---|---|
| 10% | 52.6% | x1.11 |
| 25% | 57.1% | x1.33 |
| 33% | 59.9% | x1.49 |
| 40% | 62.5% | x1.66 |
| 49% | 66.2% | x1.94 |

These figures come from `docs/analysis/beacon_bias_sim.py`, which simulates the
real construction (SHA-256 over concatenated `mix_hash` values) and gives the same
result for window sizes 1, 2, 8 and 100. The one-bit case matches the analysis in
Bonneau, Clark and Goldfeder, "On Bitcoin as a public randomness source" (2015),
which bounds the attack by the block reward the attacker gives up. SHC has no market
price, so this spec makes no claim about what an attack costs in money.

The bound holds only if:

- no single miner holds a majority of the hashrate (above 50% a miner can rewrite the
  window and retry, and there is no useful bound);
- the inputs (entrants, options, the thing being drawn from) were committed before the
  block that completes the window was found;
- nobody holds several of the last blocks of the window privately. That takes about
  `a^k` luck for `k` blocks, so it matters mostly for large `a`.

Recommendations:

1. Commit inputs at least one block before the block that completes the window.
2. Check the largest miner's current share at https://sharecoin.cc/beacon/ before relying on
   a result. If one miner holds a majority, do not use the beacon for anything that matters.
3. If withholding matters for your use, add a delay of several block intervals after the value
   is known, see docs/VDF-WRAPPER-SPEC.md. A 10 minute delay on this 2 minute chain leaves about
   5% of the bias in simulation.
4. Pick any window you like. 8 is a convenience default, not a security parameter.

| Parameter | Value | Notes |
|---|---|---|
| Reference window size | 8 blocks | Unchanged. Not a security parameter, the bias bound does not depend on it. |
| Lead time before locking a target height | At least 1 block | See the Version 1 table for what each demo uses. |
| Minimum confirmations before treating a result as final | 0 beyond the window itself | Unchanged. |

## Version 1 (superseded by Version 2)

**Erratum, 2026-09-23:** the sentence "Larger windows bound an attacker's influence more
tightly" in the table below was wrong. See Version 2. The text is left as originally
published so the record stays accurate.

| Parameter | Value | Notes |
|---|---|---|
| Reference window size | 8 blocks | Smaller than the RPC's own default of 100, chosen across this repo's demo scripts for faster, easier-to-follow illustrations. Larger windows bound an attacker's influence more tightly (see `docs/DETAILS.md`); 8 is a usability tradeoff, not a security-optimal value. |
| Lead time before locking a target height | Use-case dependent, see table below | There is no single fixed value; each demo picks a lead time appropriate to its own purpose. |
| Minimum confirmations before treating a result as final | 0 beyond the window itself | The reference demos treat a beacon value as final the moment the RPC returns one, with no additional confirmation buffer. Applications with a lower risk tolerance for chain reorganizations may reasonably choose to wait for additional confirmations past `start_height + window_size - 1`; this repo's demos currently do not. |

Lead time by reference demo, as actually implemented in this repo:

| Demo | Lead time | Reasoning |
|---|---|---|
| Oracle selector | 0 (uses the current tip immediately) | Needs an answer right away, not after a delay. |
| Raffle / roulette web demos | 1 block | Kept short so a live demo resolves quickly; still strictly in the future at commit time. |
| Sortition selector | 5 blocks (default, caller-adjustable) | Committee selection tolerates a short wait. |
| Time-locked vault | 10 blocks (default, caller-adjustable) | Deliberately longer, since the use case is a delayed reveal. |

## Intended applications (documented, not exhaustive, not enforced)

Lotteries and raffles, NFT/collectible reveals, fair matchmaking, DAO or
committee sortition, delayed-reveal commitments, oracle/validator subset
selection. This list describes what the reference demos in this repo
illustrate. It is not a claim that these are the only valid uses, nor a
guarantee that any of them are appropriate for real-money stakes without
your own risk assessment, see `docs/DETAILS.md`'s "Known limitations"
section.

## Permanence policy

Any future change to the values in this document will be published as a
new version of this file (`Version 2`, `Version 3`, ...), never a silent
edit to `Version 1`'s numbers. Each version is:

1. Committed to this repository's git history (ordinary, but permanent
   and diffable as long as history isn't force-rewritten).
2. Tagged as a git release (e.g. `beacon-spec-v1`), giving a permanent,
   unambiguous reference for "what this document said, as of this
   version."
3. Timestamped with [OpenTimestamps](https://opentimestamps.org/), which
   anchors a hash of this exact file into the real Bitcoin blockchain,
   infrastructure this project's maintainer does not control and cannot
   rewrite. The proof file (`BEACON-SPEC.md.ots`) is committed alongside
   this document. Anyone can independently verify, using only Bitcoin
   itself, that this exact text existed unchanged at the time it claims,
   with no need to trust this repository, GitHub, or its maintainer.
   A submitted proof only becomes a completed, verifiable Bitcoin
   anchor once its calendar servers' pending attestations are
   *upgraded* - a step that's easy to forget and was in fact missed
   for days at a time in the past. `.github/workflows/spec-timestamp.yml`
   (shared with `docs/VDF-WRAPPER-SPEC.md`, which gets identical
   treatment) now automates both halves of this: it re-stamps the file
   the moment its content changes on `master`, and checks once a day
   whether the proof is upgradable yet, committing the completed proof
   the moment it is. Deciding whether a given edit warrants a new
   numbered version (`Version 2`, `Version 3`, ...) stays a human call,
   not something this automation infers on its own.

This does not make the parameters themselves immutable, they are usage
conventions, not consensus rules, and may reasonably need to change. What
it makes immutable is the *record* of what was recommended and when, so
no earlier version can be quietly rewritten out of history.
