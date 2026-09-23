#!/usr/bin/env python3
"""Simulates how much a miner can bias getrandombeacon by withholding blocks.

The beacon is SHA-256 over the mix_hash values of the blocks in the window. The miner
who finds the block that completes the window sees the finished value before deciding
whether to publish. If they dislike it they discard the block and the race restarts.

Run with no arguments to print both tables used in docs/BEACON-SPEC.md.
"""
import hashlib
import random

rng = random.Random(1)
BLOCK_TIME = 120.0


def bias_trial(window, share, want_bit=0):
    """One draw. Returns True if the attacker ends up with the bit they wanted."""
    known = b"".join(rng.randbytes(32) for _ in range(window - 1))
    while True:
        attacker_found = rng.random() < share
        bit = hashlib.sha256(known + rng.randbytes(32)).digest()[0] >> 7
        if not attacker_found:
            return bit == want_bit  # an honest miner finished the window, random result
        if bit == want_bit:
            return True  # attacker likes it and publishes
        # otherwise the attacker discards the block and the race starts again


def delay_trial(share, delay, want=0.5, machines=8):
    """Same race, but the value only becomes usable after a VDF of `delay` seconds.

    The attacker learns a candidate's value only after `delay` seconds and can use it
    only if no honest block appeared at that height in the meantime.
    """
    honest_at = rng.expovariate((1 - share) / BLOCK_TIME)
    t, found = 0.0, []
    while True:
        t += rng.expovariate(share / BLOCK_TIME)
        if t >= honest_at:
            break
        found.append(t)
    for t_found in found[:machines]:
        if t_found + delay < honest_at and rng.random() < want:
            return True
    return rng.random() < want


def rate(fn, n, *args):
    return sum(fn(*args) for _ in range(n)) / n


if __name__ == "__main__":
    print("Chance a miner with hashrate share a gets the bit it wants (fair is 0.5)")
    print("a      formula  window=1  window=8  window=100")
    for a in (0.10, 0.25, 0.33, 0.40, 0.49):
        formula = 0.5 / (1 - a * 0.5)
        row = [rate(bias_trial, 40000, w, a) for w in (1, 8, 100)]
        print("%.2f   %.4f   %.4f    %.4f    %.4f" % (a, formula, *row))
    print("\nSame miner (a=0.33) when the value only becomes usable after a delay")
    for delay in (0, 60, 300, 600):
        p = rate(delay_trial, 100000, 0.33, delay)
        print("delay %4d s: %.4f (bias left: %3.0f%% of the no-delay bias)" % (delay, p, 100 * (p - 0.5) / 0.0994))
