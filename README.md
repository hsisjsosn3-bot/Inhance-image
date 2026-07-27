# 🤖 Telegram AI Image Enhancer Bot

Professional Telegram bot — user image bhejta hai, bot 12 different enhancements
apply karke wapas bhejta hai. Premium inline-button UI, quality/resolution/intensity
controls, per-user stats aur Render deployment ready.

## ✨ Features

| Effect | Kya karta hai |
|---|---|
| 🔮 AI Auto Enhance | CLAHE + colour + contrast + smart sharpen |
| 📐 2x Upscale | Lanczos upscale + halo-free sharpening |
| 🎨 Color Boost | Saturation boost, skin tones protected |
| 💎 HDR Effect | Detail enhance + local tone mapping |
| 🔲 Sharpen Pro | Edge-masked multi-radius sharpening |
| 🌿 Denoise | NlMeans (chhoti images) / bilateral (badi images) |
| 💡 Brightness Fix | Auto gamma + percentile levels |
| 🖼️ Background Blur | Face-detect portrait mode blur |
| 🎭 Cinematic Filter | Teal &amp; orange LUT grading |
| 🧑 Face Enhance | Haar cascade + skin smoothing + eye sharpening |
| ⚫ B&amp;W Artistic | High-contrast mono + film grain |
| 🌈 Vibrance Max | Clipping-safe vibrance |

Plus: 4 quality levels, 4 resolution presets, 4 intensity levels, before/after
comparison, full-quality file download, optional watermark, per-user stats,
daily limit, cooldown, admin broadcast + global stats, feedback command.

## 🗂️ Structure

~~~
bot.py                 # entry point, handler registration
config.py              # env vars + presets
database.py            # thread-safe JSON DB
enhance.py             # saare image algorithms + pipeline
keep_alive.py          # Flask health check (Render)
handlers/              # commands, image_handler, callbacks, admin
keyboards/             # main_menu, quality, resolution, intensity
utils/                 # fonts (unicode), progress bar, formatter
~~~

## 🚀 Local run

~~~bash
pip install -r requirements.txt
export BOT_TOKEN="123456:ABC..."      # Windows: set BOT_TOKEN=...
export ADMIN_ID="123456789"
python bot.py
~~~

## ☁️ Render deploy (free tier)

1. Code GitHub pe push karo.
2. Render.com → **New → Web Service** → repo connect karo.
3. **Build Command:** ~~~pip install -r requirements.txt~~~
4. **Start Command:** ~~~python bot.py~~~
5. Environment variables add karo: ~~~BOT_TOKEN~~~, ~~~ADMIN_ID~~~, ~~~BOT_USERNAME~~~ (optional: ~~~DAILY_LIMIT_FREE~~~, ~~~WATERMARK~~~).
6. Deploy → logs mein "Bot starting" dikhna chahiye.

Repo mein ~~~render.yaml~~~ bhi hai — Render "Blueprint" se import karo to sab settings
automatically set ho jayengi.

**Free tier sleep fix:** service 15 min idle ke baad sleep hoti hai. UptimeRobot ya
cron-job.org pe monitor banao jo har 10 minute pe
~~~https://your-app.onrender.com/health~~~ ko ping kare.

## 🧪 Testing checklist

- [ ] /start pe welcome + menu aata hai
- [ ] Photo bhejne par 12 effect buttons dikhte hain
- [ ] Har effect kaam karta hai (error par friendly message)
- [ ] Quality / Resolution / Intensity buttons pe ✅ shift hota hai
- [ ] 📥 Download Original aur 📥 Full Quality File kaam karte hain
- [ ] 🆚 Before/After comparison banta hai
- [ ] /stats mein counter badhta hai
- [ ] /broadcast aur /botstats sirf admin ke liye chalte hain
- [ ] Render pe deploy + /health endpoint 200 deta hai

## 📝 Notes

- **Data:** Render free tier ka disk ephemeral hai — restart pe ~~~data/users.json~~~
  reset ho sakta hai. Permanent chahiye to Render Disk mount karke ~~~DB_PATH~~~ set karo,
  ya ~~~database.py~~~ ko Postgres pe port karo (functions ka interface same rakho).
- **Speed:** free tier CPU slow hai. ULTRA quality + 4K par processing 10-20s le sakti hai;
  HIGH + 1080p sweet spot hai.
- **Limits:** photo upload 10MB tak, document 50MB tak — encoder khud compress karta hai.
