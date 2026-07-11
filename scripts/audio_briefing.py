"""Generate and play a spoken Thai audio briefing of today's AI news.

Free, local, no API key: gTTS (unofficial Google Translate TTS, no signup)
for speech synthesis + playsound for silent local playback. Companion to
notify_check.py - designed to be called right after the toast notification
fires, for "listen instead of read" mode.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

from gtts import gTTS
from playsound import playsound

SITE_LATEST_URL = "https://mewuserr.github.io/ai-news-th/data/latest.json"
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audio")
BANGKOK = timezone(timedelta(hours=7))

CATEGORY_LABELS_TH = {
    "model_release": "เปิดตัวโมเดล/ฟีเจอร์ใหม่",
    "product": "ผลิตภัณฑ์",
    "funding": "ทุน/ธุรกิจ",
    "research": "งานวิจัย",
    "policy": "นโยบาย/กฎหมาย",
    "other": "ข่าวทั่วไป",
}


def today_str() -> str:
    return datetime.now(BANGKOK).strftime("%Y-%m-%d")


def fetch_latest_items():
    req = urllib.request.Request(SITE_LATEST_URL, headers={"User-Agent": "ai-news-th-audio"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_script(today_items: list, date_str: str) -> str:
    major = [i for i in today_items if i.get("importance") == "major"]
    normal = [i for i in today_items if i.get("importance") != "major"]

    lines = [f"สวัสดีครับ นี่คือสรุปข่าว AI ประจำวันที่ {date_str} มีข่าวทั้งหมด {len(today_items)} ข่าว"]

    if major:
        lines.append(f"เริ่มจากข่าวใหญ่ {len(major)} ข่าวก่อน")
        for i, item in enumerate(major, 1):
            lines.append(f"ข่าวใหญ่ที่ {i}: {item.get('title_th', '')}. {item.get('summary_th', '')}")

    if normal:
        lines.append("ต่อไปเป็นข่าวอื่นๆ")
        for item in normal:
            label = CATEGORY_LABELS_TH.get(item.get("category", "other"), "ข่าวทั่วไป")
            lines.append(f"ข่าว{label}: {item.get('title_th', '')}. {item.get('summary_th', '')}")

    lines.append("จบสรุปข่าว AI วันนี้ครับ")
    return " ".join(lines)


def generate_and_play(play: bool = True) -> str:
    """Returns the path to the generated mp3, or '' if there's nothing to say today."""
    today = today_str()
    items = fetch_latest_items()
    today_items = [i for i in items if i.get("date") == today]
    if not today_items:
        print(f"no published items for {today} yet, skipping audio briefing")
        return ""

    script_text = build_script(today_items, today)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    mp3_path = os.path.join(AUDIO_DIR, f"{today}.mp3")

    gTTS(text=script_text, lang="th").save(mp3_path)
    print(f"saved audio briefing: {mp3_path}")

    if play:
        playsound(mp3_path)
        print("played audio briefing")

    return mp3_path


if __name__ == "__main__":
    generate_and_play(play=True)
