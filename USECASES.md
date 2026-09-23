# Sharecoin randomness beacon: use cases

`getrandombeacon` turns already-mined blocks into a public, verifiable
source of randomness (see `docs/BEACON-SPEC.md` for exactly what it
guarantees and what's just demo convention). This doc explains, for each
demo script in `demos/`, what it does and a real-world scenario it fits.
Kept honest on purpose: a use case that doesn't actually fit the technology
is recorded as such below, not smoothed over.

## How the beacon fits into all of these

Every script here follows the same shape:

1. Lock something (a candidate list, an entrant pool, a secret) at the
   current block height, or decide how many blocks ahead the draw should
   happen.
2. Wait for a specific future block to actually confirm. Nobody, including
   whoever runs the script, can know that block's beacon value before it
   exists.
3. Once that block confirms, pull its `getrandombeacon` value and use it to
   deterministically pick a winner, a committee, or a reveal moment.
4. Anyone can redo step 3 by hand with the same public inputs and get the
   same answer. That's what makes the result verifiable rather than just
   "trust the operator."

## Scripts

### `raffle.py` - lotteries and raffles

Locks an entrant list at one block height, draws a winner from a future
block's beacon once it's confirmed.

**Real-world example:** a community giveaway where entrants send a small
amount of SHC to a raffle address before a cutoff block. Once the draw
block confirms, anyone (not just the organizer) can recompute the winner
from the entrant list and the public beacon value, so nobody has to take
the organizer's word for a fair result.

This CLI version simulates entrants using raw txids in a block as a
stand-in for tickets. A fuller version that actually scans for payments
sent to a dedicated raffle address is deployed live as a web app
(`raffle_app.py`), same underlying mechanic, more realistic ticket
handling.

### `sharecoin-sortition-selector.py` - committee and jury selection

Draws a committee, without replacement, from a candidate pool using a
future block's beacon.

**Real-world example:** a DAO or open-source project needs to pick a
rotating review committee (code auditors, grant reviewers, dispute jurors)
from a larger pool of eligible members, without any single person deciding
who gets picked. Publish the candidate list, agree on a future block height,
and let the beacon draw the committee. Anyone can verify the result matches
the published candidates and beacon value.

### `sharecoin-oracle-selector.py` - active node/validator subset selection

Selects a subset of nodes from a pool for the *current* confirmed block, no
scheduled wait involved, since this needs an answer immediately rather than
after a delay.

**Real-world example:** a data oracle network with more registered
providers than needed for any single round wants to rotate which subset is
actually queried, so no fixed group of providers can quietly become a
single point of trust or collusion. Note the honest timing caveat in the
script's own docstring: the beacon only changes when a new block confirms
(about every 2 minutes on this network), so repeated calls within the same
block return the same subset, that's expected behavior, not a bug.

### `sharecoin-timelock-vault.py` - delayed-reveal commitments

A commit-then-reveal scheme: lock a secret and a commitment hash now,
reveal it only once a target block height has genuinely passed, with the
beacon value serving as public proof the reveal condition was actually met.

**Real-world example:** a sealed-bid auction, or a "predictions locked in
advance" contest, where participants need proof that whoever holds the
secret didn't peek early and adjust their story. Publishing the commitment
hash before the reveal lets anyone confirm afterward that the revealed
content matches what was originally locked.

**Important limitation, carried from the script's own docstring:** this is
not true cryptographic timelock encryption. The decryption key is generated
at lock time and held by the operator, who could in principle apply it
early if they chose to break their own word, the beacon makes that
detectable after the fact (the reveal moment is publicly verifiable), not
cryptographically impossible in advance. Real timelock encryption, where the
key is mathematically inaccessible until the condition is met, would need
identity-based encryption (e.g. drand's "tlock"), which a plain hash-output
beacon isn't built for.

## Also deployed live, not in `demos/`

Live web apps rather than standalone scripts, all linked from
[sharecoin.cc](https://sharecoin.cc):

- **`raffle_app.py`** - the fuller version of the raffle mechanic above,
  actually scans for real payments to a dedicated address instead of using
  txids as a stand-in for tickets.
- **`roulette_app.py`** - same underlying draw mechanic, framed explicitly
  as a pitch for how a real-money game could be built on this, deliberately
  not itself a real-money product. Unlicensed real-money gambling is a
  legal/regulatory problem independent of the code being correct, so this
  stays a simulated-credits demo.
- **`audit_draw_app.py`** (added 2026-07-31) - the raffle/sortition
  mechanic relabeled for the AML/compliance-audit and customs/shipping
  inspection-selection use cases documented below: pick N candidates out
  of a pool for closer review, with nobody able to steer which ones get
  picked. Mechanically identical to the raffle demo, different framing.
- **`fair_queue_app.py`** (added 2026-07-31) - a genuinely different
  mechanic from the others: produces a full verifiable ordering of an
  entire list (a beacon-seeded Fisher-Yates shuffle), not a subset
  selection. Fits speaker order, PR review queues, standup order, or any
  "who goes first" decision for a whole group.
- **`sealed_bid_app.py`** (added 2026-07-31) - a live, multi-user version
  of the `sharecoin-timelock-vault.py` commit-then-reveal pattern: bidders
  submit a hash of their sealed bid before a lock height, reveal only
  becomes possible once a target block confirms, highest valid revealed
  bid wins. Carries the same honest limitation as the CLI timelock-vault
  script (see above): proves the reveal happened on schedule, does not
  stop the operator from peeking at commitments early - real
  cryptographic timelock encryption would need identity-based encryption
  this beacon doesn't provide.

## Evaluated and not recommended

- **Kernel entropy injection.** An early draft script periodically wrote a
  SHA-512 hash (beacon value mixed with local time and `os.urandom`) into
  `/dev/urandom`, framed as "injecting GPU-mined entropy into the OS". Not
  included in `demos/`, and not recommended, for two reasons:
  - The framing overstates the benefit. A modern Linux kernel's CSPRNG is
    already cryptographically secure once seeded at boot from multiple
    independent hardware sources; mixing in extra hash output on top of an
    already-secure pool doesn't add meaningful real-world security. Writing
    to `/dev/urandom` can't make the pool *weaker* (the kernel only ever
    mixes new input through a one-way function), but claiming it
    meaningfully strengthens an already-secure system is misleading.
  - It requires running arbitrary code as root against a system security
    file, on a permanent loop, for a benefit that doesn't hold up. That's a
    real operational risk to take on for a use case that isn't actually
    solving a real gap.

## Proposed and evaluated, not built

- **High-value wholesale settlement / interbank RTGS batching** (proposed
  2026-07-23). Idea: batch high-value interbank transfers into blocks, use
  the beacon to shuffle/clear them, eliminating front-running. Evaluated as
  a poor fit:
  - RTGS (CHAPS, Fedwire) exists specifically to settle transactions
    individually and immediately, precisely to avoid the systemic risk of
    a batch not fully clearing before a participant fails. Batching
    reintroduces the exact risk RTGS is designed to eliminate.
  - Scale/trust mismatch: real interbank settlement requires central-bank
    oversight, audits, and legal frameworks far beyond a single-maintainer,
    unaudited PoC chain.
  - The front-running/MEV framing doesn't map cleanly, MEV is a public
    mempool/order-book problem, interbank transfers aren't typically
    visible to other banks before settlement in the first place.

- **Time-locked interbank escrow / treasury bond auctions** (proposed
  2026-07-23). Idea: banks submit encrypted sealed bids, decryption tied to
  a future block height, preventing early leaks or late/backdated bids.
  Better conceptual fit (this is genuinely the timelock-vault pattern), but
  the pitch overstated the guarantee: it described true cryptographic
  timelock encryption ("bids automatically unpack the exact moment miners
  solve block X"), which is not what the current beacon provides, see the
  timelock vault caveat above. What it *can* honestly support: normal
  encryption keeps bids private regardless of timing, and the beacon makes
  the reveal moment itself unpredictable in advance and verifiable after
  the fact, so a late bid can't be disguised as an early one. The
  "operator could technically peek early and just not tell anyone" gap
  remains open under the current design.

- **Randomised AML/compliance audit selection** (proposed 2026-07-23, then
  corrected). Idea: banks pick which flagged transactions get a secondary
  compliance review by seeding a deterministic selection from the beacon
  value of a target block, so no internal actor can bias which accounts get
  audited. Best conceptual fit of the three proposed so far, this is
  exactly the sortition-selector pattern already built above. First draft
  of the pitch had two factual errors, corrected in the second pass:
  - Claimed the beacon makes manipulation "mathematically impossible",
    corrected to the actual model: bounded, not literally impossible.
    A miner who finds the last block of the window can discard it and
    try again, forfeiting that block's reward, so what a miner can gain
    depends on their share of the hashrate (docs/BEACON-SPEC.md).
  - Claimed the audit roster is proven via a "Zero-Knowledge Proof",
    corrected: nothing here is zero-knowledge (which proves a statement
    without revealing the underlying data). This is the opposite, full
    public verifiability, where anyone can recompute the exact same
    selection from openly published inputs.
  - Real dependency correctly identified in the corrected version: this
    only neutralises a corrupt insider if the chain's hashrate is genuinely
    external to the bank. A bank's own small private deployment could be
    dominated by that same insider with enough resources, collapsing the
    guarantee.
  - Minor unresolved detail: "the block mined exactly at midnight" needs
    the same real-time-trigger scheduling the raffle demo uses (wait for
    the clock time, then take whatever height is current), since blocks
    aren't scheduled to timestamps.
  - **Built 2026-07-31**: `audit_draw_app.py` (see "Also deployed live"
    above) - this pitch and the customs/shipping-inspection one below no
    longer need to stay hypothetical, there's a real, live, running demo
    of exactly this mechanic now.

- **Shipping and logistics** (proposed 2026-07-28). Three pitches, all
  reusing patterns already validated above rather than needing anything
  new:
  - Random customs/inspection selection: same fit as the AML
    audit-selection entry above, no insider can predict which containers
    get physically inspected.
  - Sealed freight-tender bidding: the timelock-vault pattern, same
    "operator could technically peek early" caveat as the treasury-auction
    entry above. **Built 2026-07-31**: `sealed_bid_app.py` (see "Also
    deployed live" above) is a live, multi-bidder version of exactly this.
  - Overbooking/berth-slot tiebreaking: same sortition pattern, smaller
    niche, but a fair alternative to opaque carrier discretion.
  - Adjacent pitch already rejected elsewhere and not re-litigated here:
    supply-chain anti-counterfeiting/provenance logging doesn't use the
    beacon at all (it's a timestamping problem), and its usual threat
    model (nation-state tampering) is mismatched to this chain's actual
    hashrate.
