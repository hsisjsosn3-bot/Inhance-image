"""keyboards/resolution.py — Resolution selection keyboard."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import RESOLUTIONS, RESOLUTION_LABELS


def get_resolution_keyboard(current="1080p"):
    rows = []
    for key, (w, h) in RESOLUTIONS.items():
        label = "📏 " + RESOLUTION_LABELS[key] + "  (" + str(w) + "×" + str(h) + ")"
        if key == current:
            label = "✅ " + label
        rows.append([InlineKeyboardButton(label, callback_data="res_" + key)])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="action_settings")])
    return InlineKeyboardMarkup(rows)
