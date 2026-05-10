# ============================================================
# TEMPLATE — copy to "config.py" and fill in your secrets.
# "config.py" is gitignored; do not commit real keys.
# ============================================================
#
# CG SCANNER — CONFIGURATION
# Fill in API keys and tune lists below.
# ============================================================

# --- TELEGRAM ---
# Keys: https://my.telegram.org → API development tools
TELEGRAM_API_ID     = 0          # numeric api_id
TELEGRAM_API_HASH   = ""         # api_hash string
TELEGRAM_PHONE      = ""         # E.164 e.g. "+79001234567"
TELEGRAM_SESSION    = "cg_scanner_session"  # Telethon session filename stem

# Public channel usernames without @
TELEGRAM_CHANNELS = [
    # RU/CIS-oriented channels
    "cg_jobs",
    "cg_freelance",
    "freelance_cg",
    "motion_jobs",
    "designjobs_ru",
    "3d_jobs",
    "vfx_jobs_ru",
    "aftereffects_jobs",
    "cgjobsrussia",
    "artjobs_ru",
    "freelance_motion",
    "motiongraphics_ru",
    "cgwork",
    "render_jobs",
    "visualdesign_jobs",
    # EN-oriented channels
    "motiongraphicsjobs",
    "vfxjobs",
    "cgarena_jobs",
    "cgfreelance",
    # Events/exhibitions — add handles you find via Telegram search:
    # "event_jobs", "design_event", "creativeproduction",
]

# Messages to fetch per channel (most recent first)
TELEGRAM_LIMIT = 200

# --- REDDIT ---
# App: https://www.reddit.com/prefs/apps (type: script)
REDDIT_CLIENT_ID     = ""
REDDIT_CLIENT_SECRET = ""
REDDIT_USER_AGENT    = "cg_scanner/1.0 by your_reddit_username"

# Subreddit names (no r/)
REDDIT_SUBREDDITS = [
    "vfx",
    "motiongraphics",
    "blender",
    "Cinema4D",
    "AfterEffects",
    "3Dmodeling",
    "gamedev",
    "forhire",
    "DesignJobs",
    "animationcareer",
    "visualeffects",
    "houdini",
    "unrealengine",
    # Events / projection / AV (often need CG or screen content)
    "projectionmapping",
    "Experientialmarketing",
    "techtheatre",
    "lightingdesign",
    "CommercialAV",
    "broadcastengineering",
]

# Posts per subreddit per feed (new + hot)
REDDIT_LIMIT = 100

# --- INSTAGRAM ---
# Prefer a dedicated account (not personal).
INSTAGRAM_USERNAME = ""
INSTAGRAM_PASSWORD = ""

INSTAGRAM_HASHTAGS = [
    "cgjobs",
    "vfxjobs",
    "motiongraphicsjobs",
    "3dartistjobs",
    "animationjobs",
    "cghire",
    "hiringartists",
    "cgartistwanted",
    "motiondesignerjobs",
    "freelancecg",
    "projectionmapping",
    "experientialevent",
    "eventproduction",
    "immersiveexperience",
    "ledwallcontent",
]

INSTAGRAM_ACCOUNTS = [
    "buck",
    "manvsmachine",
    "silasveta",
    "gmunk",
    "territory_studio",
    "framestore",
    "method_studios",
    "the_mill",
    "blur_studio",
    "psyop",
    "imaginaryforces",
    "elastic",
    "trollback",
]

INSTAGRAM_LIMIT = 30

# --- GENERAL ---
OUTPUT_DIR = "output"

# Drop posts older than this (days)
MAX_AGE_DAYS = 30

# Pause between HTTP calls (seconds)
REQUEST_DELAY = 1.5

# --- MATCHING ---
# A post is kept if any KEYWORDS_HIRE or KEYWORDS_ROLES substring matches.

KEYWORDS_HIRE = [
    # EN
    "hiring", "looking for", "we need", "seeking", "wanted",
    "open position", "job opportunity", "freelance opportunity",
    "we're looking", "join our team", "job opening",
    "need a", "need an", "looking to hire",
    "rfp", "pitch deck", "call for artists",
    # Events / exhibitions / installs / mapping (EN)
    "event production", "experiential agency", "experiential producer",
    "exhibition design", "museum installation", "trade show",
    "projection mapping", "video mapping", "3d mapping",
    "immersive installation", "interactive installation",
    "site-specific", "creative technologist", "content for led",
    "led wall", "stage visuals", "opening ceremony",
    # RU (post language)
    "ищем", "ищу", "требуется", "нужен", "нужна", "нужны",
    "вакансия", "вакансии", "набираем", "набор",
    "в команду", "присоединяйся", "открыта вакансия",
    "срочно", "фриланс задача", "ищем специалиста",
    "приглашаем", "рассматриваем кандидатов",
    # RU events / mapping
    "ивент", "ивент агентство", "ивент-агентство", "ивент продакшн",
    "организация мероприятий", "мероприятие", "выставка", "экспозиция",
    "инсталляция", "музейный проект", "офлайн проект",
    "видеомэппинг", "видео мэппинг", "проекционный мэппинг",
    "3д мэппинг", "3д маппинг", "иммерсив", "медиафасад",
    "контент для экранов", "контент для led", "мультиэкран",
    "павильон", "бренд зона", "промо зона",
]

KEYWORDS_ROLES = [
    # EN
    "art director", "cg lead", "cg artist", "motion designer",
    "motion graphic", "3d artist", "vfx artist", "vfx supervisor",
    "producer", "creative director", "generalist", "compositor",
    "houdini artist", "character animator", "rigging", "td",
    "technical director", "cg supervisor", "lighting artist",
    "texture artist", "matte painting", "concept artist",
    "environment artist", "fx artist", "nuke", "after effects",
    "cinema 4d", "c4d", "houdini", "blender", "maya",
    # Events / exhibits / mapping (EN)
    "event producer", "technical producer", "show director",
    "exhibition designer", "spatial designer", "scenic designer",
    "projection designer", "video designer", "media server",
    "touchdesigner", "notch", "disguise", "pixera",
    "creative technologist", "content designer", "screen content",
    "visual storyteller", "opening film",
    # RU (post language)
    "арт директор", "арт-директор", "cg лид", "моушн дизайнер",
    "3д артист", "3d артист", "vfx артист", "продюсер",
    "креативный директор", "аниматор", "композитор",
    "технический директор", "эффекты", "риггер",
    # RU events / content
    "ивент продюсер", "продюсер мероприятий", "шоу режиссёр",
    "шоу режиссер", "технический продакшн", "виджеер", "vj ",
    "художник по свету", "сценография", "мультиэкранный контент",
]

# Region guess from loose keyword hits in post body
REGION_KEYWORDS = {
    "CIS":  ["москва", "russia", "russian", "ukraine", "belarus", "казахстан",
             "киев", "питер", "санкт-петербург", "московск", "удалёнка", "ru",
             "spb", "msk", "снг", "cis", "минск", "almaty"],
    "EU":   ["london", "berlin", "amsterdam", "paris", "prague", "barcelona",
             "madrid", "rome", "milan", "stockholm", "copenhagen", "warsaw",
             "uk", "germany", "france", "spain", "italy", "europe", "eu",
             "netherlands", "switzerland", "austria", "belgium"],
    "USA":  ["new york", "los angeles", "san francisco", "chicago", "austin",
             "new york city", "nyc", "la", "sf", "bay area", "seattle",
             "united states", "usa", "us-based", "north america", "canada",
             "toronto", "vancouver"],
}
