"""
keyboards/main_menu.py — Main enhancement keyboard + result/settings keyboards.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import QUALITY_PRESETS, RESOLUTION_LABELS

_Q_SHORT = {"low": "🟢 L", "medium": "🟡 M", "high": "🟠 H", "ultra": "🔴 U"}


def _mark(active, text):
    return ("✅ " + text) if active else text


def get_main_keyboard(user_data=None):
    """12 effects + quality/resolution/intensity rows + action row."""
    settings = (user_data or {}).get("settings", {})
    quality = settings.get("default_quality", "high")
    res = settings.get("default_resolution", "1080p")
    intensity = settings.get("intensity", 75)

    keyboard = [
        [InlineKeyboardButton("🔮 Auto Enhance", callback_data="enhance_auto"),
         InlineKeyboardButton("📐 2x Upscale", callback_data="enhance_upscale")],
        [InlineKeyboardButton("🎨 Color Boost", callback_data="enhance_color"),
         InlineKeyboardButton("💎 HDR Effect", callback_data="enhance_hdr")],
        [InlineKeyboardButton("🔲 Sharpen Pro", callback_data="enhance_sharpen"),
         InlineKeyboardButton("🌿 Denoise", callback_data="enhance_denoise")],
        [InlineKeyboardButton("💡 Brightness Fix", callback_data="enhance_brightness"),
         InlineKeyboardButton("🖼️ BG Blur", callback_data="enhance_bg_blur")],
        [InlineKeyboardButton("🎭 Cinematic", callback_data="enhance_cinematic"),
         InlineKeyboardButton("🧑 Face Enhance", callback_data="enhance_face")],
        [InlineKeyboardButton("⚫ B&W Artistic", callback_data="enhance_bw"),
         InlineKeyboardButton("🌈 Vibrance Max", callback_data="enhance_vibrance")],
        # Quality row
        [InlineKeyboardButton(_mark(quality == key, _Q_SHORT[key]),
                              callback_data="quality_" + key)
         for key in ("low", "medium", "high", "ultra")],
        # Resolution row
        [InlineKeyboardButton(_mark(res == key, "📏 " + RESOLUTION_LABELS[key]),
                              callback_data="res_" + key)
         for key in ("720p", "1080p", "2k", "4k")],
        # Intensity row
        [InlineKeyboardButton(_mark(intensity == value, str(value) + "%"),
                              callback_data="intensity_" + str(value))
         for value in (25, 50, 75, 100)],
        [InlineKeyboardButton("📥 Download Original", callback_data="action_download"),
         InlineKeyboardButton("⚙️ Settings", callback_data="action_settings")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="action_help"),
         InlineKeyboardButton("⭐ Premium", callback_data="action_premium")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_start_keyboard():
    """/start ke liye — abhi image nahi aayi."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ Help", callback_data="action_help"),
         InlineKeyboardButton("📊 My Stats", callback_data="action_stats")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="action_settings"),
         InlineKeyboardButton("⭐ Premium", callback_data="action_premium")],
    ])


def get_result_keyboard():
    """Enhanced image ke saath dikhne wale buttons."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Enhance Again", callback_data="action_again"),
         InlineKeyboardButton("🆚 Before/After", callback_data="action_compare")],
        [InlineKeyboardButton("📥 Full Quality File", callback_data="action_file"),
         InlineKeyboardButton("⭐ Rate Us", callback_data="action_rate")],
    ])


def get_settings_keyboard(user_data=None):
    settings = (user_data or {}).get("settings", {})
    watermark = settings.get("watermark", False)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Quality: " + QUALITY_PRESETS[
            settings.get("default_quality", "high")]["label"], callback_data="set_quality")],
        [InlineKeyboardButton("📏 Resolution: " + RESOLUTION_LABELS.get(
            settings.get("default_resolution", "1080p"), "1080p"), callback_data="set_res")],
        [InlineKeyboardButton("🎚️ Intensity: " + str(settings.get("intensity", 75)) + "%",
                              callback_data="set_intensity")],
        [InlineKeyboardButton("💧 Watermark: " + ("🟢 ON" if watermark else "🔴 OFF"),
                              callback_data="toggle_watermark")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu_main")],
    ])


def get_back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu_main")]
    ])
