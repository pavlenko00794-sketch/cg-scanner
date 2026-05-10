"""
CG SCANNER — MAIN ORCHESTRATOR
Runs scanners, merges results, writes JSON + CSV.

Usage:
    python main.py                  # all platforms
    python main.py --telegram       # Telegram only
    python main.py --reddit         # Reddit only
    python main.py --instagram      # Instagram only
    python main.py --dry-run        # print stats only, do not save
"""

import asyncio
import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import config
from utils import deduplicate, save_json, save_csv, merge_with_existing

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/scanner.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("main")


# Output paths
OUT_DIR          = Path(config.OUTPUT_DIR)
DB_JSON          = OUT_DIR / "contacts_db.json"       # cumulative DB
LATEST_JSON      = OUT_DIR / "latest_scan.json"       # this run only
LATEST_CSV       = OUT_DIR / "latest_scan.csv"
ALL_CSV          = OUT_DIR / "contacts_all.csv"


# Scanner entrypoints

async def run_telegram() -> list[dict]:
    try:
        from scanners.telegram_scanner import run
        return await run()
    except ImportError as e:
        log.error(f"Telegram scanner import error: {e}")
        return []
    except Exception as e:
        log.error(f"Telegram scanner failed: {e}")
        return []


def run_reddit() -> list[dict]:
    try:
        from scanners.reddit_scanner import run
        return run()
    except ImportError as e:
        log.error(f"Reddit scanner import error: {e}")
        return []
    except Exception as e:
        log.error(f"Reddit scanner failed: {e}")
        return []


def run_instagram() -> list[dict]:
    try:
        from scanners.instagram_scanner import run
        return run()
    except ImportError as e:
        log.error(f"Instagram scanner import error: {e}")
        return []
    except Exception as e:
        log.error(f"Instagram scanner failed: {e}")
        return []


# Stats summary

def print_stats(records: list[dict], title: str = "Results"):
    sep = "-" * 52
    print(f"\n{sep}")
    print(f"  {title}")
    print(f"{sep}")
    print(f"  Total records:  {len(records)}")

    by_platform = {}
    by_region   = {}
    by_role     = {}
    by_status   = {}

    for r in records:
        by_platform[r.get("sourcePlatform", "?")] = by_platform.get(r.get("sourcePlatform", "?"), 0) + 1
        by_region[r.get("region", "?")]           = by_region.get(r.get("region", "?"), 0) + 1
        by_role[r.get("role", "?")]               = by_role.get(r.get("role", "?"), 0) + 1
        by_status[r.get("status", "?")]           = by_status.get(r.get("status", "?"), 0) + 1

    print(f"\n  By platform:")
    for k, v in sorted(by_platform.items(), key=lambda x: -x[1]):
        print(f"    {k:<16} {v}")

    print(f"\n  By region:")
    for k, v in sorted(by_region.items(), key=lambda x: -x[1]):
        print(f"    {k:<16} {v}")

    print(f"\n  By role (top 8):")
    for k, v in sorted(by_role.items(), key=lambda x: -x[1])[:8]:
        print(f"    {k:<24} {v}")

    print(f"{sep}\n")


# Main

async def main():
    parser = argparse.ArgumentParser(description="CG Industry Contact Scanner")
    parser.add_argument("--telegram",  action="store_true", help="Scan Telegram only")
    parser.add_argument("--reddit",    action="store_true", help="Scan Reddit only")
    parser.add_argument("--instagram", action="store_true", help="Scan Instagram only")
    parser.add_argument("--dry-run",   action="store_true", help="Don't save, just print stats")
    parser.add_argument("--fresh",     action="store_true", help="Don't merge with existing DB")
    args = parser.parse_args()

    # Default: run all scanners
    run_all = not (args.telegram or args.reddit or args.instagram)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    log.info("=" * 52)
    log.info("CG SCANNER STARTED")
    log.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info("=" * 52)

    new_records: list[dict] = []

    if run_all or args.telegram:
        log.info("\n[1/3] TELEGRAM")
        tg_records = await run_telegram()
        new_records.extend(tg_records)
        log.info(f"Telegram: +{len(tg_records)} records")

    if run_all or args.reddit:
        log.info("\n[2/3] REDDIT")
        rd_records = run_reddit()
        new_records.extend(rd_records)
        log.info(f"Reddit: +{len(rd_records)} records")

    if run_all or args.instagram:
        log.info("\n[3/3] INSTAGRAM")
        ig_records = run_instagram()
        new_records.extend(ig_records)
        log.info(f"Instagram: +{len(ig_records)} records")

    new_deduped = deduplicate(new_records)
    log.info(f"\nAfter dedup (this scan): {len(new_deduped)} unique records (removed {len(new_records) - len(new_deduped)} dupes)")

    print_stats(new_deduped, "This scan - new records")

    if args.dry_run:
        log.info("Dry run - not saving.")
        return

    save_json(new_deduped, str(LATEST_JSON))
    save_csv(new_deduped,  str(LATEST_CSV))

    if args.fresh:
        merged = new_deduped
    else:
        merged = merge_with_existing(new_deduped, str(DB_JSON))

    merged.sort(key=lambda r: r.get("dateAdded", ""), reverse=True)

    save_json(merged, str(DB_JSON))
    save_csv(merged,  str(ALL_CSV))

    print_stats(merged, "Full DB (cumulative)")

    elapsed = time.time() - t_start
    log.info(f"Done in {elapsed:.1f}s  |  DB: {len(merged)} total contacts")
    log.info(f"Files: {DB_JSON}  |  {ALL_CSV}")
    log.info("=" * 52)


if __name__ == "__main__":
    asyncio.run(main())
