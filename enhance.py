"""
enhance.py — Saare image enhancement algorithms (OpenCV + NumPy + Pillow).

Har effect function ka signature same hai:  func(img_bgr, intensity) -> img_bgr
Isse handlers mein simple dispatch ho jata hai (EFFECTS dict dekho).
"""
import io
import logging
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config import (BOT_USERNAME, MAX_PHOTO_BYTES, QUALITY_PRESETS,
                    RESOLUTIONS)

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _f(intensity):
    """Intensity (0-100) ko 0.05-1.0 factor mein convert karo."""
    return max(0.05, min(1.0, float(intensity) / 100.0))


def _blend(original, new, intensity):
    a = _f(intensity)
    return cv2.addWeighted(original, 1.0 - a, new, a, 0)


def _unsharp(img, radius=2.0, amount=0.7):
    """Unsharp mask — sharpen without halo (kernel filter se better)."""
    if amount <= 0:
        return img
    blur = cv2.GaussianBlur(img, (0, 0), radius)
    return cv2.addWeighted(img, 1.0 + amount, blur, -amount, 0)


def _saturate(img, factor):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * factor, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def _contrast(img, factor):
    out = (img.astype(np.float32) - 128.0) * factor + 128.0
    return np.clip(out, 0, 255).astype(np.uint8)


def _odd(value):
    value = int(max(3, value))
    return value if value % 2 == 1 else value + 1


_CASCADE = None


def _faces(img):
    """Haar cascade se face detect karo (cascade sirf ek baar load hota hai)."""
    global _CASCADE
    try:
        if _CASCADE is None:
            _CASCADE = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        scale = 1.0
        if max(gray.shape) > 1400:                    # detection ke liye chhota image kaafi hai
            scale = 1400.0 / max(gray.shape)
            gray = cv2.resize(gray, (0, 0), fx=scale, fy=scale)
        found = _CASCADE.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
        return [tuple(int(v / scale) for v in face) for face in found]
    except Exception as exc:
        log.warning("Face detection failed: %s", exc)
        return []


# ──────────────────────────────────────────────
# 1. 🔮 AI Auto Enhance
# ──────────────────────────────────────────────
def auto_enhance(img, intensity=75):
    k = _f(intensity)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.6 + 1.8 * k, tileGridSize=(8, 8))
    l = clahe.apply(l)
    out = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    out = _saturate(out, 1.0 + 0.22 * k)
    out = _contrast(out, 1.0 + 0.08 * k)
    out = _unsharp(out, 1.8, 0.55 * k)
    return _blend(img, out, min(100, intensity + 15))


# ──────────────────────────────────────────────
# 2. 📐 2x Upscale
# ──────────────────────────────────────────────
def upscale_image(img, intensity=75, factor=2):
    k = _f(intensity)
    h, w = img.shape[:2]
    # 16MP se upar na jaye — memory + Telegram limits
    while (w * factor) * (h * factor) > 16_000_000 and factor > 1:
        factor -= 1
    if factor < 2:
        factor = 2
        img = _limit_pixels(img, 4_000_000)
        h, w = img.shape[:2]
    up = cv2.resize(img, (w * factor, h * factor), interpolation=cv2.INTER_LANCZOS4)
    up = _unsharp(up, 1.4, 0.5 + 0.5 * k)
    up = cv2.bilateralFilter(up, 5, 30, 30)          # halka smoothing, jaggies kam
    return _unsharp(up, 0.8, 0.25 * k)


