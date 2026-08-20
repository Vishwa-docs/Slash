#!/usr/bin/env python3
"""Bring up the Slash product (API + React UI) from one process.

Usage:  python scripts/serve.py [--port 8501] [--host 127.0.0.1] [--lens supply-chain|fraud]
Before first run: `npm --prefix assets/app install && npm --prefix assets/app run build`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.api import make_server
from src.hydradb_client import HydraDBClient
from src.lens import lens_by_id


def main() -> int:
    ap = argparse.ArgumentParser(description="Slash product server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8501)
    ap.add_argument(
        "--lens",
        choices=["supply-chain", "fraud"],
        default="supply-chain",
        help="graph lens to serve (default: dependency-graph)",
    )
    args = ap.parse_args()

    lens = lens_by_id(args.lens)
    client = HydraDBClient()
    server = make_server(client, host=args.host, port=args.port, lens=lens)
    print("  _   _           _     _   ")
    print(" | | | | __ _ ___| |__ | |_ ")
    print(" | |_| |/ _` / __| '_ \\| __| dependency console on GitHub + npm + OSV data")
    print(" |  _  | (_| \\__ \\ | | | |_ ")
    print(" |_| |_|\\__,_|___/_| |_|\\__| on HydraDB")
    print(
        f"\n  lens: {lens.title}   http://{args.host}:{server.server_address[1]}   (Ctrl-C to stop)"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  bye.")
    finally:
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
