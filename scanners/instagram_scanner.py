"""
INSTAGRAM SCANNER
Optional: hashtags and studio accounts via instagrapi.

Requires: pip install instagrapi
Use a dedicated Instagram account (not your primary). Respect rate limits.
"""

import logging
import time
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    BadPassword,
    RateLimitError,
    UserNotFound,
)

import config
from utils import (
    extract_contacts, detect_region, detect_role,
    is_relevant, make_record,
)

log = logging.getLogger("instagram_scanner")

SESSION_FILE = "output/instagram_session.json"


def get_client() -> Client | None:
    """Build and log in Instagram client."""
    if not config.INSTAGRAM_USERNAME or not config.INSTAGRAM_PASSWORD:
        log.error("Instagram credentials not set in config.py")
        return None

    cl = Client()
    cl.delay_range = [2, 5]

    session_path = Path(SESSION_FILE)
    if session_path.exists():
        try:
            cl.load_settings(session_path)
            cl.login(config.INSTAGRAM_USERNAME, config.INSTAGRAM_PASSWORD)
            log.info("Instagram: session restored from file")
            return cl
        except Exception:
            log.info("Instagram: saved session expired, re-logging...")

    try:
        cl.login(config.INSTAGRAM_USERNAME, config.INSTAGRAM_PASSWORD)
        cl.dump_settings(session_path)
        log.info("Instagram: logged in successfully")
        return cl
    except BadPassword:
        log.error("Instagram: wrong password")
    except ChallengeRequired:
        log.error("Instagram: challenge required — verify your account in the app first")
    except Exception as e:
        log.error(f"Instagram: login error: {e}")

    return None


def _post_to_record(cl: Client, media, platform_context: str) -> dict | None:
    """Map one media item to a DB record."""
    try:
        caption    = media.caption_text or ""
        if not is_relevant(caption):
            return None

        contacts   = extract_contacts(caption)
        region     = detect_region(caption)
        role       = detect_role(caption)

        try:
            user_info  = cl.user_info(media.user.pk)
            bio        = user_info.biography or ""
            bio_contacts = extract_contacts(bio)
            username   = user_info.username
            full_name  = user_info.full_name or ""
            email    = bio_contacts.get("email") or contacts.get("email", "")
            telegram = bio_contacts.get("telegram") or contacts.get("telegram", "")
            phone    = bio_contacts.get("phone") or contacts.get("phone", "")
        except Exception:
            username = getattr(media.user, "username", "")
            full_name = ""
            email    = contacts.get("email", "")
            telegram = contacts.get("telegram", "")
            phone    = contacts.get("phone", "")

        post_date = media.taken_at.replace(tzinfo=timezone.utc) if media.taken_at else datetime.now(timezone.utc)
        date_str  = post_date.strftime("%Y-%m-%d")
        post_url  = f"https://instagram.com/p/{media.code}/" if hasattr(media, "code") else ""

        preview = caption[:350].replace("\n", " ").strip()
        source_ctx = (
            f"{platform_context}. "
            f"Account @{username}. "
            f"Date: {date_str}. "
            f"Post: {preview}{'...' if len(caption) > 350 else ''}"
        )

        return make_record(
            company        = full_name or username,
            name           = full_name,
            role           = role,
            region         = region,
            email          = email,
            telegram       = telegram,
            instagram      = f"@{username}",
            phone          = phone,
            source_platform= "Instagram",
            source_context = source_ctx,
            source_url     = post_url,
            date_added     = date_str,
            notes          = f"Instagram: @{username}",
        )
    except Exception as e:
        log.warning(f"  Post conversion error: {e}")
        return None


def scan_hashtags(cl: Client, cutoff: datetime) -> list[dict]:
    """Scan configured hashtags."""
    records = []
    log.info(f"  Instagram hashtags: scanning {len(config.INSTAGRAM_HASHTAGS)}...")

    for tag in config.INSTAGRAM_HASHTAGS:
        try:
            medias = cl.hashtag_medias_recent(tag, amount=config.INSTAGRAM_LIMIT)
            count = 0
            for media in medias:
                post_date = media.taken_at.replace(tzinfo=timezone.utc) if media.taken_at else datetime.now(timezone.utc)
                if post_date < cutoff:
                    continue
                rec = _post_to_record(cl, media, f"Hashtag #{tag}")
                if rec:
                    records.append(rec)
                    count += 1
                time.sleep(config.REQUEST_DELAY)

            log.info(f"    #{tag}: {count} relevant posts")
        except RateLimitError:
            log.warning(f"    #{tag}: rate limited — sleeping 60s")
            time.sleep(60)
        except Exception as e:
            log.warning(f"    #{tag}: {e}")
        time.sleep(config.REQUEST_DELAY * 2)

    return records


def scan_accounts(cl: Client, cutoff: datetime) -> list[dict]:
    """Scan configured studio/account usernames."""
    records = []
    log.info(f"  Instagram accounts: scanning {len(config.INSTAGRAM_ACCOUNTS)}...")

    for username in config.INSTAGRAM_ACCOUNTS:
        try:
            user_id = cl.user_id_from_username(username)
            medias  = cl.user_medias(user_id, amount=config.INSTAGRAM_LIMIT)
            count   = 0
            for media in medias:
                post_date = media.taken_at.replace(tzinfo=timezone.utc) if media.taken_at else datetime.now(timezone.utc)
                if post_date < cutoff:
                    continue
                rec = _post_to_record(cl, media, f"Studio account @{username}")
                if rec:
                    records.append(rec)
                    count += 1
                time.sleep(config.REQUEST_DELAY)

            log.info(f"    @{username}: {count} relevant posts")
        except UserNotFound:
            log.warning(f"    @{username}: not found")
        except RateLimitError:
            log.warning(f"    @{username}: rate limited — sleeping 60s")
            time.sleep(60)
        except Exception as e:
            log.warning(f"    @{username}: {e}")
        time.sleep(config.REQUEST_DELAY * 2)

    return records


def run() -> list[dict]:
    """Entry point."""
    cl = get_client()
    if not cl:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.MAX_AGE_DAYS)
    all_records = []

    log.info("Instagram: starting scan...")
    all_records.extend(scan_hashtags(cl, cutoff))
    all_records.extend(scan_accounts(cl, cutoff))

    log.info(f"Instagram total: {len(all_records)} records")
    return all_records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = run()
    print(json.dumps(results, ensure_ascii=False, indent=2))