# ──────────────────────────────────────────────
# 3. 🎨 Color Boost (skin-tone safe)
# ──────────────────────────────────────────────
def color_boost(img, intensity=75):
    k = _f(intensity)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    skin = ((h <= 25) | (h >= 172)) & (s > 35) & (s < 190) & (v > 60)
    boost = np.full_like(s, 1.0 + 0.45 * k)
    boost[skin] = 1.0 + 0.10 * k                     # skin tones ko barely touch karo
    hsv[..., 1] = np.clip(s * boost, 0, 255)
    hsv[..., 2] = np.clip(v * (1.0 + 0.04 * k), 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


# ──────────────────────────────────────────────
# 4. 💎 HDR Effect
# ──────────────────────────────────────────────
def hdr_effect(img, intensity=75):
    k = _f(intensity)
    work = _limit_pixels(img, 6_000_000)             # detailEnhance heavy hai
    detail = cv2.detailEnhance(work, sigma_s=10, sigma_r=0.15)
    lab = cv2.cvtColor(detail, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.0 + 1.5 * k, tileGridSize=(8, 8)).apply(l)
    detail = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    detail = _saturate(detail, 1.0 + 0.15 * k)
    if detail.shape[:2] != img.shape[:2]:
        detail = cv2.resize(detail, (img.shape[1], img.shape[0]),
                            interpolation=cv2.INTER_LANCZOS4)
    return _blend(img, detail, intensity)


# ──────────────────────────────────────────────
# 5. 🔲 Sharpen Pro (edge masked)
# ──────────────────────────────────────────────
def sharpen_pro(img, intensity=75):
    k = _f(intensity)
    fine = _unsharp(img, 1.0, 0.8 * k)
    both = _unsharp(fine, 3.0, 0.45 * k)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.convertScaleAbs(cv2.Laplacian(gray, cv2.CV_16S, ksize=3))
    mask = cv2.GaussianBlur(edges, (0, 0), 2).astype(np.float32) / 255.0
    mask = np.clip(mask * 3.0, 0.15, 1.0)[..., None]  # flat areas mein noise na aaye
    out = img.astype(np.float32) * (1 - mask) + both.astype(np.float32) * mask
    return np.clip(out, 0, 255).astype(np.uint8)


# ──────────────────────────────────────────────
# 6. 🌿 Denoise
# ──────────────────────────────────────────────
def denoise_image(img, intensity=75):
    k = _f(intensity)
    pixels = img.shape[0] * img.shape[1]
    if pixels > 3_000_000:
        # fastNlMeans bade images pe bahut slow — bilateral use karo
        out = cv2.bilateralFilter(img, 9, int(30 + 60 * k), int(30 + 60 * k))
    else:
        strength = float(3 + 9 * k)
        out = cv2.fastNlMeansDenoisingColored(img, None, strength, strength, 7, 21)
    out = _unsharp(out, 1.2, 0.35)                   # detail wapas laao
    return _blend(img, out, min(100, intensity + 10))


# ──────────────────────────────────────────────
# 7. 💡 Brightness Fix (auto levels)
# ──────────────────────────────────────────────
def brightness_fix(img, intensity=75):
    k = _f(intensity)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean = max(float(np.mean(gray)), 1.0)
    gamma = math.log(0.5) / math.log(mean / 255.0)   # mean ko ~128 pe laao
    gamma = 1.0 + (gamma - 1.0) * k
    gamma = min(max(gamma, 0.35), 3.0)
    lut = np.array([min(255, int(255.0 * ((i / 255.0) ** gamma))) for i in range(256)],
                   dtype=np.uint8)
    out = cv2.LUT(img, lut)
    # halka contrast stretch (1st–99th percentile)
    lo, hi = np.percentile(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY), (1, 99))
    if hi - lo > 20:
        out = np.clip((out.astype(np.float32) - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)
    return _blend(img, out, min(100, intensity + 20))


# ──────────────────────────────────────────────
# 8. 🖼️ Background Blur (portrait mode)
# ──────────────────────────────────────────────
def bg_blur(img, intensity=75):
    k = _f(intensity)
    h, w = img.shape[:2]
    mask = np.zeros((h, w), np.float32)
    faces = _faces(img)
    if faces:
        for (x, y, fw, fh) in faces:
            cx, cy = x + fw // 2, y + int(fh * 1.1)
            cv2.ellipse(mask, (cx, cy), (int(fw * 1.6), int(fh * 2.6)), 0, 0, 360, 1.0, -1)
    else:
        cv2.ellipse(mask, (w // 2, h // 2), (int(w * 0.34), int(h * 0.44)),
                    0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), max(6.0, max(w, h) * 0.02))
    mask = np.clip(mask, 0, 1)[..., None]
    ksize = _odd(max(w, h) * 0.018 * k)
    blurred = cv2.GaussianBlur(img, (ksize, ksize), 0)
    out = img.astype(np.float32) * mask + blurred.astype(np.float32) * (1 - mask)
    return np.clip(out, 0, 255).astype(np.uint8)


# ──────────────────────────────────────────────
# 9. 🎭 Cinematic Filter (teal & orange)
# ──────────────────────────────────────────────
def cinematic_filter(img, intensity=75):
    x = np.arange(256, dtype=np.float32)
    shadow = 1.0 - x / 255.0
    highlight = x / 255.0
    lut = np.zeros((256, 1, 3), dtype=np.uint8)
    lut[:, 0, 0] = np.clip(x * 0.92 + 22 * shadow, 0, 255)      # B → shadows teal
    lut[:, 0, 1] = np.clip(x * 0.97 + 8 * shadow, 0, 255)       # G
    lut[:, 0, 2] = np.clip(x * 1.02 + 26 * highlight, 0, 255)   # R → highlights orange
    graded = cv2.LUT(img, lut)
    graded = _contrast(graded, 1.12)
    graded = _saturate(graded, 0.94)
    graded = _unsharp(graded, 1.5, 0.25)
    return _blend(img, graded, intensity)


# ──────────────────────────────────────────────
# 10. 🧑 Face Enhance
# ──────────────────────────────────────────────
def face_enhance(img, intensity=75):
    k = _f(intensity)
    out = img.copy()
    faces = _faces(img)
    for (x, y, w, h) in faces:
        x, y = max(0, x), max(0, y)
        roi = out[y:y + h, x:x + w]
        if roi.size == 0:
            continue
        smooth = cv2.bilateralFilter(roi, 13, int(40 + 50 * k), int(40 + 50 * k))
        roi = cv2.addWeighted(roi, 1 - 0.75 * k, smooth, 0.75 * k, 0)   # skin smoothing
        eye_top, eye_bottom = int(h * 0.20), int(h * 0.50)
        eyes = roi[eye_top:eye_bottom, :]
        if eyes.size:
            roi[eye_top:eye_bottom, :] = _unsharp(eyes, 1.0, 0.9 * k)   # eye sharpening
        out[y:y + h, x:x + w] = roi
    if not faces:
        out = _saturate(_unsharp(out, 1.5, 0.4 * k), 1.0 + 0.08 * k)    # fallback
    lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=1.4, tileGridSize=(8, 8)).apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


