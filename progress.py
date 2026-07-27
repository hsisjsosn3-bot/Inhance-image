"""
utils/progress.py — Text progress bar + processing stage labels.
"""

FILLED = "█"
EMPTY = "░"

STAGES = [
    (15, "📥 Reading image"),
    (35, "🔍 Analysing pixels"),
    (55, "🎨 Applying effect"),
    (75, "📐 Resizing output"),
    (90, "💾 Encoding file"),
    (100, "✅ Finishing up"),
]


def bar(pct, width=10):
    """[████████░░] 80% jaisa bar."""
    pct = max(0, min(100, int(pct)))
    filled = round(width * pct / 100)
    return "[" + FILLED * filled + EMPTY * (width - filled) + "] " + str(pct) + "%"


def stage_label(pct):
    for limit, label in STAGES:
        if pct <= limit:
            return label
    return STAGES[-1][1]
