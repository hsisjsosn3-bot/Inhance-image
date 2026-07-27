"""
database.py — Simple, thread-safe JSON database.
Structure: {"users": {"<user_id>": {...}}, "feedback": [...]}

Render free tier ka disk ephemeral hai — restart pe data reset ho sakta hai.
Permanent storage chahiye to DB_PATH ko Render Disk pe point karo, ya
SQLite/Postgres pe shift kar do (interface same rakhna).
"""
import json
import logging
import os
import threading
from copy import deepcopy
from datetime import date, datetime

from config import DB_PATH, DEFAULT_SETTINGS

log = logging.getLogger(__name__)
_lock = threading.RLock()
_db = None


def _blank():
    return {"users": {}, "feedback": []}


def _load():
    global _db
    if _db is None:
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, "r", encoding="utf-8") as f:
                    _db = json.load(f)
            except Exception as exc:
                log.warning("DB corrupt (%s) — fresh start", exc)
                _db = _blank()
        else:
            _db = _blank()
        _db.setdefault("users", {})
        _db.setdefault("feedback", [])
    return _db


def _flush():
    db = _load()
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = DB_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DB_PATH)


def _today():
    return date.today().isoformat()


def get_user(user_id, username=None, first_name=None):
    """User record laao — na ho to bana do. Har call pe daily counter reset check."""
    with _lock:
        db = _load()
        key = str(user_id)
        user = db["users"].get(key)
        if user is None:
            user = {
                "user_id": user_id,
                "username": username or "",
                "first_name": first_name or "",
                "settings": deepcopy(DEFAULT_SETTINGS),
                "stats": {
                    "total_processed": 0,
                    "today_processed": 0,
                    "last_used": _today(),
                    "favorite_effect": "-",
                    "effects": {},
                    "total_seconds": 0.0,
                },
                "premium": False,
                "joined_date": _today(),
            }
            db["users"][key] = user
        else:
            if username:
                user["username"] = username
            if first_name:
                user["first_name"] = first_name
            for k, v in DEFAULT_SETTINGS.items():
                user.setdefault("settings", {}).setdefault(k, v)
            stats = user.setdefault("stats", {})
            stats.setdefault("effects", {})
            stats.setdefault("total_seconds", 0.0)
            stats.setdefault("total_processed", 0)
            stats.setdefault("favorite_effect", "-")
            if stats.get("last_used") != _today():
                stats["today_processed"] = 0
                stats["last_used"] = _today()
        _flush()
        return deepcopy(user)


def set_setting(user_id, key, value):
    """Ek setting update karo aur updated user record return karo."""
    with _lock:
        db = _load()
        user = db["users"].get(str(user_id))
        if user is None:
            get_user(user_id)
            db = _load()
            user = db["users"][str(user_id)]
        user["settings"][key] = value
        _flush()
        return deepcopy(user)


def record_processing(user_id, effect_label, seconds):
    """Enhancement complete hone par stats update karo."""
    with _lock:
        db = _load()
        user = db["users"].get(str(user_id))
        if user is None:
            get_user(user_id)
            db = _load()
            user = db["users"][str(user_id)]
        stats = user["stats"]
        if stats.get("last_used") != _today():
            stats["today_processed"] = 0
        stats["total_processed"] = stats.get("total_processed", 0) + 1
        stats["today_processed"] = stats.get("today_processed", 0) + 1
        stats["last_used"] = _today()
        stats["total_seconds"] = round(stats.get("total_seconds", 0.0) + float(seconds), 2)
        effects = stats.setdefault("effects", {})
        effects[effect_label] = effects.get(effect_label, 0) + 1
        stats["favorite_effect"] = max(effects, key=effects.get)
        _flush()
        return deepcopy(user)


def set_premium(user_id, value=True):
    with _lock:
        db = _load()
        user = db["users"].get(str(user_id))
        if user is None:
            get_user(user_id)
            db = _load()
            user = db["users"][str(user_id)]
        user["premium"] = bool(value)
        _flush()
        return deepcopy(user)


def add_feedback(user_id, username, text):
    with _lock:
        db = _load()
        db["feedback"].append({
            "user_id": user_id,
            "username": username or "",
            "text": text,
            "at": datetime.now().isoformat(timespec="seconds"),
        })
        _flush()


def all_user_ids():
    with _lock:
        return [int(k) for k in _load()["users"].keys()]


def global_stats():
    with _lock:
        db = _load()
        users = db["users"].values()
        total_images = sum(u.get("stats", {}).get("total_processed", 0) for u in users)
        today_active = sum(1 for u in users if u.get("stats", {}).get("last_used") == _today())
        effects = {}
        for u in users:
            for name, count in u.get("stats", {}).get("effects", {}).items():
                effects[name] = effects.get(name, 0) + count
        top = max(effects, key=effects.get) if effects else "-"
        return {
            "users": len(db["users"]),
            "images": total_images,
            "today_active": today_active,
            "premium": sum(1 for u in users if u.get("premium")),
            "top_effect": top,
            "feedback": len(db["feedback"]),
        }
