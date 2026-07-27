"""keyboards/quality.py — Quality selection keyboard."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import QUALITY_PRESETS, QUALITY_ORDER

DESCRIPTIONS = {
    "low": "Fast",
    "medium": "Balanced",
    "high": "Detailed",
    "ultra": "Maximum",
}


def get_quality_keyboard(current="high"):
    rows = []
    for key in QUALITY_ORDER:
        label = QUALITY_PRESETS[key]["label"] + " (" + DESCRIPTIONS[key] + ")"
        if key == current:
            label = "✅ " + label
        rows.append([InlineKeyboardButton(label, callback_data="quality_" + key)])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="action_settings")])
    return InlineKeyboardMarkup(rows)
