import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Chat IDs
SEARCH_CHAT = int(os.environ.get("SEARCH_CHAT", "0"))
FILES_CHANNEL = int(os.environ.get("FILES_CHANNEL", "0"))

# Admin System
ADMIN_IDS = [int(i) for i in os.environ.get("ADMIN_IDS", "").split(",") if i]

# TMDB
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")

# Watermark
WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "PratapCinema2026")

# Invisible Characters (U+200B = Zero Width Space)
def get_invisible_watermark(text):
    # This creates a "fingerprint" using zero-width characters
    return "".join(["\u200b" if c == " " else c + "\u200c" for c in text])

INVISIBLE_WATERMARK = get_invisible_watermark(WATERMARK_TEXT)
