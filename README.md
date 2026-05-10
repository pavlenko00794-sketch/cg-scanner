# CG Scanner — Setup Guide

Read-only monitoring for public hiring signals in CGI/VFX/motion-design spaces  
(Telegram channels, Reddit subreddits, optional Instagram).

---

## Project layout

```
cg-scanner/
├── main.py
├── scheduler.py
├── config.example.py       # template — copy to config.py
├── config.py               # secrets (local only; gitignored)
├── utils.py
├── requirements.txt
├── scanners/
│   ├── telegram_scanner.py
│   ├── reddit_scanner.py
│   └── instagram_scanner.py
├── output/
└── logs/
```

---

## Quick start

```bash
pip install -r requirements.txt
copy config.example.py config.py    # Windows; macOS/Linux: cp config.example.py config.py
# Edit config.py with your API keys
python main.py
```

`config.py` is not committed (see `.gitignore`). Use `config.example.py` on GitHub only.

---

## Telegram API

1. https://my.telegram.org → API development tools  
2. Create an app; copy **api_id** and **api_hash** into `config.py`  
3. Set `TELEGRAM_PHONE` in international format (e.g. `+79001234567`)

First run may ask for an SMS/code login code. A `.session` file is created for later runs.

---

## Reddit API

1. https://www.reddit.com/prefs/apps (or old.reddit.com/prefs/apps)  
2. Create application, type **script**  
3. Set redirect URI e.g. `http://localhost:8080`  
4. Copy **client id** and **secret** into `config.py`; set `REDDIT_USER_AGENT` (include your Reddit username)

---

## Instagram (optional)

Use a **dedicated** Instagram account, not your main profile. Credentials go in `config.py`. First login may require in-app verification.

---

## Commands

```bash
python main.py                  # all sources enabled in config
python main.py --telegram
python main.py --reddit
python main.py --instagram
python main.py --dry-run        # no write to disk
```

---

## Scheduler

Run `scheduler.py` or use cron / Windows Task Scheduler to call `main.py` on an interval. Optional Telegram bot notifications can be configured at the top of `scheduler.py`.

---

## Output

| File | Purpose |
|------|---------|
| `output/contacts_db.json` | Merged database |
| `output/contacts_all.csv` | Same data as CSV |
| `output/latest_scan.json` | Last run only |
| `output/latest_scan.csv` | Last run CSV |

---

## Tips

- Keep `REQUEST_DELAY` ≥ 1s to reduce rate-limit risk.  
- Add or remove channels/subreddits in `config.py` as needed.  
- Do not commit real secrets; use `config.example.py` as the public template.
