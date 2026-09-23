#!/usr/bin/env python3
"""
VDF wrapper around Sharecoin's getrandombeacon RPC.

Applies a Wesolowski VDF (class groups of imaginary quadratic order - no
trusted setup, via the vendored chiavdf in vdf-wrapper/vendor/chiavdf/) on
top of getrandombeacon's raw output.

What the delay adds: the miner who finds the last block of a window sees the raw
beacon value first and could discard the block if they dislike it. A delay of several
block intervals makes that a blind gamble, and it also removes the timing edge of
whoever validates the window's last block first. Everyone, including that node
operator, waits the same enforced sequential delay before the value is usable. It does
not help against a miner with a majority of the hashrate. See
docs/VDF-WRAPPER-SPEC.md for the full threat model and the versioned,
benchmarked parameters (discriminant size, iteration count, and what
real-world delay that corresponds to on reference hardware).

Requires: run this with the venv build_vdf.sh created
(vdf-wrapper/.venv/bin/python3), which has the vendored chiavdf built and
installed. Nothing else to pip install.

Usage:
  sharecoin_vdf_wrapper.py derive <start_height> [window_size]
      [--rpc-host HOST] [--rpc-port PORT] [--rpc-user USER]
      [--rpc-password PASSWORD] [--iterations N] [--discriminant-bits N]

  sharecoin_vdf_wrapper.py verify <beacon_hex> <iterations> <discriminant_bits> <y_hex> <proof_hex>

RPC credentials are never hardcoded here - pass --rpc-password or set
SHARECOIN_RPC_PASSWORD.
"""
import argparse
import base64
import http.client
import json
import os
import sys

from chiavdf import create_discriminant, prove, verify_wesolowski

DEFAULT_RPC_HOST = "127.0.0.1"
DEFAULT_RPC_PORT = 19710          # matches ../start-node.bat's regtest default
DEFAULT_RPC_USER = "sharecoin"    # matches ../start-node.bat's convention

# See docs/VDF-WRAPPER-SPEC.md Version 1 for how these were chosen and
# benchmarked - override with --iterations / --discriminant-bits for other
# deployments/hardware rather than editing the defaults here silently.
# 1024 is chiavdf's own hard cap (BQFC_MAX_D_BITS in src/bqfc.h) and also
# the value Chia's own mainnet uses - not an arbitrary choice.
DEFAULT_DISCRIMINANT_BITS = 1024
# Targets ~5 minutes on the Pi 5 reference hardware, calibrated from a real
# measured rate of ~95,100 iterations/sec (see docs/VDF-WRAPPER-SPEC.md
# Version 1) - not a guess. Re-benchmark and bump the version if deployment
# hardware changes.
DEFAULT_ITERATIONS = 28_500_000

# Fixed canonical generator element, form_size=100 (chiavdf's own convention -
# see tests/test_verifier.py in the upstream project). The beacon's value
# picks which class group is used (via the discriminant); the VDF always
# starts squaring from this same generator within that group.
GENERATOR_ELEMENT = b"\x08" + (b"\x00" * 99)


def rpc_call(host, port, user, password, method, params):
    if not password:
        raise SystemExit(
            "Refusing to guess an RPC password. Pass --rpc-password or set "
            "SHARECOIN_RPC_PASSWORD - never hardcode real credentials in this script."
        )
    conn = http.client.HTTPConnection(host, port, timeout=30)
    payload = json.dumps({"jsonrpc": "1.0", "id": "vdf-wrapper", "method": method, "params": params})
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    headers = {"Content-Type": "application/json", "Authorization": f"Basic {auth}"}
    conn.request("POST", "/", payload, headers)
    resp = conn.getresponse()
    body = json.loads(resp.read())
    conn.close()
    if body.get("error"):
        raise SystemExit(f"RPC error from {method}: {body['error']}")
    return body["result"]


