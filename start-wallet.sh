#!/bin/bash
# Launches the Sharecoin wallet GUI, connected to the live public node -
# see this repo's README for details.
# -prune=550 keeps this wallet's disk footprint small by discarding old
# block data once it's been validated - fine for a normal wallet (balance/
# send/receive), but means this copy can't serve deep-history queries
# (getrandombeacon over an old block range) or rescan from a birth date
# older than the retained window. Run without -prune if you need either.
# -fallbackfee=0.0001 (~10 sat/vB) - this chain is too young/low-traffic
# for Bitcoin Core's automatic fee estimator to have real data yet, and
# the estimator has no fallback by default in modern Bitcoin Core (it's
# disabled for safety on mainnet). Without this, sending fails outright
# with "Fee estimation failed."
# -addnode (not -connect) - adds the public node as a known peer without
# disabling normal peer discovery. -connect is exclusive and would leave
# this wallet with exactly one peer and no fallback if that one node ever
# has a rough patch.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$DIR/datadir"
"$DIR/sharecoin-qt" -datadir="$DIR/datadir" -addnode=sharecoin.duckdns.org:8443 -prune=550 -fallbackfee=0.0001 -maxtipage=1209600