# ──────────────────────────────────────────────
# 11. ⚫ B&W Artistic
# ──────────────────────────────────────────────
def bw_artistic(img, intensity=75):
    k = _f(intensity)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0 + 1.5 * k, tileGridSize=(8, 8)).apply(gray)
    gray = np.clip((gray.astype(np.float32) - 128) * (1.0 + 0.25 * k) + 128, 0, 255)
    grain = np.random.normal(0, 5.0 * k, gray.shape)
    gray = np.clip(gray + grain, 0, 255).astype(np.uint8)
    out = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return _unsharp(out, 1.2, 0.4 * k)


# ──────────────────────────────────────────────
# 12. 🌈 Vibrance Max (clipping-safe)
# ──────────────────────────────────────────────
def vibrance_max(img, intensity=100):
    k = _f(intensity)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    s = hsv[..., 1]
    weight = 1.0 - (s / 255.0)                       # already-saturated pixels safe
    hsv[..., 1] = np.clip(s * (1.0 + 0.85 * k * weight), 0, 250)
    hsv[..., 2] = np.clip(hsv[..., 2] * (1.0 + 0.03 * k), 0, 252)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    return _contrast(out, 1.0 + 0.05 * k)


# ──────────────────────────────────────────────
# Effect registry — callback_data → (label, function)
# ──────────────────────────────────────────────
EFFECTS = {
    "enhance_auto": ("🔮 AI Auto Enhance", auto_enhance),
    "enhance_upscale": ("📐 2x Upscale", upscale_image),
    "enhance_color": ("🎨 Color Boost", color_boost),
    "enhance_hdr": ("💎 HDR Effect", hdr_effect),
    "enhance_sharpen": ("🔲 Sharpen Pro", sharpen_pro),
    "enhance_denoise": ("🌿 Denoise", denoise_image),
    "enhance_brightness": ("💡 Brightness Fix", brightness_fix),
    "enhance_bg_blur": ("🖼️ Background Blur", bg_blur),
    "enhance_cinematic": ("🎭 Cinematic Filter", cinematic_filter),
    "enhance_face": ("🧑 Face Enhance", face_enhance),
    "enhance_bw": ("⚫ B&W Artistic", bw_artistic),
    "enhance_vibrance": ("🌈 Vibrance Max", vibrance_max),
}


