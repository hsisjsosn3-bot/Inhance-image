"""keyboards/intensity.py — Effect intensity slider."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

LEVELS = (25, 50, 75, 100)


def get_intensity_keyboard(current=75):
    row = []
    for value in LEVELS:
        label = str(value) + "%"
        if value == current:
            label = "✅ " + label
        row.append(InlineKeyboardButton(label, callback_data="intensity_" + str(value)))
    return InlineKeyboardMarkup([
        row,
        [InlineKeyboardButton("⬅️ Back", callback_data="action_settings")],
    ])
