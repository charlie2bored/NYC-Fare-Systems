"""Download the 1M OD-pairings CSV from a GitHub Release.

Usage:
    python scripts/download_data.py
    python scripts/download_data.py --force          # re-download even if present
    python scripts/download_data.py --url <url>      # override the default URL

The default URL points at this repo's GitHub Release asset. If you fork or
re-host the data, override with ``--url`` or the ``NYCFARE_OD_URL`` env var.

Uses only the Python standard library — no extra pip installs.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_URL = (
    "https://github.com/charlie2bored/NYC-Fare-Systems/releases/"
    "download/v1.0-data/1M_Stop_Pairings.csv.gz"
)

TARGET = Path("data/1M_Stop_Pairings.csv")
EXPECTED_SHA256 = "75732c5ce7bbb45c089f80aff7679224734b2fe27ba33a1fc267cfdf49178486"
EXPECTED_SIZE_MB = 212


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _progress(blocks: int, block_size: int, total_size: int) -> None:
    if total_size <= 0:
        return
    downloaded = min(blocks * block_size, total_size)
    pct = downloaded / total_size * 100
    bar_len = 30
    filled = int(bar_len * downloaded / total_size)
    bar = "#" * filled + "-" * (bar_len - filled)
    sys.stdout.write(
        f"\r  [{bar}] {pct:5.1f}%  "
        f"{downloaded/1e6:6.1f} / {total_size/1e6:6.1f} MB"
    )
    sys.stdout.flush()
    if downloaded == total_size:
        sys.stdout.write("\n")


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"Downloading {url}")
    try:
        urllib.request.urlretrieve(url, tmp, reporthook=_progress)
    except urllib.error.HTTPError as e:
        print(f"\nHTTP error {e.code}: {e.reason}")
        print(
            "If the release asset doesn't exist yet, create it on GitHub:\n"
            "  Releases → Draft a new release → tag v1.0-data → attach "
            "data/1M_Stop_Pairings.csv (or .csv.gz)."
        )
        raise SystemExit(1)
    if url.endswith(".gz"):
        print("Decompressing...")
        with gzip.open(tmp, "rb") as src, open(dest, "wb") as dst:
            shutil.copyfileobj(src, dst, length=1 << 20)
        tmp.unlink()
    else:
        tmp.replace(dest)


def verify(path: Path) -> bool:
    size_mb = path.stat().st_size / 1e6
    print(f"File size: {size_mb:.1f} MB (expected ~{EXPECTED_SIZE_MB} MB)")
    if abs(size_mb - EXPECTED_SIZE_MB) > 5:
        print("  WARNING: size differs from expected")
    print("Verifying SHA256...")
    actual = sha256_of(path)
    if actual == EXPECTED_SHA256:
        print(f"  OK: {actual}")
        return True
    print(f"  MISMATCH:\n    got      {actual}\n    expected {EXPECTED_SHA256}")
    return False


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--url",
        default=os.environ.get("NYCFARE_OD_URL", DEFAULT_URL),
        help="download URL (default: GitHub Release asset)",
    )
    p.add_argument("--force", action="store_true", help="re-download even if present")
    p.add_argument("--skip-verify", action="store_true")
    args = p.parse_args()

    if TARGET.exists() and not args.force:
        print(f"{TARGET} already exists. Use --force to re-download.")
        if not args.skip_verify:
            verify(TARGET)
        return

    download(args.url, TARGET)
    if not args.skip_verify:
        if not verify(TARGET):
            print("Checksum mismatch — file may be corrupt or a different version.")
            raise SystemExit(2)
    print(f"\nReady: {TARGET}")


if __name__ == "__main__":
    main()
