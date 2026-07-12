"""Generate and play a spoken Thai audio briefing of today's AI news.

Free, local, no API key: gTTS (unofficial Google Translate TTS, no signup)
for speech synthesis + playsound for silent local playback. Companion to
notify_check.py - designed to be called right after the toast notification
fires, for "listen instead of read" mode.

Two modes:
- generate_and_play(): single voice, full news read start to finish (default)
- generate_and_play_dialogue(): two alternating voices (host + co-host
  reactions) with a short jingle intro, for a more "produced" podcast feel
"""
import io
import json
import math
import os
import struct
import urllib.request
import wave
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

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

CO_HOST_REACTIONS = ["โอ้โห น่าสนใจมากเลยค่ะ", "ว้าว ข่าวนี้เด็ดเลย", "น่าติดตามจริงๆ", "อันนี้ห้ามพลาดเลยนะ"]


def spoken_thai_date(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{d.day} {THAI_MONTHS[d.month]} {d.year + 543}"


def today_str() -> str:
    return datetime.now(BANGKOK).strftime("%Y-%m-%d")


def fetch_latest_items():
    req = urllib.request.Request(SITE_LATEST_URL, headers={"User-Agent": "ai-news-th-audio"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def resolve_items():
    """Returns (use_date, use_items, is_stale) or (None, [], False) if nothing published yet."""
    today = today_str()
    items = fetch_latest_items()
    if not items:
        return None, [], False
    today_items = [i for i in items if i.get("date") == today]
    if today_items:
        return today, today_items, False
    latest_date = max(i["date"] for i in items)
    return latest_date, [i for i in items if i["date"] == latest_date], True


def build_script(items: list, date_str: str, is_stale: bool) -> str:
    major = [i for i in items if i.get("importance") == "major"]
    normal = [i for i in items if i.get("importance") != "major"]

    spoken_date = spoken_thai_date(date_str)
    if is_stale:
        intro = f"สวัสดีค่ะ ตอนนี้ยังไม่มีข่าวของวันนี้ นี่คือข่าวล่าสุดที่มี ประจำวันที่ {spoken_date} มีข่าวทั้งหมด {len(items)} ข่าว"
    else:
        intro = f"สวัสดีค่ะ นี่คือสรุปข่าว AI ประจำวันที่ {spoken_date} มีข่าวทั้งหมด {len(items)} ข่าว"
    lines = [intro]

    if major:
        lines.append(f"เริ่มจากข่าวใหญ่ {len(major)} ข่าวก่อน")
        for i, item in enumerate(major, 1):
            lines.append(f"ข่าวใหญ่ที่ {i}: {item.get('title_th', '')}. {item.get('summary_th', '')}")

    if normal:
        lines.append("ต่อไปเป็นข่าวอื่นๆ")
        for item in normal:
            label = CATEGORY_LABELS_TH.get(item.get("category", "other"), "ข่าวทั่วไป")
            lines.append(f"ข่าว{label}: {item.get('title_th', '')}. {item.get('summary_th', '')}")

    lines.append("จบสรุปข่าวค่ะ")
    return " ".join(lines)


def make_jingle_wav(path: str):
    """Synthesize a short 3-note ascending chime, no external assets needed."""
    rate = 22050
    notes = [523, 659, 784]  # C5, E5, G5
    segments = []
    for freq in notes:
        dur = 0.16
        n = int(rate * dur)
        for i in range(n):
            t = i / rate
            envelope = min(1.0, (n - i) / (n * 0.6))
            val = math.sin(2 * math.pi * freq * t) * envelope * 0.25
            segments.append(int(val * 32767))
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack("<%dh" % len(segments), *segments))


def generate_and_play(play: bool = True) -> str:
    """Single-voice mode with a short jingle intro. Returns the mp3 path, or '' if there's no news yet."""
    use_date, use_items, is_stale = resolve_items()
    if not use_items:
        print("no published items at all yet, skipping audio briefing")
        return ""

    script_text = build_script(use_items, use_date, is_stale)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    mp3_path = os.path.join(AUDIO_DIR, f"{use_date}.mp3")
    speech_path = os.path.join(AUDIO_DIR, f"_{use_date}_speech.mp3")
    jingle_path = os.path.join(AUDIO_DIR, "_jingle.wav")

    gTTS(text=script_text, lang="th").save(speech_path)

    try:
        from pydub import AudioSegment
        make_jingle_wav(jingle_path)
        combined = AudioSegment.from_wav(jingle_path) + AudioSegment.silent(duration=250) + AudioSegment.from_file(speech_path, format="mp3")
        combined.export(mp3_path, format="mp3")
        os.remove(speech_path)
        os.remove(jingle_path)
    except Exception as e:
        print(f"jingle mix failed ({e}), falling back to plain speech")
        os.replace(speech_path, mp3_path)

    print(f"saved audio briefing: {mp3_path}")

    if play:
        playsound(mp3_path)
        print("played audio briefing")

    return mp3_path


def generate_and_play_dialogue(play: bool = True) -> str:
    """Two-voice mode: host reads the news, co-host (pitch-shifted) reacts between items,
    with a short jingle intro. Needs pydub + ffmpeg (already available in this project)."""
    from pydub import AudioSegment

    use_date, use_items, is_stale = resolve_items()
    if not use_items:
        print("no published items at all yet, skipping dialogue briefing")
        return ""

    os.makedirs(AUDIO_DIR, exist_ok=True)
    jingle_path = os.path.join(AUDIO_DIR, "_jingle.wav")
    make_jingle_wav(jingle_path)
    audio = AudioSegment.from_wav(jingle_path) + AudioSegment.silent(duration=250)

    def tts_segment(text: str, pitch_up: bool = False) -> AudioSegment:
        buf = io.BytesIO()
        gTTS(text=text, lang="th").write_to_fp(buf)
        buf.seek(0)
        seg = AudioSegment.from_file(buf, format="mp3")
        if pitch_up:
            shifted = seg._spawn(seg.raw_data, overrides={"frame_rate": int(seg.frame_rate * 1.18)})
            seg = shifted.set_frame_rate(seg.frame_rate)
        return seg

    spoken_date = spoken_thai_date(use_date)
    major = [i for i in use_items if i.get("importance") == "major"]
    normal = [i for i in use_items if i.get("importance") != "major"]

    host_intro = f"สวัสดีค่ะ ดิฉันพิธีกรจาก MEW Station นี่คือสรุปข่าว AI ประจำวันที่ {spoken_date}" if not is_stale \
        else f"สวัสดีค่ะ วันนี้ยังไม่มีข่าวใหม่ นี่คือข่าวล่าสุดที่มี ประจำวันที่ {spoken_date}"
    audio += tts_segment(host_intro) + AudioSegment.silent(duration=200)
    audio += tts_segment(f"มีข่าวทั้งหมด {len(use_items)} ข่าววันนี้ค่ะ", pitch_up=True) + AudioSegment.silent(duration=250)

    ordered = major + normal
    for idx, item in enumerate(ordered):
        tag = "🔥 ข่าวใหญ่" if item in major else CATEGORY_LABELS_TH.get(item.get("category", "other"), "ข่าวทั่วไป")
        host_line = f"ข่าว{tag}: {item.get('title_th', '')}. {item.get('summary_th', '')}"
        audio += tts_segment(host_line) + AudioSegment.silent(duration=200)
        reaction = CO_HOST_REACTIONS[idx % len(CO_HOST_REACTIONS)]
        audio += tts_segment(reaction, pitch_up=True) + AudioSegment.silent(duration=300)

    audio += tts_segment("วันนี้ก็จบสรุปข่าวแค่นี้ค่ะ แล้วเจอกันใหม่") + AudioSegment.silent(duration=150)
    audio += tts_segment("บ๊ายบายค่ะ", pitch_up=True)

    mp3_path = os.path.join(AUDIO_DIR, f"{use_date}_dialogue.mp3")
    audio.export(mp3_path, format="mp3")
    os.remove(jingle_path)
    print(f"saved dialogue briefing: {mp3_path}")

    if play:
        playsound(mp3_path)
        print("played dialogue briefing")

    return mp3_path


if __name__ == "__main__":
    generate_and_play(play=True)
