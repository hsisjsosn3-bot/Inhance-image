"""
utils/formatter.py — Saare user-facing messages ek jagah (premium look).
Sab messages HTML parse_mode ke liye safe hain (user input escape karke).
"""
import html

from config import (BOT_NAME, BOT_USERNAME, DAILY_LIMIT_FREE, QUALITY_PRESETS,
                    RESOLUTION_LABELS, VERSION)
from utils.fonts import bold, bold_italic, fancy, mono
from utils.progress import bar, stage_label

LINE = "━" * 20
THIN = "─" * 20


def _quality_label(key):
    return QUALITY_PRESETS.get(key, QUALITY_PRESETS["high"])["label"]


def _res_label(key):
    return RESOLUTION_LABELS.get(key, "1080p")


def header(title):
    return "╔══════════════════════════════╗\n" \
           "   🌟 " + fancy(title) + " 🌟\n" \
           "╚══════════════════════════════╝"


def welcome(first_name, user):
    s = user["settings"]
    st = user["stats"]
    avg = (st["total_seconds"] / st["total_processed"]) if st.get("total_processed") else 0.0
    return (
        header(BOT_NAME) + "\n\n"
        "👤 Welcome, <b>" + html.escape(first_name or "friend") + "</b>!\n\n"
        "📸 Send me any image and I'll enhance it with\n"
        "pro-grade processing — 12 effects, 4 quality levels.\n\n"
        + LINE + "\n"
        "📊 " + bold("Your Stats Today") + "\n"
        + LINE + "\n"
        "🖼️ Images Processed: " + mono(str(st.get("today_processed", 0))) + "\n"
        "📦 All Time: " + mono(str(st.get("total_processed", 0))) + "\n"
        "⚡ Current Quality: " + _quality_label(s["default_quality"]) + "\n"
        "📏 Resolution: " + mono(_res_label(s["default_resolution"])) + "\n"
        "🎚️ Intensity: " + mono(str(s["intensity"]) + "%") + "\n"
        "⏱️ Avg. Processing: " + mono(("%.1fs" % avg) if avg else "-") + "\n\n"
        "┌─────────────────────────┐\n"
        "│   Choose an option 👇   │\n"
        "└─────────────────────────┘"
    )


def image_received(width, height, size_mb, user):
    s = user["settings"]
    return (
        "╔══════════════════════════════╗\n"
        "   ✨ " + bold("Image Received!") + " ✨\n"
        "╚══════════════════════════════╝\n\n"
        "📸 " + bold("Image Details") + "\n"
        + LINE + "\n"
        "📐 Size: " + mono(str(width) + "×" + str(height)) + "\n"
        "💾 File: " + mono("%.2f MB" % size_mb) + "\n"
        "🎯 Quality: " + _quality_label(s["default_quality"]) + "\n"
        "📏 Output: " + mono(_res_label(s["default_resolution"])) + "\n"
        "🎚️ Intensity: " + mono(str(s["intensity"]) + "%") + "\n"
        + THIN + "\n\n"
        "👇 " + bold("Choose Enhancement Type") + ":"
    )


def processing(effect_label, pct, quality_key):
    return (
        "⏳ " + bold("Processing your image") + "...\n\n"
        + mono(bar(pct)) + "\n"
        + stage_label(pct) + "\n"
        "🔮 Applying: <b>" + html.escape(effect_label) + "</b>\n"
        "⚡ Quality: " + _quality_label(quality_key) + "\n\n"
        "Please wait... ✨"
    )


def result(effect_label, before, after, quality_key, seconds, before_bytes, after_bytes):
    scale = (after[0] / before[0]) if before[0] else 1.0
    scale_txt = (" (%.1fx)" % scale) if abs(scale - 1) > 0.05 else ""
    return (
        "✅ " + bold("Enhancement Complete!") + "\n\n"
        "📊 " + bold("Before") + " → " + bold("After") + "\n"
        + LINE + "\n"
        "📐 " + mono("%d×%d" % before) + " → " + mono("%d×%d" % after) + scale_txt + "\n"
        "🎨 Enhanced with: <b>" + html.escape(effect_label) + "</b>\n"
        "⚡ Quality: " + _quality_label(quality_key) + "\n"
        "⏱️ Time: " + mono("%.1f seconds" % seconds) + "\n"
        "💾 Size: " + mono("%.1f MB" % (before_bytes / 1048576)) + " → "
        + mono("%.1f MB" % (after_bytes / 1048576))
    )


