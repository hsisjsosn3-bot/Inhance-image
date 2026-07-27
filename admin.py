"""
handlers/admin.py — Admin-only commands: /broadcast, /botstats, /grantpremium
ADMIN_ID environment variable set hona zaruri hai.
"""
import asyncio
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import database as db
from config import ADMIN_ID
from utils.fonts import bold, mono

log = logging.getLogger(__name__)


def _is_admin(update):
    return ADMIN_ID and update.effective_user and update.effective_user.id == ADMIN_ID


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/broadcast <message> — sab users ko message."""
    if not _is_admin(update):
        return
    text = " ".join(context.args or []).strip()
    if not text:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    ids = db.all_user_ids()
    sent = failed = 0
    status = await update.message.reply_text("📢 Broadcasting to " + str(len(ids)) + " users...")
    for user_id in ids:
        try:
            await context.bot.send_message(user_id, "📢 " + bold("Announcement") + "\n\n" + text,
                                           parse_mode=ParseMode.HTML)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)          # flood limits se bachne ke liye
    await status.edit_text("✅ Sent: " + str(sent) + " | ❌ Failed: " + str(failed))


async def bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/botstats — global stats (admin only)."""
    if not _is_admin(update):
        return
    s = db.global_stats()
    await update.message.reply_text(
        "📊 " + bold("Bot Stats") + "\n\n"
        "👥 Users: " + mono(str(s["users"])) + "\n"
        "🟢 Active today: " + mono(str(s["today_active"])) + "\n"
        "🖼️ Images: " + mono(str(s["images"])) + "\n"
        "⭐ Premium: " + mono(str(s["premium"])) + "\n"
        "🔥 Top effect: " + s["top_effect"] + "\n"
        "💬 Feedback: " + mono(str(s["feedback"])),
        parse_mode=ParseMode.HTML,
    )


async def grant_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/grantpremium <user_id> [off]"""
    if not _is_admin(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Usage: /grantpremium <user_id> [off]")
        return
    try:
        target = int(args[0])
    except ValueError:
        await update.message.reply_text("user_id number hona chahiye.")
        return
    value = not (len(args) > 1 and args[1].lower() in ("off", "0", "false"))
    db.set_premium(target, value)
    await update.message.reply_text(
        "✅ User " + str(target) + " premium = " + str(value))
    try:
        await context.bot.send_message(
            target, "⭐ Aapka Premium " + ("activate" if value else "deactivate") + " ho gaya hai!")
    except Exception:
        pass