def cmd_derive(args):
    password = args.rpc_password or os.environ.get("SHARECOIN_RPC_PASSWORD")
    params = [args.start_height] + ([args.window_size] if args.window_size is not None else [])
    result = rpc_call(args.rpc_host, args.rpc_port, args.rpc_user, password, "getrandombeacon", params)
    beacon_hex = result["beacon"]
    challenge = bytes.fromhex(beacon_hex)

    print(f"Raw beacon (start_height={result['start_height']}, end_height={result['end_height']}, "
          f"window_size={result['window_size']}): {beacon_hex}")
    print(f"Running VDF: discriminant_bits={args.discriminant_bits}, iterations={args.iterations} "
          f"(see docs/VDF-WRAPPER-SPEC.md for the real-world delay this corresponds to on reference hardware)")

    discriminant = create_discriminant(challenge, args.discriminant_bits)
    vdf_result = prove(challenge, GENERATOR_ELEMENT, args.discriminant_bits, args.iterations, "")
    form_size = len(vdf_result) // 2
    y, proof = vdf_result[:form_size], vdf_result[form_size:]

    if not verify_wesolowski(str(discriminant), GENERATOR_ELEMENT, y, proof, args.iterations):
        raise SystemExit("INTERNAL ERROR: freshly-computed proof failed its own verification - do not trust this output")

    print()
    print("Derived (VDF-delayed) randomness:")
    print(f"  beacon_hex        = {beacon_hex}")
    print(f"  discriminant_bits = {args.discriminant_bits}")
    print(f"  iterations        = {args.iterations}")
    print(f"  y (hex)           = {y.hex()}")
    print(f"  proof (hex)       = {proof.hex()}")
    print()
    print("Anyone can independently verify this, without trusting the above, by running:")
    print(f"  sharecoin_vdf_wrapper.py verify {beacon_hex} {args.iterations} {args.discriminant_bits} {y.hex()} {proof.hex()}")


def cmd_verify(args):
    challenge = bytes.fromhex(args.beacon_hex)
    y = bytes.fromhex(args.y_hex)
    proof = bytes.fromhex(args.proof_hex)
    discriminant = create_discriminant(challenge, args.discriminant_bits)
    try:
        # A tampered/malformed y or proof can fail to deserialize as a valid
        # class group element at all, rather than merely failing the
        # Wesolowski check - both cases mean "not a valid proof", not a
        # crash (confirmed by testing an actually-tampered value against a
        # real Pi-produced proof: chiavdf raises RuntimeError here instead
        # of returning False).
        ok = verify_wesolowski(str(discriminant), GENERATOR_ELEMENT, y, proof, args.iterations)
    except RuntimeError:
        ok = False
    print("VALID" if ok else "INVALID")
    sys.exit(0 if ok else 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_derive = sub.add_parser("derive", help="Call getrandombeacon and run the VDF on its output")
    p_derive.add_argument("start_height", type=int)
    p_derive.add_argument("window_size", type=int, nargs="?", default=None)
    p_derive.add_argument("--rpc-host", default=DEFAULT_RPC_HOST)
    p_derive.add_argument("--rpc-port", type=int, default=DEFAULT_RPC_PORT)
    p_derive.add_argument("--rpc-user", default=DEFAULT_RPC_USER)
    p_derive.add_argument("--rpc-password", default=None, help="or set SHARECOIN_RPC_PASSWORD")
    p_derive.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    p_derive.add_argument("--discriminant-bits", type=int, default=DEFAULT_DISCRIMINANT_BITS)
    p_derive.set_defaults(func=cmd_derive)

    p_verify = sub.add_parser("verify", help="Independently verify a derived VDF output")
    p_verify.add_argument("beacon_hex")
    p_verify.add_argument("iterations", type=int)
    p_verify.add_argument("discriminant_bits", type=int)
    p_verify.add_argument("y_hex")
    p_verify.add_argument("proof_hex")
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