def help_text():
    return (
        header("Help Guide") + "\n\n"
        "1️⃣ Mujhe koi bhi image bhejo (photo ya file)\n"
        "2️⃣ Neeche se enhancement type choose karo\n"
        "3️⃣ Enhanced image turant mil jayegi 🎉\n\n"
        + LINE + "\n"
        "🎨 " + bold("Effects") + "\n"
        + LINE + "\n"
        "🔮 <b>Auto Enhance</b> — exposure, contrast, colour, sharpness auto-fix\n"
        "📐 <b>2x Upscale</b> — Lanczos upscale + smart sharpening\n"
        "🎨 <b>Color Boost</b> — saturation boost, skin tones safe\n"
        "💎 <b>HDR Effect</b> — tone mapping + local contrast\n"
        "🔲 <b>Sharpen Pro</b> — edge-masked multi-level sharpening\n"
        "🌿 <b>Denoise</b> — grain/noise removal, details intact\n"
        "💡 <b>Brightness Fix</b> — auto levels for dark/bright photos\n"
        "🖼️ <b>BG Blur</b> — portrait mode background blur\n"
        "🎭 <b>Cinematic</b> — teal &amp; orange movie grading\n"
        "🧑 <b>Face Enhance</b> — skin smoothing + eye sharpening\n"
        "⚫ <b>B&amp;W Artistic</b> — high-contrast mono with grain\n"
        "🌈 <b>Vibrance Max</b> — safe max vibrance, no clipping\n\n"
        + LINE + "\n"
        "⚙️ " + bold("Controls") + "\n"
        + LINE + "\n"
        "⚡ Quality: LOW / MEDIUM / HIGH / ULTRA\n"
        "📏 Resolution: 720p / 1080p / 2K / 4K\n"
        "🎚️ Intensity: 25% / 50% / 75% / 100%\n\n"
        "💡 Tip: settings session mein save rehti hain — /settings se badlo."
    )


def settings_text(user):
    s = user["settings"]
    return (
        header("Settings") + "\n\n"
        "⚡ Default Quality: " + _quality_label(s["default_quality"]) + "\n"
        "📏 Default Resolution: " + mono(_res_label(s["default_resolution"])) + "\n"
        "🎚️ Default Intensity: " + mono(str(s["intensity"]) + "%") + "\n"
        "💧 Watermark: " + ("🟢 ON" if s.get("watermark") else "🔴 OFF") + "\n\n"
        + LINE + "\n"
        + bold_italic("Neeche se change karo") + " 👇"
    )


def stats_text(user):
    st = user["stats"]
    avg = (st["total_seconds"] / st["total_processed"]) if st.get("total_processed") else 0.0
    top = sorted(st.get("effects", {}).items(), key=lambda kv: -kv[1])[:5]
    lines = "\n".join("• " + html.escape(k) + " — " + mono(str(v) + "x") for k, v in top) or "• abhi koi effect nahi 🙂"
    return (
        header("Your Stats") + "\n\n"
        "🖼️ Total Processed: " + mono(str(st.get("total_processed", 0))) + "\n"
        "📅 Today: " + mono(str(st.get("today_processed", 0))) + " / "
        + mono(str(DAILY_LIMIT_FREE) if not user.get("premium") else "∞") + "\n"
        "⭐ Favourite Effect: <b>" + html.escape(st.get("favorite_effect", "-")) + "</b>\n"
        "⏱️ Avg. Time: " + mono(("%.1fs" % avg) if avg else "-") + "\n"
        "🗓️ Joined: " + mono(user.get("joined_date", "-")) + "\n"
        "💎 Plan: " + ("⭐ PREMIUM" if user.get("premium") else "🆓 FREE") + "\n\n"
        + LINE + "\n"
        "🔥 " + bold("Top Effects") + "\n"
        + LINE + "\n" + lines
    )


def premium_text(user):
    return (
        header("Premium") + "\n\n"
        "🆓 " + bold("Free Plan") + "\n"
        "• " + str(DAILY_LIMIT_FREE) + " images / day\n"
        "• Quality up to HIGH\n"
        "• Output up to 2K\n\n"
        "⭐ " + bold("Premium Plan") + "\n"
        "• Unlimited images\n"
        "• ULTRA quality + 4K output\n"
        "• Batch processing, no cooldown\n"
        "• Priority processing queue\n"
        "• Custom watermark\n\n"
        + LINE + "\n"
        "💬 Interested? " + mono("/feedback") + " se message bhejo ya admin ko contact karo: "
        + html.escape(BOT_USERNAME) + "\n\n"
        "Current plan: " + ("⭐ PREMIUM" if user.get("premium") else "🆓 FREE")
    )


def about_text(stats):
    return (
        header("About") + "\n\n"
        "🤖 Bot: <b>" + html.escape(BOT_NAME) + "</b>\n"
        "🔖 Version: " + mono(VERSION) + "\n"
        "🐍 Engine: Python + OpenCV + Pillow\n"
        "☁️ Hosting: Render (free tier)\n\n"
        + LINE + "\n"
        "👥 Users: " + mono(str(stats["users"])) + "\n"
        "🖼️ Images Enhanced: " + mono(str(stats["images"])) + "\n"
        "🔥 Most Used: <b>" + html.escape(stats["top_effect"]) + "</b>\n\n"
        "Made with ❤️ for better pictures."
    )


def limit_reached():
    return (
        "🚫 " + bold("Daily Limit Reached") + "\n\n"
        "Free plan mein " + str(DAILY_LIMIT_FREE) + " images/day allowed hain.\n"
        "Kal phir try karo, ya ⭐ Premium dekho."
    )


def error(message):
    return (
        "⚠️ " + bold("Oops!") + "\n\n"
        + html.escape(message) + "\n\n"
        "Doosra effect try karo ya nayi image bhejo 📸"
    )


def no_image():
    return (
        "📸 " + bold("Pehle image bhejo") + "\n\n"
        "Koi bhi photo ya image file send karo, phir enhancement buttons aa jayenge."
    )
