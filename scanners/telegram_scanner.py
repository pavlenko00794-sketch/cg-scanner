"""
TELEGRAM SCANNER
Reads public CG/VFX job channels via Telethon (official Telegram API).

Requires: pip install telethon
Keys: https://my.telegram.org → API development tools
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    UsernameNotOccupiedError,
    FloodWaitError,
)
from telethon.tl.types import Message

import config
from utils import (
    extract_contacts, detect_region, detect_role,
    is_relevant, make_record, log,
)

log = logging.getLogger("telegram_scanner")


async def scan_channel(client: TelegramClient, channel: str, cutoff: datetime) -> list[dict]:
    """Scan one channel; return matching records."""
    records = []
    try:
        entity = await client.get_entity(channel)
        channel_title = getattr(entity, "title", channel)
        channel_url = f"https://t.me/{channel}"

        log.info(f"  [{channel}] Reading up to {config.TELEGRAM_LIMIT} messages...")

        async for msg in client.iter_messages(entity, limit=config.TELEGRAM_LIMIT):
            if not isinstance(msg, Message):
                continue

            msg_date = msg.date.replace(tzinfo=timezone.utc)
            if msg_date < cutoff:
                break

            text = msg.message or ""
            if not text or len(text) < 30:
                continue

            if not is_relevant(text):
                continue

            contacts   = extract_contacts(text)
            region     = detect_region(text)
            role       = detect_role(text)
            msg_url    = f"{channel_url}/{msg.id}"
            date_str   = msg_date.strftime("%Y-%m-%d")

            first_line = text.split("\n")[0].strip()
            company = first_line[:60] if len(first_line) < 80 else channel_title

            preview = text[:400].replace("\n", " ").strip()
            source_ctx = (
                f"Channel @{channel} ({channel_title}). "
                f"Date: {date_str}. "
                f"Post: {preview}{'...' if len(text) > 400 else ''}"
            )

            rec = make_record(
                company        = company,
                role           = role,
                region         = region,
                email          = contacts.get("email", ""),
                telegram       = contacts.get("telegram", ""),
                instagram      = contacts.get("instagram", ""),
                phone          = contacts.get("phone", ""),
                source_platform= "Telegram",
                source_context = source_ctx,
                source_url     = msg_url,
                date_added     = date_str,
                notes          = f"Source channel: @{channel}",
            )
            records.append(rec)

            await asyncio.sleep(0.05)

        log.info(f"  [{channel}] Found {len(records)} relevant posts")

    except ChannelPrivateError:
        log.warning(f"  [{channel}] Private channel — skipping")
    except UsernameNotOccupiedError:
        log.warning(f"  [{channel}] Channel not found — skipping")
    except FloodWaitError as e:
        log.warning(f"  [{channel}] FloodWait {e.seconds}s — sleeping...")
        await asyncio.sleep(e.seconds + 5)
    except Exception as e:
        log.error(f"  [{channel}] Error: {e}")

    return records


async def run() -> list[dict]:
    """Entry point: scan all configured channels."""
    if not config.TELEGRAM_API_ID or not config.TELEGRAM_API_HASH:
        log.error("Telegram API credentials not set in config.py")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.MAX_AGE_DAYS)

    client = TelegramClient(
        config.TELEGRAM_SESSION,
        config.TELEGRAM_API_ID,
        config.TELEGRAM_API_HASH,
    )

    all_records = []

    async with client:
        await client.start(phone=config.TELEGRAM_PHONE)
        log.info(f"Telegram: scanning {len(config.TELEGRAM_CHANNELS)} channels...")

        for channel in config.TELEGRAM_CHANNELS:
            recs = await scan_channel(client, channel, cutoff)
            all_records.extend(recs)
            await asyncio.sleep(config.REQUEST_DELAY)

    log.info(f"Telegram total: {len(all_records)} records")
    return all_records


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = asyncio.run(run())
    print(json.dumps(results, ensure_ascii=False, indent=2))
