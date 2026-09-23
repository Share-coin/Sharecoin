"""
Sharecoin raffle demo (CLI version).

Locks a set of entrants at one block height, then draws a winner using a
future block's getrandombeacon value once that block has actually confirmed.
Nobody, including whoever runs this script, can predict the winner before
the beacon block exists.

Simplified for demo purposes: entrants are simulated by treating each txid
in the entry-height block as one "ticket". A real deployment would instead
scan for transactions actually sent to a dedicated raffle address, and map
each sender to one or more tickets by amount. A working example of that
fuller version is deployed live as a web app (`raffle_app.py`, referenced
in USECASES.md), this script is the minimal, dependency-free CLI version of
the same underlying mechanic.

Usage:
    python raffle.py --entry-height 500 --blocks-ahead 5
"""

import argparse
import hashlib
import json
import urllib.request
from base64 import b64encode

RPC_URL = "http://127.0.0.1:8332"
RPC_USER = "your_rpc_username"
RPC_PASS = "your_rpc_password"

WINDOW_SIZE = 8


def call_rpc(method, params=None):
    """Helper function to execute standard Bitcoin/Sharecoin JSON-RPC commands."""
    payload = json.dumps({
        "jsonrpc": "1.0",
        "id": "sharecoin-raffle",
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


def fetch_entrants_from_block(target_height):
    """
    Simulates fetching entry addresses from on-chain transactions.
    In a real app, you would scan block transactions sent to your raffle address.
    """
    print(f"[*] Scanning block {target_height} for raffle tickets...")
    block_hash = call_rpc("getblockhash", [target_height])
    if not block_hash:
        return []

    block_data = call_rpc("getblock", [block_hash])
    tx_list = block_data.get("tx", [])

    # For this demo, we'll treat each unique TXID as a ticket entry
    entrants = list(tx_list)
    print(f"[+] Found {len(entrants)} valid ticket entries in block {target_height}.")
    return entrants


def run_raffle_drawing(entry_height, beacon_height):
    """Executes the drawing using Sharecoin's live getrandombeacon."""
    entrants = fetch_entrants_from_block(entry_height)
    if not entrants:
        print("[-] No entrants found. Drawing aborted.")
        return

    current_count = call_rpc("getblockcount")
    if current_count < beacon_height:
        blocks_left = beacon_height - current_count
        print(f"[*] Waiting for beacon block... Current: {current_count}/{beacon_height} ({blocks_left} left).")
        return

    print(f"[*] Querying Sharecoin Beacon at height {beacon_height}...")
    # window_size=8 is a convenience default. The window size does not change how much
    # a miner who finds the last block can bias the result (docs/BEACON-SPEC.md).
    # getrandombeacon(start_height, window_size) combines blocks
    # [start_height, start_height + window_size - 1], so start_height is set
    # to make the window END at beacon_height, not start there, otherwise
    # this would actually need beacon_height + window_size - 1 confirmed,
    # not just beacon_height, mismatching the readiness check above.
    beacon_result = call_rpc("getrandombeacon", [beacon_height - WINDOW_SIZE + 1, WINDOW_SIZE])

    if not beacon_result:
        print("[-] Failed to retrieve randomness beacon from node.")
        return

    # getrandombeacon returns an object ({start_height, end_height,
    # window_size, beacon}), not a bare hex string, the actual entropy is
    # in the "beacon" field.
    beacon_hex = beacon_result["beacon"]
    print(f"[+] Beacon received: {beacon_hex}")

    # Sort to ensure the execution order is identical for anyone auditing
    entrants.sort()

    seed_hash = hashlib.sha256(bytes.fromhex(beacon_hex)).hexdigest()
    winning_index = int(seed_hash, 16) % len(entrants)
    winner = entrants[winning_index]

    print()
    print("=" * 50)
    print("SHARECOIN RAFFLE DRAWING COMPLETE")
    print("=" * 50)
    print(f"Total Tickets:   {len(entrants)}")
    print(f"Raffle Locked:   Block {entry_height}")
    print(f"Beacon Source:   Block {beacon_height}")
    print(f"Entropy Seed:    {seed_hash}")
    print(f"Winning Index:   {winning_index}")
    print(f"WINNING TXID:    {winner}")
    print("=" * 50)
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--entry-height", type=int, required=True, help="Block height at which ticket sales lock.")
    parser.add_argument("--blocks-ahead", type=int, default=5,
                         help="How many blocks after entry-height the beacon draw uses.")
    args = parser.parse_args()

    run_raffle_drawing(args.entry_height, args.entry_height + args.blocks_ahead)
