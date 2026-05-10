"""
REDDIT SCANNER
Read-only scan of CG/VFX-related subreddits via PRAW.

Requires: pip install praw
Keys: https://www.reddit.com/prefs/apps → create application (script)
"""

import logging
import time
from datetime import datetime, timezone, timedelta

import praw
from praw.exceptions import RedditAPIException

import config
from utils import (
    extract_contacts, detect_region, detect_role,
    is_relevant, make_record,
)

log = logging.getLogger("reddit_scanner")


def scan_subreddit(reddit: praw.Reddit, sub_name: str, cutoff: datetime) -> list[dict]:
    """Scan one subreddit (new + hot)."""
    records = []
    sub_url = f"https://reddit.com/r/{sub_name}"

    try:
        sub = reddit.subreddit(sub_name)
        log.info(f"  [r/{sub_name}] Scanning new + hot...")

        seen_ids = set()

        for feed in ("new", "hot"):
            posts = getattr(sub, feed)(limit=config.REDDIT_LIMIT)
            try:
                for post in posts:
                    if post.id in seen_ids:
                        continue
                    seen_ids.add(post.id)

                    post_date = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                    if post_date < cutoff:
                        continue

                    full_text = f"{post.title}\n{post.selftext}"
                    if not is_relevant(full_text):
                        continue

                    contacts  = extract_contacts(full_text)
                    region    = detect_region(full_text)
                    role      = detect_role(full_text)
                    date_str  = post_date.strftime("%Y-%m-%d")
                    post_url  = f"https://reddit.com{post.permalink}"

                    author_name = str(post.author) if post.author else "unknown"

                    preview = full_text[:350].replace("\n", " ").strip()
                    source_ctx = (
                        f"r/{sub_name} — post by u/{author_name}. "
                        f"Date: {date_str}. "
                        f"Title: {post.title[:100]}. "
                        f"Body: {preview}{'...' if len(full_text) > 350 else ''}"
                    )

                    company = _extract_company(post.title) or f"r/{sub_name} post"

                    rec = make_record(
                        company        = company,
                        name           = author_name,
                        role           = role,
                        region         = region,
                        email          = contacts.get("email", ""),
                        telegram       = contacts.get("telegram", ""),
                        instagram      = contacts.get("instagram", ""),
                        phone          = contacts.get("phone", ""),
                        source_platform= "Reddit",
                        source_context = source_ctx,
                        source_url     = post_url,
                        date_added     = date_str,
                        notes          = f"Reddit: r/{sub_name}, score={post.score}",
                    )
                    records.append(rec)

            except Exception as e:
                log.warning(f"  [r/{sub_name}/{feed}] Error iterating: {e}")

            time.sleep(config.REQUEST_DELAY)

    except RedditAPIException as e:
        log.error(f"  [r/{sub_name}] Reddit API error: {e}")
    except Exception as e:
        log.error(f"  [r/{sub_name}] Error: {e}")

    log.info(f"  [r/{sub_name}] Found {len(records)} relevant posts")
    return records


def _extract_company(title: str) -> str:
    """
    Heuristic: studio name from post title.
    Example: "[HIRING] Buck Studio — Senior CG Artist" → "Buck Studio"
    """
    import re
    clean = re.sub(r"\[.*?\]", "", title).strip()
    parts = re.split(r"[—\-–:|]", clean, maxsplit=1)
    candidate = parts[0].strip()
    if 2 < len(candidate) < 60:
        return candidate
    return ""


def run() -> list[dict]:
    """Entry point."""
    if not config.REDDIT_CLIENT_ID or not config.REDDIT_CLIENT_SECRET:
        log.error("Reddit API credentials not set in config.py")
        return []

    reddit = praw.Reddit(
        client_id     = config.REDDIT_CLIENT_ID,
        client_secret = config.REDDIT_CLIENT_SECRET,
        user_agent    = config.REDDIT_USER_AGENT,
        read_only     = True,
    )

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.MAX_AGE_DAYS)
    all_records = []

    log.info(f"Reddit: scanning {len(config.REDDIT_SUBREDDITS)} subreddits...")
    for sub in config.REDDIT_SUBREDDITS:
        recs = scan_subreddit(reddit, sub, cutoff)
        all_records.extend(recs)
        time.sleep(config.REQUEST_DELAY)

    log.info(f"Reddit total: {len(all_records)} records")
    return all_records


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = run()
    print(json.dumps(results, ensure_ascii=False, indent=2))
