"""
Helpers: contact extraction from text, region/role heuristics,
deduplication, persistence.
"""

import re
import json
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

import config

log = logging.getLogger("cg_scanner")


# --- Regex patterns ---

RE_EMAIL    = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.I)
RE_TELEGRAM = re.compile(r"(?:t(?:elegram)?\.me/|@)([a-zA-Z0-9_]{5,32})", re.I)
RE_INSTAGRAM= re.compile(r"(?:instagram\.com/|insta(?:gram)?:\s*@?)([a-zA-Z0-9_.]{1,30})", re.I)
RE_PHONE    = re.compile(
    r"(?:\+?\d[\d\s\-().]{6,18}\d)"
    r"(?!\d)",
    re.I,
)
RE_URL      = re.compile(r"https?://[^\s\)\]\"'>]+", re.I)


def extract_contacts(text: str) -> dict:
    """Extract emails, social handles, phones, URLs from free text."""
    if not text:
        return {}

    emails     = list(dict.fromkeys(RE_EMAIL.findall(text)))
    telegrams  = list(dict.fromkeys(
        m for m in RE_TELEGRAM.findall(text)
        if m.lower() not in {"joinchat", "share", "username"}
    ))
    instagrams = list(dict.fromkeys(RE_INSTAGRAM.findall(text)))
    phones     = list(dict.fromkeys(
        p.strip() for p in RE_PHONE.findall(text)
        if len(re.sub(r"\D", "", p)) >= 7
    ))
    urls       = list(dict.fromkeys(RE_URL.findall(text)))

    return {
        "email":     emails[0]     if emails     else "",
        "telegram":  "@" + telegrams[0]  if telegrams  else "",
        "instagram": "@" + instagrams[0] if instagrams else "",
        "phone":     phones[0]     if phones     else "",
        "extra_emails":     emails[1:]     if len(emails)     > 1 else [],
        "extra_telegrams":  telegrams[1:]  if len(telegrams)  > 1 else [],
        "extra_urls":       urls,
    }


def detect_region(text: str) -> str:
    """Guess region from keyword hits in config.REGION_KEYWORDS."""
    lower = text.lower()
    scores = {region: 0 for region in config.REGION_KEYWORDS}
    for region, kws in config.REGION_KEYWORDS.items():
        for kw in kws:
            if kw in lower:
                scores[region] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"


def detect_role(text: str) -> str:
    """Guess role from keyword hits (includes non-English hiring terms where configured)."""
    lower = text.lower()
    role_map = {
        "Art Director":      ["art director", "арт директор", "арт-директор", "ad "],
        "CG Lead":           ["cg lead", "cg лид", "lead artist", "lead cg"],
        "Producer":          ["producer", "продюсер", "exec producer"],
        "CG Hunter":         ["cg hunter", "talent scout", "фрилансер хантер", "поиск артистов"],
        "Marketer":          ["marketer", "marketing", "маркетолог", "smm"],
        "Creative Director": ["creative director", "креативный директор", "cd "],
        "VFX Supervisor":    ["vfx supervisor", "vfx super", "визуальные эффекты"],
        "Motion Designer":   ["motion designer", "motion graphic", "моушн дизайнер"],
        "3D Artist":         ["3d artist", "3д артист", "3d generalist"],
        "Compositor":        ["compositor", "compositing", "nuke", "композитор"],
        "Animator":          ["animator", "аниматор", "character animation"],
        "Houdini Artist":    ["houdini", "fx artist", "destruction", "simulation"],
        "Event Producer":    ["event producer", "technical producer", "show director",
                              "ивент продюсер", "продюсер мероприятий"],
        "Exhibition / Spatial": [
            "exhibition designer", "spatial designer", "scenic designer",
            "музейн", "экспозици", "инсталляц", "сценограф",
        ],
        "Projection / Mapping": [
            "projection mapping", "video mapping", "3d mapping",
            "видеомэппинг", "проекционн", "mapping artist", "video designer",
        ],
        "Creative Technologist": [
            "creative technologist", "touchdesigner", "media server",
            "disguise", "pixera", "notch designer",
        ],
    }
    for role, kws in role_map.items():
        for kw in kws:
            if kw in lower:
                return role
    return "Other"


def is_relevant(text: str) -> bool:
    """True if text matches hiring/role heuristics in config."""
    lower = text.lower()
    has_hire = any(kw in lower for kw in config.KEYWORDS_HIRE)
    has_role = any(kw in lower for kw in config.KEYWORDS_ROLES)
    return has_hire or has_role


def make_record(
    *,
    company: str = "",
    name: str = "",
    role: str = "",
    region: str = "",
    email: str = "",
    instagram: str = "",
    phone: str = "",
    telegram: str = "",
    source_platform: str = "",
    source_context: str = "",
    source_url: str = "",
    notes: str = "",
    status: str = "Active",
    date_added: str = "",
) -> dict:
    """Build one normalized record dict."""
    return {
        "id":             str(uuid.uuid4())[:13],
        "company":        company.strip(),
        "name":           name.strip(),
        "role":           role or "Other",
        "region":         region or "Other",
        "email":          email.strip(),
        "instagram":      instagram.strip(),
        "phone":          phone.strip(),
        "telegram":       telegram.strip(),
        "sourcePlatform": source_platform,
        "sourceContext":  source_context.strip(),
        "sourceUrl":      source_url.strip(),
        "dateAdded":      date_added or datetime.now().strftime("%Y-%m-%d"),
        "status":         status,
        "notes":          notes.strip(),
    }


def deduplicate(records: list[dict]) -> list[dict]:
    """
    Drop duplicates by telegram, email, or (company prefix + source URL).
    """
    seen_tg    = set()
    seen_email = set()
    seen_key   = set()
    result     = []

    for r in records:
        tg    = r.get("telegram", "").lower().lstrip("@")
        email = r.get("email", "").lower()
        key   = (r.get("company", "").lower()[:30], r.get("sourceUrl", "")[:60])

        if tg and tg in seen_tg:
            continue
        if email and email in seen_email:
            continue
        if key[0] and key in seen_key:
            continue

        if tg:    seen_tg.add(tg)
        if email: seen_email.add(email)
        if key[0]: seen_key.add(key)

        result.append(r)

    return result


# --- Persistence ---

def save_json(records: list[dict], path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    log.info(f"Saved {len(records)} records → {path}")


def save_csv(records: list[dict], path: str):
    import csv
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "dateAdded", "company", "name", "role", "region",
        "email", "telegram", "instagram", "phone",
        "sourcePlatform", "sourceContext", "sourceUrl", "status", "notes",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)
    log.info(f"Saved CSV {len(records)} rows → {path}")


def merge_with_existing(new_records: list[dict], existing_path: str) -> list[dict]:
    """Prepend new rows then dedupe against existing JSON DB."""
    existing = []
    p = Path(existing_path)
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    combined = new_records + existing
    return deduplicate(combined)
