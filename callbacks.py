"""
handlers/callbacks.py — Saare inline button callbacks ka single entry point.

Routing:
  enhance_*    → effect apply
  quality_*    → quality set
  res_*        → resolution set
  intensity_*  → intensity set
  action_*     → download / settings / help / premium / stats / compare / file / rate / again
  set_*        → sub-keyboards (quality, resolution, intensity)
  toggle_*     → watermark on/off
  menu_main    → main menu
"""
import asyncio
import logging
import time

from telegram import InputFile, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

import database as db
from config import COOLDOWN_SECONDS, DAILY_LIMIT_FREE
from enhance import EFFECTS, make_comparison, process_image_bytes
from keyboards.intensity import get_intensity_keyboard
from keyboards.main_menu import (get_back_keyboard, get_main_keyboard,
                                 get_result_keyboard, get_settings_keyboard)
from keyboards.quality import get_quality_keyboard
from keyboards.resolution import get_resolution_keyboard
from utils import formatter as fmt

log = logging.getLogger(__name__)


async def _safe_edit(query, text=None, keyboard=None):
    """Telegram 'message is not modified' error ko ignore karo."""
    try:
        if text is None:
            await query.edit_message_reply_markup(reply_markup=keyboard)
        else:
            await query.edit_message_text(text, reply_markup=keyboard,
                                          parse_mode=ParseMode.HTML)
    except BadRequest as exc:
        if "not modified" not in str(exc).lower():
            log.warning("Edit failed: %s", exc)


