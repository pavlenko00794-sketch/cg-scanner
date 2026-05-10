"""
SCHEDULER — run the scanner on a fixed interval.

Runs main.py every N hours and logs results.
Example background run (Unix): nohup python scheduler.py &

Alternatively use cron, e.g.:
    0 9,21 * * *  cd /path/to/cg-scanner && python main.py >> logs/cron.log 2>&1
"""

import asyncio
import logging
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Schedule settings
INTERVAL_HOURS  = 12        # hours between runs
MAX_RUNS        = None      # None = infinite; or e.g. 10
NOTIFY_TELEGRAM = False     # True = send Telegram summary after each run
NOTIFY_CHAT_ID  = ""        # Telegram chat_id for notifications
NOTIFY_BOT_TOKEN= ""        # Bot token from @BotFather

# Logger
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/scheduler.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("scheduler")


def send_telegram_notification(text: str):
    """Send a notification via Telegram Bot API."""
    if not NOTIFY_TELEGRAM or not NOTIFY_BOT_TOKEN or not NOTIFY_CHAT_ID:
        return
    try:
        import urllib.request, urllib.parse, json
        url = f"https://api.telegram.org/bot{NOTIFY_BOT_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": NOTIFY_CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log.warning(f"Telegram notification failed: {e}")


def run_scan() -> dict:
    """Run main.py as a subprocess; return a small result dict."""
    t0 = time.time()
    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    elapsed = time.time() - t0

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    run_log = Path(f"logs/run_{ts}.log")
    run_log.write_text(stdout + "\n" + stderr, encoding="utf-8")

    total = 0
    for line in stdout.split("\n"):
        if "total contacts" in line.lower():
            try:
                total = int([t for t in line.split() if t.isdigit()][-1])
            except Exception:
                pass

    return {
        "ok":      result.returncode == 0,
        "elapsed": elapsed,
        "total":   total,
        "log":     str(run_log),
    }


def main():
    interval_sec = INTERVAL_HOURS * 3600
    run_count    = 0

    log.info(f"Scheduler started. Interval: every {INTERVAL_HOURS}h. Max runs: {MAX_RUNS or '∞'}")
    log.info("Press Ctrl+C to stop.")

    while True:
        run_count += 1
        if MAX_RUNS and run_count > MAX_RUNS:
            log.info(f"Reached max runs ({MAX_RUNS}). Stopping.")
            break

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        log.info(f"\n{'-' * 48}")
        log.info(f"Run #{run_count} started at {now}")
        log.info(f"{'-' * 48}")

        res = run_scan()

        status = "OK" if res["ok"] else "ERROR"
        msg = (
            f"<b>CG Scanner run #{run_count}</b>\n"
            f"{status} | {res['elapsed']:.0f}s | DB: {res['total']} contacts\n"
            f"Log: {res['log']}"
        )
        log.info(f"Run #{run_count} done: {status}, {res['elapsed']:.1f}s, DB={res['total']} contacts")
        send_telegram_notification(msg)

        next_run = datetime.fromtimestamp(time.time() + interval_sec).strftime("%Y-%m-%d %H:%M")
        log.info(f"Next run at: {next_run}")
        time.sleep(interval_sec)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Scheduler stopped by user.")
