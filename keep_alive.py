"""
keep_alive.py — Chhota Flask server jo Render ke health check ko answer karta hai.
Render free tier 15 min idle ke baad sleep kar deta hai, isliye UptimeRobot /
cron-job.org se /health ko har 10 min ping karwao.
"""
import logging
from threading import Thread

from flask import Flask, jsonify

from config import PORT, BOT_NAME, VERSION

log = logging.getLogger(__name__)
app = Flask(__name__)


@app.route("/")
def home():
    return "✅ Bot is running!"


@app.route("/health")
def health():
    return jsonify({"status": "alive", "service": BOT_NAME, "version": VERSION}), 200


def _run():
    # Flask dev server kaafi hai — sirf health check serve karna hai
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


def keep_alive():
    """Background thread mein web server start karo (bot polling block nahi hoti)."""
    t = Thread(target=_run, daemon=True)
    t.start()
    log.info("Health check server started on port %s", PORT)
