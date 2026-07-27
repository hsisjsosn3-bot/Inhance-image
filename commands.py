"""
handlers/commands.py — /start, /help, /settings, /stats, /premium, /feedback, /about
plus plain-text fallback aur global error handler.
"""
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import database as db
from config import ADMIN_ID
from keyboards.main_menu import (get_back_keyboard, get_settings_keyboard,
                                 get_start_keyboard)
from utils import formatter as fmt

log = logging.getLogger(__name__)


def _user_record(update):
    u = update.effective_user
    return db.get_user(u.id, u.username, u.first_name)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = _user_record(update)
    log.info("/start by %s (%s)", update.effective_user.id, update.effective_user.username)
    await update.message.reply_text(
        fmt.welcome(update.effective_user.first_name, user),
        reply_markup=get_start_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _user_record(update)
    await update.message.reply_text(
        fmt.help_text(), reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML
    )


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = _user_record(update)
    await update.message.reply_text(
        fmt.settings_text(user), reply_markup=get_settings_keyboard(user),
        parse_mode=ParseMode.HTML,
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = _user_record(update)
    await update.message.reply_text(
        fmt.stats_text(user), reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML
    )


async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = _user_record(update)
    await update.message.reply_text(
        fmt.premium_text(user), reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _user_record(update)
    await update.message.reply_text(
        fmt.about_text(db.global_stats()), reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/feedback <message> — admin ko forward ho jata hai."""
    user = update.effective_user
    text = " ".join(context.args or []).strip()
    if not text:
        await update.message.reply_text(
            "💬 Aise likho: <code>/feedback aapka bot bahut accha hai</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    db.add_feedback(user.id, user.username, text)
    if ADMIN_ID:
        try:
            await context.bot.send_message(
                ADMIN_ID,
                "💬 New feedback from " + (("@" + user.username) if user.username else str(user.id))
                + ":\n\n" + text,
            )
        except Exception as exc:
            log.warning("Feedback forward failed: %s", exc)
    await update.message.reply_text("✅ Thanks! Feedback admin tak pahunch gaya 🙏")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _user_record(update)
    await update.message.reply_text(
        "📸 Mujhe image bhejo — main enhance kar dunga!\n\n"
        "Commands: /start /help /settings /stats /premium /about",
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Sab unhandled errors yahan aate hain — log + user ko friendly message."""
    log.exception("Unhandled error: %s", context.error)
    try:
        if isinstance(update, Update) and update.effective_chat:
            await context.bot.send_message(
                update.effective_chat.id,
                fmt.error("Kuch technical problem ho gayi. Dobara try karo."),
                parse_mode=ParseMode.HTML,
            )
    except Exception:
        pass
