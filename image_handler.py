"""
handlers/image_handler.py — Image receive karke session mein store karta hai
aur enhancement menu dikhata hai. Batch (album) support bhi included.
"""
import io
import logging

from PIL import Image
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import database as db
from keyboards.main_menu import get_main_keyboard
from utils import formatter as fmt

log = logging.getLogger(__name__)

MAX_INPUT_BYTES = 20 * 1024 * 1024


async def _store_and_show(update, context, raw, source):
    user = db.get_user(update.effective_user.id, update.effective_user.username,
                       update.effective_user.first_name)
    try:
        width, height = Image.open(io.BytesIO(bytes(raw))).size
    except Exception:
        await update.message.reply_text(
            fmt.error("Ye file image nahi lagti. JPG/PNG/WEBP bhejo."),
            parse_mode=ParseMode.HTML,
        )
        return

    context.user_data["original_image"] = bytes(raw)
    context.user_data["original_size"] = len(raw)
    context.user_data["original_dims"] = (width, height)
    context.user_data.pop("result_image", None)

    log.info("Image received from %s via %s (%sx%s, %s bytes)",
             update.effective_user.id, source, width, height, len(raw))

    await update.message.reply_text(
        fmt.image_received(width, height, len(raw) / 1048576, user),
        reply_markup=get_main_keyboard(user),
        parse_mode=ParseMode.HTML,
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Compressed photo (normal Telegram image send)."""
    photo = update.message.photo[-1]          # sabse badi resolution
    if photo.file_size and photo.file_size > MAX_INPUT_BYTES:
        await update.message.reply_text(
            fmt.error("Image 20MB se badi hai. Chhoti image bhejo."),
            parse_mode=ParseMode.HTML,
        )
        return
    telegram_file = await photo.get_file()
    raw = await telegram_file.download_as_bytearray()
    await _store_and_show(update, context, raw, "photo")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Uncompressed image file (best quality — recommended)."""
    doc = update.message.document
    if doc.file_size and doc.file_size > MAX_INPUT_BYTES:
        await update.message.reply_text(
            fmt.error("File 20MB se badi hai. Compress karke bhejo."),
            parse_mode=ParseMode.HTML,
        )
        return
    telegram_file = await doc.get_file()
    raw = await telegram_file.download_as_bytearray()
    await _store_and_show(update, context, raw, "document")
