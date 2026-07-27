"""
utils/fonts.py — Normal text ko fancy Unicode text mein convert karta hai.
Dict manually likhne ki zarurat nahi — Unicode blocks contiguous hote hain,
isliye offset se map bana lete hain (chhota + fast).
"""


def _range_map(upper_start, lower_start, digit_start=None):
    table = {}
    for i in range(26):
        table[chr(ord("A") + i)] = chr(upper_start + i)
        table[chr(ord("a") + i)] = chr(lower_start + i)
    if digit_start:
        for i in range(10):
            table[chr(ord("0") + i)] = chr(digit_start + i)
    return table


FONTS = {
    "bold_sans": _range_map(0x1D5D4, 0x1D5EE, 0x1D7EC),        # 𝗔𝗕𝗖 𝗮𝗯𝗰 𝟬𝟭𝟮
    "italic_sans": _range_map(0x1D608, 0x1D622),               # 𝘈𝘉𝘊 𝘢𝘣𝘤
    "bold_italic_sans": _range_map(0x1D63C, 0x1D656),          # 𝘼𝘽𝘾 𝙖𝙗𝙘
    "mono": _range_map(0x1D670, 0x1D68A, 0x1D7F6),             # 𝙰𝙱𝙲 𝚊𝚋𝚌
    "fancy": _range_map(0x1D56C, 0x1D586),                     # 𝕬𝕭𝕮 (bold Fraktur)
    "script": _range_map(0x1D4D0, 0x1D4EA),                    # 𝒜𝐵𝒞 (bold script)
    "double": _range_map(0x1D538, 0x1D552, 0x1D7D8),           # 𝔸𝔹ℂ
}


def to_fancy(text, style="bold_sans"):
    """Convert normal text to fancy unicode text."""
    table = FONTS.get(style)
    if not table:
        return text
    return "".join(table.get(ch, ch) for ch in text)


def bold(text):
    return to_fancy(text, "bold_sans")


def italic(text):
    return to_fancy(text, "italic_sans")


def bold_italic(text):
    return to_fancy(text, "bold_italic_sans")


def mono(text):
    return to_fancy(text, "mono")


def fancy(text):
    return to_fancy(text, "fancy")


def script(text):
    return to_fancy(text, "script")
