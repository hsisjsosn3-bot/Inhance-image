"""
bot.py — Main entry point.
python-telegram-bot v20+ (async) syntax. Run: python bot.py
"""
import logging
import sys

from telegram import Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          MessageHandler, filters)

from config import BOT_NAME, BOT_TOKEN, VERSION
from handlers import admin, callbacks, commands, image_handler
from keep_alive import keep_alive

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

CALLBACK_PATTERN = "^(enhance_|quality_|res_|intensity_|action_|menu_|set_|toggle_)"


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    # --- User commands ---
    app.add_handler(CommandHandler("start", commands.start))
    app.add_handler(CommandHandler("help", commands.help_command))
    app.add_handler(CommandHandler("settings", commands.settings))
    app.add_handler(CommandHandler("stats", commands.stats))
    app.add_handler(CommandHandler("premium", commands.premium))
    app.add_handler(CommandHandler("feedback", commands.feedback))
    app.add_handler(CommandHandler("about", commands.about))

    # --- Admin commands ---
    app.add_handler(CommandHandler("broadcast", admin.broadcast))
    app.add_handler(CommandHandler("botstats", admin.bot_stats))
    app.add_handler(CommandHandler("grantpremium", admin.grant_premium))

    # --- Images ---
    app.add_handler(MessageHandler(filters.PHOTO, image_handler.handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, image_handler.handle_document))

    # --- Inline buttons ---
    app.add_handler(CallbackQueryHandler(callbacks.handle_callback, pattern=CALLBACK_PATTERN))

    # --- Fallback text ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, commands.handle_text))

    # --- Errors ---
    app.add_error_handler(commands.error_handler)
    return app


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN missing! Environment variable set karo.")
        sys.exit(1)

    keep_alive()                      # Render health check server (background thread)
    app = build_application()
    logger.info("🤖 %s v%s starting...", BOT_NAME, VERSION)
    # run_polling khud event loop manage karta hai — asyncio.run ki zarurat nahi
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
