<img align="left" width="72" height="72" src="docs/img/logo.svg" alt="Sharecoin logo">

# Sharecoin (SHC)

**Website**: [sharecoin.cc](https://sharecoin.cc) - block explorer and live demos.

A real fork of Bitcoin Core's C++ source, swapping the mining
proof-of-work algorithm from SHA-256d to ProgPoW/KawPow - the same
GPU-favorable, ASIC-resistant algorithm Ravencoin uses. Everything else
(transactions, scripts, wallets, P2P networking, RPC) is untouched
upstream Bitcoin Core.

The build instructions below assume Linux, the standard way to build any
Bitcoin Core fork. You don't have to build anything to use Sharecoin,
though - see the prebuilt-package callout right below, or
[docs/WINDOWS.md](docs/WINDOWS.md) for the Windows-specific path if you'd
rather use prebuilt binaries there instead.

**Just want to get mining, no cloning or building?** Grab a prebuilt
package from [Releases](https://github.com/Share-coin/sharecoin/releases/latest) -
Windows gets a portable wallet + launchers (unzip, then follow
[START-HERE.txt](START-HERE.txt)); Linux gets `sharecoind`/`sharecoin-cli`/
`sharecoin-util`/`sharecoin-qt` all in one tarball (the GUI wallet needs
Qt6 runtime libraries already installed - see the README.txt inside the
tarball for exact package names per distro).

**Want something even simpler?** [Sharecoin Simple Wallet](https://github.com/Share-coin/sharecoin-simple-wallet)
is a single portable app for casual users: open it, get a wallet, click
a button, start mining, no config files or flags involved. It bundles
its own GPU miner too, so there's nothing else to download separately.
Windows only for now.

**On Android?** [Sharecoin Android Wallet](https://github.com/Share-coin/sharecoin-android-mobile-app)
is a lightweight SPV wallet (send, receive, QR codes) for your phone -
grab the APK from that repo's Releases page.

## The pitch

Here's what almost every Bitcoin fork quietly throws away: all that GPU
compute is producing something genuinely valuable, and nobody's bothered
to use it for anything but itself. Sharecoin does.

Every ProgPoW block mined here comes with a `mix_hash` - an
unpredictable, cryptographically-earned number that costs real GPU-hours
to produce and can't be faked, front-run, or bought after the fact.
That's not exhaust. That's raw material. `getrandombeacon` turns it into
the one thing every lottery, raffle, NFT reveal, matchmaking system, and
sortition-based DAO on the internet is quietly hungry for: **randomness
nobody can rig.** No oracle to trust, no backend quietly rolling dice in
someone's data center, no vendor lock-in - just math, GPUs, and a chain
that was mining anyway. See [USECASES.md](USECASES.md) for real, runnable
demos of exactly this: raffles, committee sortition, data oracle rotation,
and delayed-reveal commitments.

Decentralization here isn't a promise baked in from day one - it's a
function of who actually shows up and mines. The mechanism doesn't care
how many nodes exist; the security guarantee does. Every independent
miner and node that joins makes the beacon harder for any single party
to bias, and every block mined spends real work turning unpredictability
into a public good instead of a corporate product. What's true right now,
already, no matter how many nodes are running: the mechanism is real,
live, and callable over RPC - not a whitepaper promise, a feature you can
query this second.

Bitcoin proved you could mine money. Sharecoin's here to prove you can
mine trust.

No premine, no founder allocation, no presale, no coins set aside for
anyone before the genesis block. Every coin in circulation is mined the
same way, by anyone with a GPU, starting from the same publicly verifiable
genesis everyone else did.

**The current chain (live since 2026-07-28) is the one that's here to
stay.** Like any young project, its early days involved genesis/consensus
changes while the network was still finding its footing, most recently a
full rebuild that replaced the previous chain outright rather than
migrating it - that phase is now over. Barring a genuinely serious bug
that leaves no other option, this is the chain to mine on, hold on, and
build on going forward.

## Contact
Forum - https://bitcointalk.org/index.php?topic=5588928

Discord - https://discord.gg/mUv7nW5rQH

Email - contact@sharecoin.cc

## Contents

- `bitcoin-source/` - the patched Bitcoin Core source tree, builds the
  same way upstream does (`bitcoin-source/doc/build-*.md`).
- `generate_wallet.py` - standalone offline wallet/keypair generator,
  pure Python, works on any OS.
- `patch_*.py` - a literal, file-by-file record of every change from
  upstream Bitcoin Core - not required reading to just use this, see
  `docs/DETAILS.md` if you want to audit or re-derive the diff.
- `wallet/` - prebuilt Windows binaries and `.bat` launcher scripts, see
  `docs/WINDOWS.md` - not needed on Linux.
- `demos/` - standalone scripts built on the randomness beacon (raffles,
  committee sortition, data oracle rotation, delayed-reveal commitments), see
  `USECASES.md`.
- `START-HERE.txt` - plain-language quick-start for anyone using the
  prebuilt Windows package from Releases, not building from source.
- `WHITEPAPER.pdf` - formal writeup of the protocol, threat model, and
  the randomness beacon's design.

Real GPU mining software (kawpowminer etc.) isn't part of this source
tree - see "Mining" below. The prebuilt Windows portable package (see
Releases) does bundle it directly, under its own separate license.

## Building

Build `bitcoin-source/` the same way you'd build upstream Bitcoin Core -
standard CMake + vcpkg or system deps, see `bitcoin-source/doc/build-*.md`.
The resulting binaries are named `sharecoind`, `sharecoin-cli`,
`sharecoin-qt` (with `BUILD_GUI=ON`), etc. - same build, same flags, as
any Bitcoin Core fork, just renamed and running ProgPoW/KawPow instead of
SHA-256d.

**Don't pass `-regtest`.** The live Sharecoin network is this fork's own
real mainnet (`CMainParams`) - its own genesis, its own consensus rules,
mined with ProgPoW/KawPow from block 1, distinct from real Bitcoin's
mainnet. Running plain `sharecoind` with no network flag connects to it
correctly. `-regtest` switches to a separate, incompatible test chain
("sharenet") used only for local development - a wallet or node started
with `-regtest` will not see the live network, the live balance, or the
live peers, and will silently sync a dead fork instead. Every command in
this README and in `docs/` already omits it; if you're adapting a command
from an older version of this doc or from memory, don't add it back in.

## Getting a wallet address

Run `generate_wallet.py` (`pip install base58 pycryptodome ecdsa` - on
modern Debian/Ubuntu, add `--break-system-packages` to that command, or
use a venv, or it'll fail with an "externally-managed-environment"
error) to generate a real secp256k1 keypair entirely offline - no node or
wallet software required. **Keep the printed private key secret and
backed up** - there's no recovery if it's lost.

If you built `sharecoin-qt`, it works like any Bitcoin-Qt build: create a
wallet, then use the **Receive** tab to generate an address directly (or
import the key generated above instead - see `docs/DETAILS.md` for the
exact console commands).

**On Windows**, you don't need to build anything to get a wallet: run
`wallet/start-wallet.bat` (launches the prebuilt `sharecoin-qt.exe`). On
first run it prompts you to create a wallet - accept the defaults. Once
it's open, go to the **Receive** tab and click **Create new receiving
address**. That's it - the wallet holds the private key for you,
encrypted if you set a passphrase when creating it (**Settings → Encrypt
Wallet**, recommended before receiving anything real). See
[docs/WINDOWS.md](docs/WINDOWS.md) for the rest of the Windows path
(mining, running your own node).

## Mining

**You need real GPU mining software - this source tree does not include
it.** Sharecoin's own binaries (`sharecoind`/`sharecoin-qt`) validate and
relay blocks, but the actual GPU proof-of-work computation only happens
inside a separate KawPow-capable miner - **kawpowminer** (the same one
Ravencoin uses) is the one this fork has actually been tested against.

**The Windows portable package (see Releases) bundles kawpowminer
directly**, in `kawpowminer-windows-1.2.4/`, so `start-mining.bat` works
out of the box with no separate download. This is the official,
unmodified [RavenCommunity/kawpowminer](https://github.com/RavenCommunity/kawpowminer)
v1.2.4 Windows CUDA build, GPLv3-licensed - a separate project under its
own license, not Sharecoin's own code, bundled alongside it rather than
combined into it (see the `NOTICE.txt` in that folder for the exact
license/source details). If you're building from source or on Linux,
download kawpowminer yourself instead, same as before.

**Download the current wallet release and let it fully sync before you
mine a single block.** An older wallet build is not just outdated, it
can be built against a genesis/chain from before a past network change -
that old chain is no longer valid on this network at all, so mining
against it earns nothing no matter how much GPU time you put in. Get the
latest build from this repo's own Releases page, and don't skip the sync
step above just because the wallet opens and looks normal - a stale
build can look like it's running fine while quietly following a dead
fork.

**Wait for your node to finish syncing before you trust anything it tells
you or start mining against it.** A node still catching up to the real
chain tip shows an incomplete balance and missing transactions, and if
you're pointing a miner at your own node rather than a pool, it'll hand
out mining work built on a stale, outdated chain tip - blocks found
against that work can never be accepted by the real network, so it's
wasted GPU-hours for zero reward, not just an inconvenience. **This
applies just as much to a brand-new wallet/address you're about to mine
to** - create it and let the node reach a confirmed sync state first,
rather than generating an address and pointing a miner at it in the same
breath. Check with:

```
sharecoin-cli getblockchaininfo
```

and confirm `"initialblockdownload"` is `false` and `"blocks"` equals
`"headers"`. Until both of those are true, whatever the wallet shows you
isn't the real picture yet.

**Your mining rewards land on the real chain regardless of what your
miner is pointed at** - `kawpowminer` just hashes whatever work the pool
hands it, it doesn't care about chain history. But if you separately run
your *own* wallet/node to check or spend that balance, make sure it's
actually connecting to the current network (`sharecoin.duckdns.org:8443`/
`10000`) rather than an old address left over from a past network
migration - an outdated wallet pointed at a retired endpoint won't just
fail to connect, it can also carry a stale genesis and quietly sync a
long-dead fork instead, showing a permanently-zero balance even though
your real rewards are sitting fine on the actual live chain.

Get it from [RavenCommunity/kawpowminer's GitHub Releases](https://github.com/RavenCommunity/kawpowminer/releases)
(Linux: Ubuntu 18/20 builds, CUDA or OpenCL) - verify its published
`.sha256sum` against the download, then point it at a live Sharecoin
network:

```
./kawpowminer -P stratum+tcp://YOUR_ADDRESS.worker1@sharecoin.duckdns.org:10000 --cu-schedule spin --cu-parallel-hash 8 --cu-streams 4 --display-interval 2
```

There's automatic failover behind this address, so you don't need to do
anything or change any address if the machine currently serving it goes
down; miner software just reconnects on its own within well under a
minute. See `docs/DETAILS.md` for how that works.

See `docs/DETAILS.md` for running your own node/network/Stratum proxy
instead of joining that one, and GPU batch-size quirks at low difficulty.

## Randomness beacon

`getrandombeacon start_height (window_size)` is a public, verifiable
randomness source derived from already-confirmed blocks, designed to
resist the "last revealer" bias that a single block's own `mix_hash`
would have. See `docs/DETAILS.md` for the full design rationale, or
[WHITEPAPER.pdf](WHITEPAPER.pdf) for the formal writeup.

**Blockchain Explorer** - https://sharecoin.cc/explorer/

## Use cases

The beacon is the basis for a handful of real, runnable demos: lotteries
and raffles, committee/jury sortition, data oracle rotation, and
delayed-reveal commitments. See [USECASES.md](USECASES.md) for what each
one does and a real-world scenario it fits, and [`demos/`](demos/) for the
scripts themselves.

**Live demos**: [sharecoin.cc](https://sharecoin.cc) is the hub for all six
web demos (raffle, roulette, random draw, audit draw, fair queue, sealed
bid) plus the explorer. Each one runs against the live network - lock
something in, pick a future block height, and watch it settle from that
block's actual beacon value once it's mined. Anyone can verify the result
themselves from the numbers shown on the page.

**Beyond demos - real payouts**: [sharecoin.cc/daily-raffle](https://sharecoin.cc/daily-raffle/)
pays a real 1 SHC to a real winner every day at 12:00 UTC, no signup - enter your address once
and you're eligible for every draw for 30 days. There's also a Discord bot (`/raffle create` for
a self-serve join-by-button raffle, `/raffle manual` for a pre-collected address list) that runs
the same verifiable draw inside any server and pays winners directly from a dedicated prize
wallet, same beacon mechanic, same "nobody can know the result early" guarantee as everything
else here.

## License

MIT, see [LICENSE](LICENSE). Bitcoin Core's own copyright is preserved
throughout, as its license requires, alongside this fork's own changes.

## Known limitations

See `docs/DETAILS.md`.
