"""
Sharecoin sortition selector: pick a committee (auditors, jurors, reviewers)
from a candidate pool using a public, verifiable random draw.

Same underlying mechanic as the raffle demo: waits for a real future block
height (chosen at the moment it's reached, not pre-guessed from a calendar
estimate), then draws committee members without replacement from the
candidate pool using that block's getrandombeacon value. Anyone can
reproduce the exact same result given the candidate list and the beacon
value, nobody, including whoever runs this script, can predict or influence
the outcome before that block exists.

Usage:
    python sharecoin-sortition-selector.py --candidates candidates.txt --committee-size 5 --blocks-ahead 5
"""

import argparse
import hashlib
import json
import time
import urllib.request
from base64 import b64encode

RPC_URL = "http://127.0.0.1:8332"
RPC_USER = "your_rpc_username"
RPC_PASS = "your_rpc_password"

WINDOW_SIZE = 8
POLL_INTERVAL_SECONDS = 15


def call_rpc(method, params=None):
    payload = json.dumps({
        "jsonrpc": "1.0",
        "id": "sharecoin-sortition-selector",
        "method": method,
        "params": params or [],
    }).encode()
    req = urllib.request.Request(
        RPC_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Basic " + b64encode(f"{RPC_USER}:{RPC_PASS}".encode()).decode(),
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
        if body.get("error"):
            raise RuntimeError(body["error"]["message"])
        return body["result"]


def draw_committee(candidates, committee_size, beacon_hex):
    """Deterministic, reproducible, without-replacement draw. Given the same
    candidate list and beacon value, anyone gets the exact same committee,
    in the exact same order."""
    sorted_candidates = sorted(candidates)
    remaining = list(sorted_candidates)
    picks = []
    for i in range(committee_size):
        round_hash = hashlib.sha256(f"{beacon_hex}:{i}".encode()).hexdigest()
        idx = int(round_hash, 16) % len(remaining)
        name = remaining.pop(idx)
        picks.append((name, round_hash, idx))
    return sorted_candidates, picks


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidates", required=True, help="File with one candidate name/ID per line.")
    parser.add_argument("--committee-size", type=int, required=True, help="How many to select.")
    parser.add_argument("--blocks-ahead", type=int, default=5, help="Blocks from now the selection height locks in at.")
    args = parser.parse_args()

    with open(args.candidates) as f:
        candidates = [line.strip() for line in f if line.strip()]

    if args.committee_size > len(candidates):
        print(f"Committee size {args.committee_size} is larger than the candidate pool ({len(candidates)}), clamping.")
        args.committee_size = len(candidates)

    current_height = call_rpc("getblockcount")
    target_height = current_height + args.blocks_ahead
    print(f"Candidate pool locked at block {current_height} ({len(candidates)} candidates).")
    print(f"Selection height: {target_height} (chosen now, at lock time, since this is a short, fixed lead, "
          f"not a calendar-time estimate).")

    while True:
        current_height = call_rpc("getblockcount")
        if current_height >= target_height:
            break
        print(f"Waiting... current height {current_height}, {target_height - current_height} block(s) to go.")
        time.sleep(POLL_INTERVAL_SECONDS)

    window_start = target_height - WINDOW_SIZE + 1
    beacon_result = call_rpc("getrandombeacon", [window_start, WINDOW_SIZE])
    beacon_hex = beacon_result["beacon"]

    sorted_candidates, picks = draw_committee(candidates, args.committee_size, beacon_hex)

    print()
    print(f"Selection height {target_height} confirmed.")
    print(f"Beacon window: blocks {window_start}-{target_height} (call: getrandombeacon {window_start} {WINDOW_SIZE})")
    print(f"Beacon value: {beacon_hex}")
    print()
    print("Draw order (verify by hand: sha256(f'{beacon}:{round}') mod candidates-remaining):")
    for i, (name, h, idx) in enumerate(picks):
        print(f"  Round {i + 1}: {h[:16]}... mod {len(sorted_candidates) - i} = {idx} -> {name}")
    print()
    print("Selected committee:")
    for name, _, _ in picks:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
