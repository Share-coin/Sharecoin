SHARECOIN (SHC) - LINUX PREBUILT BINARIES
===========================================

Includes both the CLI daemon and the graphical wallet:
sharecoind, sharecoin-cli, sharecoin-util, sharecoin-qt.

sharecoin-qt needs Qt6 runtime libraries already installed on your
system (not statically bundled here):

    Debian/Ubuntu:  sudo apt install qt6-base-dev qt6-wayland libqrencode-dev
    Fedora:         sudo dnf install qt6-qtbase qt6-qtwayland qrencode
    Arch:           sudo pacman -S qt6-base qt6-wayland qrencode

(only the runtime libraries are strictly needed to *run* it, not the
full -dev/build packages above, but those are the simplest one-liners
that also cover it.) sharecoind/sharecoin-cli/sharecoin-util have no
such requirement - they run standalone.


QUICK START - JUST WANT A WALLET?
------------------------------------
Run:

    ./start-wallet.sh

That's it - it launches sharecoin-qt with the right flags already set
(connected to the live network, pruned to keep disk use small, a
sensible fallback fee), using a "datadir" folder right next to the
script so it doesn't touch your home directory. No need to read any
further unless you want the CLI daemon instead, or want to understand
what the script is doing under the hood - see its own comments for that.


DON'T PASS -regtest
--------------------
The live Sharecoin network is this fork's own real mainnet - its own
genesis, its own consensus rules, distinct from real Bitcoin's mainnet.
Running plain sharecoind (or sharecoin-qt) with no network flag connects
to it correctly. -regtest switches to a separate, incompatible test chain
used only for local development - a node started with -regtest will not
see the live network, the live balance, or the live peers, and will
silently sync a dead fork instead.

Example (CLI):

    ./sharecoind -daemon
    ./sharecoin-cli getblockchaininfo
    ./sharecoin-cli -addnode=sharecoin.duckdns.org:8443 -listen=0

Example (GUI wallet):

    ./sharecoin-qt -addnode=sharecoin.duckdns.org:8443 -fallbackfee=0.0001

On first run, sharecoin-qt may show a one-time disk-space notice -
just click OK, it's informational only and not a problem.


CONNECTING TO THE LIVE NETWORK
--------------------------------
    ./sharecoind -addnode=sharecoin.duckdns.org:8443 -listen=0 -fallbackfee=0.0001 -daemon

A freshly built/downloaded sharecoind with no flags at all also finds
the live network on its own via a compiled-in DNS seed - the explicit
-addnode above just gives it one known-good peer right away in addition
to whatever the seed finds, rather than restricting it to just one peer.
Use -addnode, not -connect - -connect is exclusive and disables normal
peer discovery, leaving the node with exactly one peer and no fallback
if that one node ever has a rough patch.

Once running, use sharecoin-cli the same way as any Bitcoin Core node
(getbalance, getnewaddress, sendtoaddress, etc.) - or use sharecoin-qt's
own Receive tab to generate an address - see this repo's README.md and
docs/ for the full RPC surface, including the getrandombeacon randomness
beacon this fork adds.

Prefer generating a key offline instead? generate_wallet.py
(pip install base58 pycryptodome ecdsa - on modern Debian/Ubuntu, add
--break-system-packages to that command, or use a venv, or it'll fail
with an "externally-managed-environment" error) works the same as on
any other OS; see docs/DETAILS.md for how to import a key generated
this way into the Qt wallet.


MINING
-------
This package doesn't include a GPU miner. Grab kawpowminer from:

    https://github.com/RavenCommunity/kawpowminer/releases

Get the native Linux build for your distro (kawpowminer-ubuntu20-cuda11
or kawpowminer-ubuntu20-opencl as of writing, or the ubuntu18 builds for
older systems) - the Windows build is a Windows executable and won't run
on a real Linux system (it may appear to run under WSL specifically,
since WSL transparently forwards .exe execution to the Windows host, but
that's a WSL-only quirk, not something that works on an actual Linux
machine, VPS, or Docker container). Verify the published .sha256sum,
then point it at:

    stratum+tcp://<your-address>.<worker-name>@sharecoin.duckdns.org:10000

If you get an error like "error while loading shared libraries:
libnvrtc.so.X.X: cannot open shared object file", your system's CUDA
runtime doesn't match the exact version the CUDA build was compiled
against - either install that specific CUDA toolkit version, or try the
OpenCL build instead. If the OpenCL build reports "No OpenCL platforms
found", your GPU driver package doesn't have OpenCL support installed -
on Ubuntu/Debian this usually means installing your NVIDIA/AMD vendor's
OpenCL ICD package alongside the regular driver (already included in a
normal desktop driver install; missing GPU-passthrough setups like WSL
may need it added separately).


Full source, docs, and the beacon spec: github.com/Share-coin/sharecoin