# ──────────────────────────────────────────────
# Decode / resize / encode / watermark
# ──────────────────────────────────────────────
def decode(raw):
    """Bytes → BGR numpy array (EXIF rotation + transparency handle karke)."""
    pil = Image.open(io.BytesIO(bytes(raw)))
    try:
        from PIL import ImageOps
        pil = ImageOps.exif_transpose(pil)
    except Exception:
        pass
    if pil.mode in ("RGBA", "LA", "P"):
        pil = pil.convert("RGBA")
        bg = Image.new("RGBA", pil.size, (255, 255, 255, 255))
        pil = Image.alpha_composite(bg, pil)
    pil = pil.convert("RGB")
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def _limit_pixels(img, max_pixels):
    h, w = img.shape[:2]
    if h * w <= max_pixels:
        return img
    scale = math.sqrt(max_pixels / float(h * w))
    return cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))),
                      interpolation=cv2.INTER_AREA)


def resize_to_preset(img, res_key):
    """Resolution preset ke hisaab se fit karo — chhoti image upscale, badi smart resize."""
    target = RESOLUTIONS.get(res_key)
    if not target:
        return img
    tw, th = target
    h, w = img.shape[:2]
    scale = min(tw / float(w), th / float(h))
    if abs(scale - 1.0) < 0.03:
        return img
    new = (max(1, int(w * scale)), max(1, int(h * scale)))
    interp = cv2.INTER_LANCZOS4 if scale > 1 else cv2.INTER_AREA
    out = cv2.resize(img, new, interpolation=interp)
    if scale > 1:
        out = _unsharp(out, 1.2, 0.35)
    return out


def add_watermark(img, text=None):
    """Bottom-right corner mein chhota watermark."""
    text = text or ("✨ Enhanced by " + BOT_USERNAME)
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    size = max(14, int(pil.width * 0.022))
    font = None
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            font = ImageFont.truetype(path, size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    x, y = pil.width - tw - int(size * 0.8), pil.height - th - int(size * 0.9)
    draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def encode_image(img, jpeg_quality=93, max_bytes=MAX_PHOTO_BYTES):
    """JPEG bytes banao aur Telegram limit ke andar rakho (auto-compress)."""
    quality = int(jpeg_quality)
    work = img
    for _ in range(8):
        ok, buf = cv2.imencode(".jpg", work, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not ok:
            raise RuntimeError("Image encode nahi ho payi")
        data = buf.tobytes()
        if len(data) <= max_bytes:
            return data
        if quality > 70:
            quality -= 8
        else:
            work = cv2.resize(work, (0, 0), fx=0.85, fy=0.85, interpolation=cv2.INTER_AREA)
    return data


def make_comparison(before_raw, after_raw):
    """Side-by-side Before | After image (bonus feature)."""
    before, after = decode(before_raw), decode(after_raw)
    height = 900
    def fit(im):
        scale = height / float(im.shape[0])
        return cv2.resize(im, (max(1, int(im.shape[1] * scale)), height),
                          interpolation=cv2.INTER_AREA)
    before, after = fit(before), fit(after)
    gap = np.full((height, 8, 3), 255, np.uint8)
    combo = np.hstack([before, gap, after])
    for text, x in (("BEFORE", 20), ("AFTER", before.shape[1] + 28)):
        cv2.rectangle(combo, (x - 10, 18), (x + 130, 60), (0, 0, 0), -1)
        cv2.putText(combo, text, (x, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                    (255, 255, 255), 2, cv2.LINE_AA)
    return encode_image(combo, 90)


def process_image_bytes(raw, effect_key, quality="high", resolution="1080p",
                        intensity=75, watermark=False):
    """
    Poora pipeline: decode → limit → effect → resolution → watermark → encode.
    Ye function blocking hai — handlers isko asyncio.to_thread se call karte hain.
    """
    preset = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["high"])
    label, func = EFFECTS[effect_key]

    img = decode(raw)
    before = (int(img.shape[1]), int(img.shape[0]))
    work = _limit_pixels(img, preset["max_pixels"])

    out = func(work, intensity)

    if effect_key != "enhance_upscale":
        out = resize_to_preset(out, resolution)
    if watermark:
        out = add_watermark(out)

    data = encode_image(out, preset["jpeg_quality"])
    return {
        "bytes": data,
        "label": label,
        "before": before,
        "after": (int(out.shape[1]), int(out.shape[0])),
    }