def _cooldown_left(context):
    last = context.user_data.get("last_process_ts", 0)
    left = COOLDOWN_SECONDS - (time.time() - last)
    return max(0, int(round(left)))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    user = db.get_user(update.effective_user.id, update.effective_user.username,
                       update.effective_user.first_name)

    # ---- Effects ----
    if data in EFFECTS:
        await run_enhancement(update, context, data, user)
        return

    # ---- Quality ----
    if data.startswith("quality_"):
        value = data.split("_", 1)[1]
        user = db.set_setting(user["user_id"], "default_quality", value)
        await query.answer("⚡ Quality: " + value.upper())
        if query.message and query.message.text and "Settings" in query.message.text:
            await _safe_edit(query, fmt.settings_text(user), get_quality_keyboard(value))
        else:
            await _safe_edit(query, None, get_main_keyboard(user))
        return

    # ---- Resolution ----
    if data.startswith("res_"):
        value = data.split("_", 1)[1]
        user = db.set_setting(user["user_id"], "default_resolution", value)
        await query.answer("📏 Resolution: " + value.upper())
        if query.message and query.message.text and "Settings" in query.message.text:
            await _safe_edit(query, fmt.settings_text(user), get_resolution_keyboard(value))
        else:
            await _safe_edit(query, None, get_main_keyboard(user))
        return

    # ---- Intensity ----
    if data.startswith("intensity_"):
        value = int(data.split("_", 1)[1])
        user = db.set_setting(user["user_id"], "intensity", value)
        await query.answer("🎚️ Intensity: " + str(value) + "%")
        if query.message and query.message.text and "Settings" in query.message.text:
            await _safe_edit(query, fmt.settings_text(user), get_intensity_keyboard(value))
        else:
            await _safe_edit(query, None, get_main_keyboard(user))
        return

    # ---- Sub-menus ----
    if data == "set_quality":
        await query.answer()
        await _safe_edit(query, fmt.settings_text(user),
                         get_quality_keyboard(user["settings"]["default_quality"]))
        return
    if data == "set_res":
        await query.answer()
        await _safe_edit(query, fmt.settings_text(user),
                         get_resolution_keyboard(user["settings"]["default_resolution"]))
        return
    if data == "set_intensity":
        await query.answer()
        await _safe_edit(query, fmt.settings_text(user),
                         get_intensity_keyboard(user["settings"]["intensity"]))
        return
    if data == "toggle_watermark":
        new_value = not user["settings"].get("watermark", False)
        user = db.set_setting(user["user_id"], "watermark", new_value)
        await query.answer("💧 Watermark " + ("ON" if new_value else "OFF"))
        await _safe_edit(query, fmt.settings_text(user), get_settings_keyboard(user))
        return

    # ---- Info screens ----
    if data == "action_settings":
        await query.answer()
        await _safe_edit(query, fmt.settings_text(user), get_settings_keyboard(user))
        return
    if data == "action_help":
        await query.answer()
        await _safe_edit(query, fmt.help_text(), get_back_keyboard())
        return
    if data == "action_premium":
        await query.answer()
        await _safe_edit(query, fmt.premium_text(user), get_back_keyboard())
        return
    if data == "action_stats":
        await query.answer()
        await _safe_edit(query, fmt.stats_text(user), get_back_keyboard())
        return
    if data == "menu_main":
        await query.answer()
        if context.user_data.get("original_image"):
            width, height = context.user_data.get("original_dims", (0, 0))
            size_mb = context.user_data.get("original_size", 0) / 1048576
            await _safe_edit(query, fmt.image_received(width, height, size_mb, user),
                             get_main_keyboard(user))
        else:
            await _safe_edit(query, fmt.welcome(update.effective_user.first_name, user),
                             get_back_keyboard())
        return
    if data == "action_rate":
        await query.answer("⭐ Thanks for the love! /feedback se review bhejo 💛",
                           show_alert=True)
        return

    # ---- Files ----
    if data == "action_download":
        raw = context.user_data.get("original_image")
        if not raw:
            await query.answer("Pehle image bhejo 📸", show_alert=True)
            return
        await query.answer("📥 Bhej raha hoon...")
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=InputFile(bytes(raw), filename="original.jpg"),
            caption="📥 Original image (uncompressed)",
        )
        return

    if data == "action_file":
        result = context.user_data.get("result_image")
        if not result:
            await query.answer("Pehle koi effect apply karo ✨", show_alert=True)
            return
        await query.answer("📥 Full quality file bhej raha hoon...")
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=InputFile(bytes(result), filename="enhanced.jpg"),
            caption="📥 Full quality (Telegram compression ke bina)",
        )
        return

    if data == "action_compare":
        raw = context.user_data.get("original_image")
        result = context.user_data.get("result_image")
        if not (raw and result):
            await query.answer("Pehle koi effect apply karo ✨", show_alert=True)
            return
        await query.answer("🆚 Comparison bana raha hoon...")
        try:
            combo = await asyncio.to_thread(make_comparison, raw, result)
            await context.bot.send_photo(
                chat_id=query.message.chat_id, photo=combo,
                caption="🆚 <b>Before</b> vs <b>After</b>", parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            log.exception("Comparison failed: %s", exc)
            await context.bot.send_message(
                query.message.chat_id,
                fmt.error("Comparison ban nahi payi."), parse_mode=ParseMode.HTML)
        return

    if data == "action_again":
        await query.answer()
        if not context.user_data.get("original_image"):
            await context.bot.send_message(query.message.chat_id, fmt.no_image(),
                                           parse_mode=ParseMode.HTML)
            return
        width, height = context.user_data.get("original_dims", (0, 0))
        size_mb = context.user_data.get("original_size", 0) / 1048576
        await context.bot.send_message(
            query.message.chat_id,
            fmt.image_received(width, height, size_mb, user),
            reply_markup=get_main_keyboard(user), parse_mode=ParseMode.HTML,
        )
        return

    await query.answer()


async def run_enhancement(update, context, effect_key, user):
    """Effect apply karo — progress animation + threaded processing."""
    query = update.callback_query
    raw = context.user_data.get("original_image")
    if not raw:
        await query.answer("Pehle image bhejo 📸", show_alert=True)
        return

    # Daily limit (free users)
    if not user.get("premium") and user["stats"].get("today_processed", 0) >= DAILY_LIMIT_FREE:
        await query.answer()
        await context.bot.send_message(query.message.chat_id, fmt.limit_reached(),
                                       parse_mode=ParseMode.HTML)
        return

    # Per-user cooldown
    left = _cooldown_left(context)
    if left > 0 and not user.get("premium"):
        await query.answer("⏳ " + str(left) + "s ruko, phir try karo", show_alert=False)
        return
    context.user_data["last_process_ts"] = time.time()

    settings = user["settings"]
    quality = settings.get("default_quality", "high")
    resolution = settings.get("default_resolution", "1080p")
    intensity = settings.get("intensity", 75)
    watermark = settings.get("watermark", False)
    label = EFFECTS[effect_key][0]

    await query.answer("✨ " + label)
    progress = await context.bot.send_message(
        query.message.chat_id, fmt.processing(label, 10, quality), parse_mode=ParseMode.HTML
    )

    started = time.perf_counter()
    task = asyncio.create_task(asyncio.to_thread(
        process_image_bytes, raw, effect_key, quality, resolution, intensity, watermark
    ))

    pct = 10
    while not task.done():
        await asyncio.sleep(1.2)
        if task.done():
            break
        pct = min(90, pct + 20)
        try:
            await progress.edit_text(fmt.processing(label, pct, quality),
                                     parse_mode=ParseMode.HTML)
        except Exception:
            pass

    try:
        result = await task
    except Exception as exc:
        log.exception("Enhancement failed (%s): %s", effect_key, exc)
        try:
            await progress.edit_text(
                fmt.error("Ye effect apply nahi ho paya."), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    elapsed = time.perf_counter() - started
    context.user_data["result_image"] = result["bytes"]

    caption = fmt.result(result["label"], result["before"], result["after"], quality,
                         elapsed, len(raw), len(result["bytes"]))
    try:
        await progress.delete()
    except Exception:
        pass

    await context.bot.send_photo(
        chat_id=query.message.chat_id, photo=result["bytes"], caption=caption,
        reply_markup=get_result_keyboard(), parse_mode=ParseMode.HTML,
    )
    db.record_processing(user["user_id"], result["label"], elapsed)
    log.info("Enhanced %s for %s in %.2fs", effect_key, user["user_id"], elapsed)
