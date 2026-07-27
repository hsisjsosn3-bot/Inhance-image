"""
config.py — Saare constants aur environment variables (single source of truth).
Sirf yahan values change karo, poore project mein reflect ho jayega.
"""
import os

# --- Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
BOT_NAME = os.getenv("BOT_NAME", "Image Enhancer Pro")
BOT_USERNAME = os.getenv("BOT_USERNAME", "@YourBotName")
VERSION = "1.0.0"

# --- Server (Render health check) ---
PORT = int(os.getenv("PORT", "10000"))

# --- Storage ---
DB_PATH = os.getenv("DB_PATH", "data/users.json")

# --- Limits / safety ---
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "3"))
MAX_PHOTO_BYTES = 9_000_000          # Telegram photo upload limit ke andar
MAX_DOCUMENT_BYTES = 45_000_000      # Document limit (50MB) ke andar
DAILY_LIMIT_FREE = int(os.getenv("DAILY_LIMIT_FREE", "40"))
WATERMARK_DEFAULT = os.getenv("WATERMARK", "0") == "1"

# --- Quality presets ---
# max_pixels = processing se pehle image ko is size tak limit karenge (speed ke liye)
QUALITY_PRESETS = {
    "low":    {"label": "🟢 LOW",    "jpeg_quality": 80, "max_pixels": 2_000_000},
    "medium": {"label": "🟡 MEDIUM", "jpeg_quality": 88, "max_pixels": 4_000_000},
    "high":   {"label": "🟠 HIGH",   "jpeg_quality": 93, "max_pixels": 8_000_000},
    "ultra":  {"label": "🔴 ULTRA",  "jpeg_quality": 97, "max_pixels": 12_000_000},
}
QUALITY_ORDER = ["low", "medium", "high", "ultra"]

# --- Resolution presets ---
RESOLUTIONS = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}
RESOLUTION_LABELS = {"720p": "720p", "1080p": "1080p", "2k": "2K", "4k": "4K"}

# --- Default per-user settings ---
DEFAULT_SETTINGS = {
    "default_quality": "high",
    "default_resolution": "1080p",
    "intensity": 75,
    "auto_enhance": True,
    "watermark": WATERMARK_DEFAULT,
}
