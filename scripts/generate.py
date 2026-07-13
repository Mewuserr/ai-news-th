"""Regenerate index.html / weekly.html / archive.html from data/*.json.

Pure stdlib, no server needed - output is opened directly via file://.
Run manually or from engine-prompt.md after data/ is updated.
"""
import json
import glob
import os
import re
import random
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

try:
    from pythainlp.tokenize import word_tokenize as _thai_word_tokenize
    from pythainlp.corpus import thai_stopwords as _thai_stopwords
    THAI_NLP_AVAILABLE = True
except ImportError:
    THAI_NLP_AVAILABLE = False

BANGKOK = timezone(timedelta(hours=7))
ALL_SOURCES = []

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_NEWS_DIR = os.path.join(ROOT, "data", "news")
DATA_WEEKLY_DIR = os.path.join(ROOT, "data", "weekly")
LATEST_PATH = os.path.join(ROOT, "data", "latest.json")

CATEGORY_LABELS = {
    "model_release": "เปิดตัวโมเดล/ฟีเจอร์ใหม่",
    "product": "ผลิตภัณฑ์",
    "funding": "ทุน/ธุรกิจ",
    "research": "งานวิจัย",
    "policy": "นโยบาย/กฎหมาย",
    "space": "อวกาศ",
    "other": "อื่นๆ",
}

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]


def thai_date(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{d.day} {THAI_MONTHS[d.month]} {d.year + 543}"


def load_all_news():
    """Returns list of items, each with a 'date' field, sorted newest first."""
    items = []
    for path in sorted(glob.glob(os.path.join(DATA_NEWS_DIR, "*.json"))):
        date_str = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            day_items = json.load(f)
        for item in day_items:
            item.setdefault("date", date_str)
            items.append(item)
    items.sort(key=lambda x: x["date"], reverse=True)
    return items


def load_weekly():
    weeks = []
    for path in sorted(glob.glob(os.path.join(DATA_WEEKLY_DIR, "*.json")), reverse=True):
        with open(path, encoding="utf-8") as f:
            weeks.append(json.load(f))
    return weeks


def load_narrative(date_str: str) -> str:
    path = os.path.join(ROOT, "data", "narrative", f"{date_str}.json")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("narrative_th", "")


def load_capabilities() -> dict:
    path = os.path.join(ROOT, "data", "capabilities.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_skills() -> dict:
    path = os.path.join(ROOT, "data", "skills.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


SHARED_STYLE = """
:root {
  color-scheme: dark;
  --bg: #000000;
  --text: #f2f2f5;
  --text-dim: #9a9aa8;
  --accent: #4fd1ff;
  --major: #ff4fd8;
  --border: rgba(79, 209, 255, 0.25);
  --card-bg: rgba(255, 255, 255, 0.045);
}
html, body { background: var(--bg); }
body {
  font-family: "Leelawadee UI", "Noto Sans Thai", "Segoe UI", -apple-system, sans-serif;
  font-size: 16.5px;
  max-width: 880px; margin: 0 auto; padding: 24px 16px 64px; line-height: 1.65;
  color: var(--text); position: relative; z-index: 0;
}
canvas#starfield { position: fixed; inset: 0; z-index: -3; }
.celestial-body { position: fixed; z-index: -2; pointer-events: none; background-size: contain; background-repeat: no-repeat; background-position: center; animation: floatPlanet ease-in-out infinite; }
.body-earth { top: -130px; right: -130px; width: 340px; height: 340px; background-image: url('assets/earth.webp'); opacity: 0.92; animation-duration: 9s; }
.body-moon { bottom: -30px; left: -30px; width: 100px; height: 100px; background-image: url('assets/moon.webp'); opacity: 0.5; animation-duration: 13s; animation-delay: -3s; }
.body-sun { top: -55px; left: -60px; width: 150px; height: 150px; background-image: url('assets/sun.webp'); opacity: 0.38; animation-duration: 17s; animation-delay: -6s; }
.body-saturn { bottom: -14px; right: -55px; width: 190px; height: 75px; background-image: url('assets/saturn.webp'); opacity: 0.5; animation-duration: 15s; animation-delay: -9s; }
.body-uranus { top: 42%; left: -35px; width: 78px; height: 78px; background-image: url('assets/uranus.webp'); opacity: 0.4; animation-duration: 11s; animation-delay: -1s; }
.body-mars { top: 58%; right: -28px; width: 62px; height: 62px; background-image: url('assets/mars.webp'); opacity: 0.42; animation-duration: 10s; animation-delay: -5s; }
@keyframes floatPlanet { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-16px); } }
@media (prefers-reduced-motion: reduce) { .celestial-body { animation: none; } }
.lang-toggle { display: flex; justify-content: center; gap: 6px; margin-bottom: 10px; }
.lang-toggle button { border: 1px solid var(--border); background: color-mix(in srgb, var(--accent) 6%, transparent); color: var(--text-dim); border-radius: 999px; padding: 4px 14px; font-size: 12.5px; font-weight: 700; cursor: pointer; }
.lang-toggle button.active { background: color-mix(in srgb, var(--accent) 25%, transparent); color: var(--text); border-color: var(--accent); }
#google_translate_element, .goog-te-gadget-icon, iframe.skiptranslate { display: none !important; }
body { top: 0 !important; }
.goog-text-highlight { background: none !important; box-shadow: none !important; }
.brand { font-size: 14px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); opacity: 0.9; margin-bottom: 10px; font-weight: 700; }
.site-footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid var(--border); font-size: 13px; color: var(--text-dim); opacity: 0.8; text-align: center; }
nav { display: flex; gap: 16px; margin-bottom: 24px; font-size: 15.5px; flex-wrap: wrap; }
nav a { text-decoration: none; padding: 6px 12px; border-radius: 8px; opacity: 0.75; color: var(--text-dim); }
nav a.active { background: color-mix(in srgb, var(--accent) 20%, transparent); opacity: 1; font-weight: 700; color: var(--text); box-shadow: 0 0 12px color-mix(in srgb, var(--accent) 35%, transparent); }
h1 { font-size: 25px; margin-bottom: 4px; color: var(--text); font-weight: 700; }
h2 { color: var(--text); }
.sub { opacity: 0.7; font-size: 14.5px; margin-bottom: 20px; color: var(--text-dim); }
.filters { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
.filters button { border: 1px solid var(--border); background: color-mix(in srgb, var(--accent) 6%, transparent); color: var(--text-dim); border-radius: 999px; padding: 6px 14px; font-size: 13.5px; cursor: pointer; }
.filters button.active { background: color-mix(in srgb, var(--accent) 25%, transparent); color: var(--text); font-weight: 700; border-color: var(--accent); }
.card { border: 1px solid var(--border); border-radius: 12px; padding: 17px; margin-bottom: 14px; background: var(--card-bg); backdrop-filter: blur(2px); }
.card.major { border: 1.5px solid var(--major); background: color-mix(in srgb, var(--major) 10%, var(--card-bg)); box-shadow: 0 0 18px color-mix(in srgb, var(--major) 22%, transparent); }
.badge { display: inline-block; font-size: 12.5px; padding: 3px 10px; border-radius: 999px; background: color-mix(in srgb, var(--accent) 18%, transparent); color: var(--text-dim); margin-bottom: 8px; margin-right: 6px; }
.badge.major { background: var(--major); color: #1a0016; font-weight: 700; }
.card h3 { margin: 0 0 8px; font-size: 18px; font-weight: 700; }
.card h3 a { color: var(--text); text-decoration: underline; text-decoration-color: color-mix(in srgb, var(--accent) 55%, transparent); text-decoration-thickness: 1.5px; text-underline-offset: 3px; }
.card h3 a:hover { color: var(--accent); text-decoration-color: var(--accent); }
.card p { margin: 0 0 8px; color: var(--text); opacity: 0.92; font-size: 15.5px; }
.card p.context { font-size: 13.5px; font-style: italic; color: var(--accent); opacity: 0.85; border-left: 2px solid var(--accent); padding-left: 8px; }
.meta { font-size: 13.5px; opacity: 0.6; color: var(--text-dim); }
.group-heading { margin-top: 32px; margin-bottom: 12px; font-size: 16.5px; opacity: 0.9; font-weight: 700; color: var(--accent); }
.major-toggle { display: flex; align-items: center; gap: 6px; font-size: 13.5px; margin-bottom: 16px; opacity: 0.85; cursor: pointer; color: var(--text-dim); }
details { margin-bottom: 10px; }
summary { cursor: pointer; font-weight: 700; padding: 4px 0; color: var(--text); }
.empty { opacity: 0.65; padding: 20px 0; color: var(--text-dim); }
.stat-section { margin-bottom: 36px; }
.stat-section h2 { font-size: 16.5px; margin-bottom: 14px; }
.stat-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.stat-label { width: 130px; flex-shrink: 0; font-size: 13.5px; text-align: right; opacity: 0.85; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-dim); }
.stat-track { flex: 1; position: relative; height: 20px; }
.stat-bar { height: 20px; max-height: 20px; background: var(--accent); border-radius: 4px; min-width: 4px; box-shadow: 0 0 8px color-mix(in srgb, var(--accent) 50%, transparent); }
.stat-value { font-size: 12.5px; opacity: 0.7; margin-left: 8px; font-variant-numeric: tabular-nums; color: var(--text-dim); }
.stat-bar-wrap { display: flex; align-items: center; flex: 1; }
.card-actions { display: flex; gap: 4px; float: right; align-items: center; }
.card-actions button { background: none; border: none; cursor: pointer; font-size: 16px; line-height: 1; padding: 4px 5px; opacity: 0.6; color: var(--text-dim); border-radius: 6px; }
.card-actions button:hover { opacity: 1; background: color-mix(in srgb, var(--accent) 12%, transparent); }
.bookmark-btn { color: var(--major); font-size: 18px; }
.bookmark-btn.saved { opacity: 1; }
.share-btn { color: var(--accent); }
.listen-btn.speaking { opacity: 1; color: var(--accent); }
.like-btn.active[data-v="up"] { opacity: 1; color: #6fe08f; }
.like-btn.active[data-v="down"] { opacity: 1; color: var(--text-dim); }
.related { clear: both; margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border); font-size: 12.5px; color: var(--text-dim); }
.related span { opacity: 0.8; }
.related ul { margin: 4px 0 0; padding-left: 18px; }
.related a { color: var(--accent); text-decoration: none; }
.related a:hover { text-decoration: underline; }
.search-box { width: 100%; box-sizing: border-box; padding: 10px 14px; margin-bottom: 16px; border-radius: 8px; border: 1px solid var(--border); background: var(--card-bg); color: var(--text); font-size: 15px; font-family: inherit; }
.search-box::placeholder { color: var(--text-dim); }
.quick-read { border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 20px; background: color-mix(in srgb, var(--accent) 8%, var(--card-bg)); font-size: 15px; line-height: 1.8; }
.word-cloud { display: flex; flex-wrap: wrap; gap: 10px; align-items: baseline; margin-bottom: 30px; }
.word-cloud span { color: var(--accent); opacity: 0.85; }
.leaderboard { list-style: none; padding: 0; margin: 0 0 30px; counter-reset: rank; }
.leaderboard li { counter-increment: rank; display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--border); }
.leaderboard li::before { content: counter(rank); font-weight: 700; color: var(--major); width: 22px; font-size: 15px; }
.leaderboard .lb-name { flex: 1; }
.leaderboard .lb-count { color: var(--text-dim); font-variant-numeric: tabular-nums; font-size: 13.5px; }
.streak-badge { font-size: 12.5px; color: var(--major); opacity: 0.9; margin-bottom: 8px; }
.accent-picker { display: flex; gap: 8px; align-items: center; margin-bottom: 16px; }
.accent-picker button { width: 22px; height: 22px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; }
.accent-picker button.active { border-color: var(--text); }
.follow-toggle { background: none; border: 1px solid var(--border); color: var(--text-dim); border-radius: 8px; padding: 5px 12px; font-size: 12.5px; cursor: pointer; margin-bottom: 12px; }
.follow-toggle:hover { color: var(--text); }
.follow-panel { display: none; border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 16px; background: var(--card-bg); }
.follow-panel.open { display: block; }
.follow-panel label { display: inline-flex; align-items: center; gap: 6px; margin: 0 14px 8px 0; font-size: 13.5px; color: var(--text-dim); }
.follow-panel .fp-actions { margin-top: 6px; }
.follow-panel .fp-actions button { font-size: 12px; margin-right: 10px; background: none; border: none; color: var(--accent); cursor: pointer; text-decoration: underline; padding: 0; }
.quiz-q { border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 14px; background: var(--card-bg); }
.quiz-q h3 { font-size: 15.5px; margin: 0 0 12px; }
.quiz-q .quiz-opt { display: block; width: 100%; text-align: left; padding: 10px 14px; margin-bottom: 8px; border-radius: 8px; border: 1px solid var(--border); background: transparent; color: var(--text); cursor: pointer; font-size: 14.5px; font-family: inherit; }
.quiz-q .quiz-opt:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); }
.quiz-q .quiz-opt.correct { border-color: #3ddc84; background: color-mix(in srgb, #3ddc84 15%, transparent); }
.quiz-q .quiz-opt.wrong { border-color: var(--major); background: color-mix(in srgb, var(--major) 15%, transparent); }
.quiz-score { text-align: center; font-size: 20px; font-weight: 800; padding: 20px; border: 1px solid var(--border); border-radius: 12px; background: color-mix(in srgb, var(--accent) 8%, var(--card-bg)); }
.narrative-section { border: 1px solid var(--border); border-radius: 12px; padding: 18px; margin-bottom: 20px; background: color-mix(in srgb, var(--major) 6%, var(--card-bg)); line-height: 1.85; font-size: 15px; }
.narrative-section h2 { font-size: 15.5px; margin: 0 0 10px; color: var(--major); }
.ics-btn { display: inline-block; }
.champ-section { margin-bottom: 28px; }
.champ-section h2 { font-size: 17px; margin: 0 0 4px; }
.champ-disclaimer { font-size: 12px; color: var(--text-dim); opacity: 0.75; margin-bottom: 14px; }
.champ-row { display: flex; gap: 14px; flex-wrap: wrap; }
.champ-card { flex: 1; min-width: 150px; max-width: 220px; border: 1px solid var(--border); border-radius: 16px; padding: 16px 14px; text-align: center; background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 10%, var(--card-bg)), var(--card-bg)); }
.champ-rank { font-size: 20px; margin-bottom: 2px; }
.champ-name { font-weight: 700; font-size: 14.5px; margin-bottom: 4px; word-break: break-word; }
.champ-class { font-size: 12.5px; color: var(--text-dim); margin-bottom: 10px; }
.champ-power { font-size: 22px; font-weight: 800; color: var(--major); }
.champ-power span { font-variant-numeric: tabular-nums; }
.champ-detail { font-size: 11.5px; color: var(--text-dim); margin-top: 6px; }
.cap-methodology { font-size: 13px; color: var(--text-dim); line-height: 1.7; border: 1px dashed var(--border); border-radius: 10px; padding: 12px 14px; margin-bottom: 26px; }
.cap-category { margin-bottom: 34px; }
.cap-category h2 { font-size: 19px; margin: 0 0 8px; }
.cap-summary { font-size: 14.5px; line-height: 1.75; margin: 0 0 10px; opacity: 0.92; }
.cap-scale-note { font-size: 12.5px; color: var(--text-dim); margin-bottom: 14px; }
.cap-tool-grid { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 10px; }
.cap-tool-card { flex: 1; min-width: 210px; max-width: 260px; border: 1px solid var(--border); border-radius: 14px; padding: 16px; background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 8%, var(--card-bg)), var(--card-bg)); }
.cap-tool-rank { font-size: 18px; margin-bottom: 2px; }
.cap-tool-name { font-weight: 700; font-size: 14.5px; margin-bottom: 4px; }
.cap-stars { color: var(--major); font-size: 15px; letter-spacing: 1px; margin-bottom: 4px; }
.cap-score-label { font-size: 11.5px; color: var(--text-dim); margin-bottom: 8px; }
.cap-verdict { font-size: 13px; line-height: 1.6; margin: 0; opacity: 0.9; }
.cap-sources { font-size: 12px; color: var(--text-dim); }
.cap-sources a { color: var(--accent); text-decoration: none; }
.cap-sources a:hover { text-decoration: underline; }
.dogfight-wrap { border: 1px solid var(--border); border-radius: 20px; padding: 8px; margin-bottom: 14px; background: radial-gradient(ellipse at center, color-mix(in srgb, var(--accent) 5%, transparent), transparent 70%); }
.dogfight-wrap canvas { display: block; width: 100%; height: 190px; border-radius: 14px; }
@media (max-width: 520px) { .dogfight-wrap canvas { height: 150px; } }
.timeline { display: flex; gap: 0; overflow-x: auto; padding: 20px 0 30px; }
.tl-point { flex: 0 0 220px; position: relative; padding: 0 16px; border-top: 2px solid var(--border); padding-top: 16px; }
.tl-dot { position: absolute; top: -6px; left: 16px; width: 10px; height: 10px; border-radius: 50%; background: var(--major); box-shadow: 0 0 8px color-mix(in srgb, var(--major) 60%, transparent); }
.tl-date { font-size: 12.5px; color: var(--text-dim); margin-bottom: 8px; }
.tl-card { border: 1px solid var(--border); border-radius: 10px; padding: 12px; background: var(--card-bg); }
.tl-source { font-size: 12px; color: var(--accent); margin-bottom: 6px; font-weight: 700; }
.tl-card a { color: var(--text); text-decoration: none; font-size: 14.5px; line-height: 1.5; }
.tl-card a:hover { color: var(--accent); text-decoration: underline; }
.wrap-carousel { display: flex; gap: 16px; overflow-x: auto; scroll-snap-type: x mandatory; padding-bottom: 20px; }
.wrap-card { flex: 0 0 85%; max-width: 360px; scroll-snap-align: center; border-radius: 20px; border: 1px solid var(--border); background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 12%, var(--card-bg)), color-mix(in srgb, var(--major) 10%, var(--card-bg))); padding: 40px 24px; text-align: center; min-height: 260px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; text-decoration: none; color: inherit; cursor: pointer; transition: transform 0.15s ease; }
.wrap-card:hover { transform: translateY(-4px); border-color: var(--accent); }
.wrap-emoji { font-size: 40px; }
.wrap-big { font-size: 34px; font-weight: 800; color: var(--text); word-break: break-word; }
.wrap-label { font-size: 14px; color: var(--text-dim); }
.warp-overlay { position: fixed; inset: 0; z-index: 9999; pointer-events: none; opacity: 0; background: radial-gradient(circle at center, #fff 0%, color-mix(in srgb, var(--accent) 60%, #fff) 15%, transparent 70%); }
.warp-overlay.active { animation: warpFlash 0.4s ease-out; }
@keyframes warpFlash { 0% { opacity: 0; transform: scale(0.3); } 40% { opacity: 0.9; transform: scale(1.6); } 100% { opacity: 0; transform: scale(2.6); } }
@media (prefers-reduced-motion: reduce) { .warp-overlay.active { animation: none; } }
@media print {
  canvas#starfield, .celestial-body, nav, .brand, .site-footer, .card-actions, .tool-row, .filters, .major-toggle, .search-box, .accent-picker { display: none !important; }
  body { background: #fff; color: #000; }
  .card { background: #fff; border: 1px solid #ccc; break-inside: avoid; }
  details { open: true; }
}
.freshness { display: inline-block; font-size: 12.5px; padding: 3px 10px; border-radius: 999px; margin-bottom: 10px; }
.freshness.fresh { background: color-mix(in srgb, #3ddc84 18%, transparent); color: #6fe08f; box-shadow: 0 0 10px color-mix(in srgb, #3ddc84 30%, transparent); }
.freshness.stale { background: color-mix(in srgb, var(--text-dim) 15%, transparent); color: var(--text-dim); }
.card.is-read { opacity: 0.5; }
.read-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--accent); margin-right: 6px; vertical-align: middle; }
.card.is-read .read-dot { display: none; }
.tool-row { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
.tool-btn { border: 1px solid var(--border); background: color-mix(in srgb, var(--accent) 6%, transparent); color: var(--text-dim); border-radius: 8px; padding: 7px 14px; font-size: 13.5px; cursor: pointer; text-decoration: none; display: inline-block; }
.tool-btn:hover { background: color-mix(in srgb, var(--accent) 18%, transparent); color: var(--text); }
.memory-section { border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 24px; background: color-mix(in srgb, var(--accent) 6%, var(--card-bg)); }
.memory-section h2 { font-size: 15.5px; margin: 0 0 10px; color: var(--accent); }
.speak-hint { font-size: 12.5px; color: var(--text-dim); opacity: 0.8; margin: -8px 0 16px; }
"""

STARFIELD_SCRIPT = """
(function() {
  const canvas = document.getElementById('starfield');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
  resize();
  window.addEventListener('resize', resize);
  const stars = Array.from({length: 140}, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: Math.random() * 1.3 + 0.3,
    baseA: Math.random() * 0.5 + 0.35,
    phase: Math.random() * Math.PI * 2,
    speed: Math.random() * 0.15 + 0.04,
    driftY: Math.random() * 0.03 + 0.008
  }));
  function frame(t) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#fff';
    stars.forEach(s => {
      const twinkle = reduceMotion ? s.baseA : s.baseA + Math.sin(t * 0.001 * s.speed * 10 + s.phase) * 0.35;
      ctx.globalAlpha = Math.max(0.12, Math.min(1, twinkle));
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
      if (!reduceMotion) {
        s.y += s.driftY;
        if (s.y > canvas.height) s.y = 0;
      }
    });
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
"""

FILTER_SCRIPT = """
let currentCat = 'all';
function applyFilter() {
  const majorOnly = document.getElementById('majorOnly')?.checked;
  document.querySelectorAll('.card').forEach(c => {
    const catOk = currentCat === 'all' || c.dataset.category === currentCat;
    const majorOk = !majorOnly || c.dataset.importance === 'major';
    c.style.display = (catOk && majorOk) ? '' : 'none';
  });
  document.querySelectorAll('.group-heading').forEach(h => {
    const anyVisible = [...document.querySelectorAll(`.card[data-group="${h.dataset.group}"]`)]
      .some(c => c.style.display !== 'none');
    h.style.display = anyVisible ? '' : 'none';
  });
}
document.querySelectorAll('.filters button').forEach(b => b.addEventListener('click', () => {
  currentCat = b.dataset.cat;
  document.querySelectorAll('.filters button').forEach(x => x.classList.toggle('active', x === b));
  applyFilter();
}));
document.getElementById('majorOnly')?.addEventListener('change', applyFilter);
"""

BOOKMARK_SCRIPT = """
function getBookmarks() {
  try { return new Set(JSON.parse(localStorage.getItem('ai_news_bookmarks') || '[]')); }
  catch (e) { return new Set(); }
}
function saveBookmarks(set) {
  localStorage.setItem('ai_news_bookmarks', JSON.stringify([...set]));
}
function refreshBookmarkButtons() {
  const bookmarks = getBookmarks();
  document.querySelectorAll('.bookmark-btn').forEach(btn => {
    const saved = bookmarks.has(btn.dataset.url);
    btn.classList.toggle('saved', saved);
    btn.textContent = saved ? '★' : '☆';
  });
  if (document.body.dataset.page === 'bookmarks') {
    document.querySelectorAll('.card').forEach(c => {
      c.style.display = bookmarks.has(c.dataset.url) ? '' : 'none';
    });
    const anySaved = document.querySelectorAll('.card').length > 0 &&
      [...document.querySelectorAll('.card')].some(c => c.style.display !== 'none');
    const emptyMsg = document.getElementById('noBookmarks');
    if (emptyMsg) emptyMsg.style.display = anySaved ? 'none' : '';
  }
}
document.querySelectorAll('.bookmark-btn').forEach(btn => btn.addEventListener('click', () => {
  const bookmarks = getBookmarks();
  const url = btn.dataset.url;
  if (bookmarks.has(url)) bookmarks.delete(url); else bookmarks.add(url);
  saveBookmarks(bookmarks);
  refreshBookmarkButtons();
}));
refreshBookmarkButtons();
"""

SHARE_SCRIPT = """
document.querySelectorAll('.share-btn').forEach(btn => btn.addEventListener('click', async () => {
  const url = btn.dataset.url;
  const title = btn.dataset.title;
  if (navigator.share) {
    try { await navigator.share({ title, url }); return; } catch (e) { /* user cancelled or failed, fall through */ }
  }
  try {
    await navigator.clipboard.writeText(url);
    const original = btn.textContent;
    btn.textContent = '✅';
    setTimeout(() => { btn.textContent = original; }, 1500);
  } catch (e) {
    prompt('คัดลอกลิงก์นี้ไปแชร์ได้เลย:', url);
  }
}));
"""

READ_SCRIPT = """
function getReadSet() {
  try { return new Set(JSON.parse(localStorage.getItem('ai_news_read') || '[]')); }
  catch (e) { return new Set(); }
}
function markRead(url) {
  const read = getReadSet();
  if (read.has(url)) return;
  read.add(url);
  localStorage.setItem('ai_news_read', JSON.stringify([...read]));
}
function refreshReadMarks() {
  const read = getReadSet();
  document.querySelectorAll('.card').forEach(c => {
    c.classList.toggle('is-read', read.has(c.dataset.url));
  });
}
document.querySelectorAll('.card h3 a').forEach(a => a.addEventListener('click', () => {
  const card = a.closest('.card');
  if (card) { markRead(card.dataset.url); card.classList.add('is-read'); }
}));
refreshReadMarks();
"""

RANDOM_SCRIPT = """
document.getElementById('randomOldNews')?.addEventListener('click', () => {
  const data = document.getElementById('all-urls');
  if (!data) return;
  const urls = JSON.parse(data.textContent);
  if (!urls.length) return;
  const pick = urls[Math.floor(Math.random() * urls.length)];
  window.open(pick, '_blank', 'noopener');
});
"""

SPEAK_SCRIPT = """
let _voiceCache = [];
function _refreshVoiceCache() { _voiceCache = window.speechSynthesis.getVoices(); }
if ('speechSynthesis' in window) {
  _refreshVoiceCache();
  window.speechSynthesis.onvoiceschanged = _refreshVoiceCache;
}
function waitForVoices() {
  return new Promise(resolve => {
    if (_voiceCache.length) { resolve(_voiceCache); return; }
    let tries = 0;
    const iv = setInterval(() => {
      _refreshVoiceCache();
      tries++;
      if (_voiceCache.length || tries > 10) { clearInterval(iv); resolve(_voiceCache); }
    }, 150);
  });
}
function pickVoiceForLang(prefix) {
  return _voiceCache.find(v => v.lang && v.lang.toLowerCase().startsWith(prefix)) || null;
}
function pickThaiVoice() {
  return pickVoiceForLang('th');
}
function currentSiteLang() {
  const m = document.cookie.match(/googtrans=\/th\/(\w+)/);
  return (m && m[1] === 'en') ? 'en' : 'th';
}
function pickSpeechVoice() {
  if (currentSiteLang() === 'en') {
    const en = pickVoiceForLang('en');
    if (en) return { voice: en, lang: en.lang };
  }
  const th = pickThaiVoice();
  return th ? { voice: th, lang: 'th-TH' } : null;
}
const NO_THAI_VOICE_MSG = 'เครื่อง/เบราว์เซอร์นี้ไม่มีเสียงพูดที่ใช้งานได้ ลองเปิดเว็บนี้จากมือถือแทนดูครับ (Android/iPhone ส่วนใหญ่มีเสียงไทยอยู่แล้ว) หรือลองเปลี่ยนเป็น Chrome/Edge บนคอม';
async function speakBookmarked() {
  if (!('speechSynthesis' in window)) {
    alert('เบราว์เซอร์นี้ไม่รองรับการอ่านออกเสียง ลองเปิดจาก Chrome หรือ Safari บนมือถือดูครับ');
    return;
  }
  const cards = [...document.querySelectorAll('.card')].filter(c => c.style.display !== 'none');
  if (!cards.length) { alert('ยังไม่มีข่าวที่บันทึกไว้ให้ฟัง'); return; }
  await waitForVoices();
  const picked = pickSpeechVoice();
  if (!picked) { alert(NO_THAI_VOICE_MSG); return; }
  window.speechSynthesis.cancel();
  const btn = document.getElementById('speakBookmarks');
  cards.forEach((card, idx) => {
    const title = card.querySelector('h3 a')?.textContent || '';
    const summary = card.querySelector('p')?.textContent || '';
    const utter = new SpeechSynthesisUtterance(`${title}. ${summary}`);
    utter.lang = picked.lang;
    utter.voice = picked.voice;
    if (idx === 0 && btn) utter.onstart = () => { btn.textContent = '⏸ กำลังอ่าน... (กดเพื่อหยุด)'; };
    if (idx === cards.length - 1 && btn) utter.onend = () => { btn.textContent = '🔊 ฟังข่าวที่บันทึกไว้ทั้งหมด'; };
    window.speechSynthesis.speak(utter);
  });
}
document.getElementById('speakBookmarks')?.addEventListener('click', () => {
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    const btn = document.getElementById('speakBookmarks');
    if (btn) btn.textContent = '🔊 ฟังข่าวที่บันทึกไว้ทั้งหมด';
    return;
  }
  speakBookmarked();
});
"""

DIALOGUE_SCRIPT = """
const DIALOGUE_TEXT = {
  th: {
    greetingFresh: title => `สวัสดีค่ะ ดิฉันพิธีกรจาก MEW Station ${title}`,
    greetingStale: 'สวัสดีค่ะ ดิฉันพิธีกรจาก MEW Station วันนี้ยังไม่มีข่าวใหม่ค่ะ แต่จะขอนำข่าวล่าสุดที่มีมาสรุปให้ฟังกันนะคะ',
    count: n => `มีข่าวทั้งหมด ${n} ข่าววันนี้ค่ะ`,
    closing: 'วันนี้ก็จบสรุปข่าวแค่นี้ค่ะ แล้วเจอกันใหม่',
    noVoice: 'เบราว์เซอร์นี้ไม่รองรับการอ่านออกเสียง',
    noNews: 'ไม่มีข่าววันนี้ให้ฟัง',
    listeningBtn: '⏸ กำลังฟัง... (กดเพื่อหยุด)',
    idleBtn: '🎙️ ฟังพิธีกรอ่านข่าว',
  },
  en: {
    greetingFresh: title => `Hello, I'm your host from MEW Station. ${title}`,
    greetingStale: "Hello, I'm your host from MEW Station. There's no new news today, but I'll go ahead and read you the latest news we have.",
    count: n => `There ${n === 1 ? 'is' : 'are'} ${n} ${n === 1 ? 'story' : 'stories'} today.`,
    closing: "That wraps up today's news. See you next time.",
    noVoice: "This browser doesn't support reading text aloud.",
    noNews: 'There is no news to listen to today.',
    listeningBtn: '⏸ Listening... (click to stop)',
    idleBtn: '🎙️ Listen to the host read the news',
  },
};

function playJingle() {
  return new Promise(resolve => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const notes = [523, 659, 784];
      notes.forEach((freq, i) => {
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.type = 'sine'; o.frequency.value = freq;
        const start = ctx.currentTime + i * 0.18;
        g.gain.setValueAtTime(0.001, start);
        g.gain.linearRampToValueAtTime(0.15, start + 0.02);
        g.gain.exponentialRampToValueAtTime(0.001, start + 0.16);
        o.connect(g); g.connect(ctx.destination);
        o.start(start); o.stop(start + 0.17);
      });
      setTimeout(resolve, notes.length * 180 + 200);
    } catch (e) { resolve(); }
  });
}

let _dialogueActive = false;
let _dialogueStop = false;

function speakQueue(lines, picked) {
  return new Promise(resolve => {
    let i = 0;
    function next() {
      if (_dialogueStop || i >= lines.length) { resolve(); return; }
      const [text, pitch] = lines[i++];
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = picked.lang;
      utter.pitch = pitch;
      utter.voice = picked.voice;
      utter.onend = next;
      utter.onerror = next;
      window.speechSynthesis.speak(utter);
    }
    next();
  });
}

document.getElementById('dialogueListen')?.addEventListener('click', async (e) => {
  const btn = e.currentTarget;
  const lang = currentSiteLang();
  const T = DIALOGUE_TEXT[lang];
  if (_dialogueActive) {
    _dialogueStop = true;
    window.speechSynthesis.cancel();
    _dialogueActive = false;
    btn.textContent = T.idleBtn;
    return;
  }
  if (!('speechSynthesis' in window)) { alert(T.noVoice); return; }
  await waitForVoices();
  const picked = pickSpeechVoice();
  if (!picked) { alert(NO_THAI_VOICE_MSG); return; }
  window.speechSynthesis.cancel();
  const items = [...document.querySelectorAll('.card')].filter(c => c.style.display !== 'none');
  if (!items.length) { alert(T.noNews); return; }
  _dialogueActive = true;
  _dialogueStop = false;
  btn.textContent = T.listeningBtn;
  const isStale = !!document.querySelector('.freshness.stale');
  const lines = [];
  const title0 = document.querySelector('h1')?.textContent || '';
  lines.push([isStale ? T.greetingStale : T.greetingFresh(title0), 1.0]);
  lines.push([T.count(items.length), 1.0]);
  items.forEach(card => {
    const t = card.querySelector('h3 a')?.textContent || '';
    const s = card.querySelector('p')?.textContent || '';
    lines.push([`${t}. ${s}`, 1.0]);
  });
  lines.push([T.closing, 1.0]);
  await playJingle();
  await speakQueue(lines, picked);
  _dialogueActive = false;
  btn.textContent = T.idleBtn;
});
"""

LISTEN_SCRIPT = """
document.querySelectorAll('.listen-btn').forEach(btn => btn.addEventListener('click', async () => {
  if (!('speechSynthesis' in window)) {
    alert('เบราว์เซอร์นี้ไม่รองรับการอ่านออกเสียง');
    return;
  }
  if (btn.classList.contains('speaking')) {
    window.speechSynthesis.cancel();
    btn.classList.remove('speaking');
    return;
  }
  await waitForVoices();
  const picked = pickSpeechVoice();
  if (!picked) { alert(NO_THAI_VOICE_MSG); return; }
  window.speechSynthesis.cancel();
  document.querySelectorAll('.listen-btn.speaking').forEach(b => b.classList.remove('speaking'));
  const card = btn.closest('.card');
  const title = card?.querySelector('h3 a')?.textContent || '';
  const summary = card?.querySelector('p')?.textContent || '';
  const text = (title || summary) ? `${title}. ${summary}` : btn.dataset.text;
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = picked.lang;
  utter.voice = picked.voice;
  utter.onstart = () => btn.classList.add('speaking');
  utter.onend = () => btn.classList.remove('speaking');
  window.speechSynthesis.speak(utter);
}));
"""

LIKE_SCRIPT = """
function getLikes() {
  try { return JSON.parse(localStorage.getItem('ai_news_likes') || '{}'); }
  catch (e) { return {}; }
}
function saveLikes(obj) { localStorage.setItem('ai_news_likes', JSON.stringify(obj)); }
function refreshLikeButtons() {
  const likes = getLikes();
  document.querySelectorAll('.like-btn').forEach(btn => {
    const current = likes[btn.dataset.url];
    btn.classList.toggle('active', current === btn.dataset.v);
  });
}
document.querySelectorAll('.like-btn').forEach(btn => btn.addEventListener('click', () => {
  const likes = getLikes();
  const url = btn.dataset.url;
  likes[url] = likes[url] === btn.dataset.v ? undefined : btn.dataset.v;
  if (likes[url] === undefined) delete likes[url];
  saveLikes(likes);
  refreshLikeButtons();
}));
refreshLikeButtons();
"""

SEARCH_SCRIPT = """
const searchBox = document.getElementById('searchBox');
searchBox?.addEventListener('input', () => {
  const q = searchBox.value.trim().toLowerCase();
  let anyVisible = false;
  document.querySelectorAll('.month-group').forEach(group => {
    let groupHasMatch = false;
    group.querySelectorAll('.card').forEach(card => {
      const text = card.textContent.toLowerCase();
      const match = !q || text.includes(q);
      card.style.display = match ? '' : 'none';
      if (match) groupHasMatch = true;
    });
    group.style.display = groupHasMatch ? '' : 'none';
    if (q && groupHasMatch) group.open = true;
    if (groupHasMatch) anyVisible = true;
  });
  const emptyMsg = document.getElementById('searchEmpty');
  if (emptyMsg) emptyMsg.hidden = anyVisible || !q;
});

if (location.hash) {
  const target = document.querySelector(location.hash);
  if (target && target.tagName === 'DETAILS') {
    target.open = true;
    setTimeout(() => target.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
  }
}
"""

QUICKREAD_SCRIPT = """
document.getElementById('quickReadToggle')?.addEventListener('click', () => {
  const el = document.getElementById('quickRead');
  if (!el) return;
  el.hidden = !el.hidden;
});
document.getElementById('qrToggle')?.addEventListener('click', () => {
  const el = document.getElementById('qrBox');
  if (!el) return;
  el.hidden = !el.hidden;
});
"""

PRINT_SCRIPT = """
document.getElementById('printPdf')?.addEventListener('click', () => {
  document.querySelectorAll('details.month-group').forEach(d => d.open = true);
  window.print();
});
"""

STREAK_SCRIPT = """
(function() {
  const KEY = 'ai_news_visit_streak';
  const today = new Date().toISOString().slice(0, 10);
  let data;
  try { data = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { data = {}; }
  if (data.lastVisit !== today) {
    const y = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    data.streak = data.lastVisit === y ? (data.streak || 0) + 1 : 1;
    data.lastVisit = today;
    localStorage.setItem(KEY, JSON.stringify(data));
  }
  const streak = data.streak || 1;
  const ranks = [
    [1, 'นักบินฝึกหัด 🧑‍🚀'], [3, 'นักบินสำรวจ 🛸'], [7, 'นักบินอาวุโส 🚀'],
    [14, 'ผู้บังคับการยาน 🪐'], [30, 'กัปตันยานข่าว AI 👨‍🚀✨']
  ];
  let rank = ranks[0][1];
  ranks.forEach(([days, name]) => { if (streak >= days) rank = name; });
  const el = document.getElementById('streakBadge');
  if (el) el.textContent = `${rank} · เข้าดูข่าวติดต่อกัน ${streak} วัน`;
})();
"""

ACCENT_SCRIPT = """
(function() {
  const options = [
    { name: 'ฟ้า', accent: '#4fd1ff' },
    { name: 'ชมพู', accent: '#ff4fd8' },
    { name: 'เขียวมรกต', accent: '#35ffb0' },
    { name: 'เหลืองอำพัน', accent: '#ffb020' }
  ];
  const saved = localStorage.getItem('ai_news_accent');
  if (saved) document.documentElement.style.setProperty('--accent', saved);
  const picker = document.getElementById('accentPicker');
  if (!picker) return;
  options.forEach(opt => {
    const btn = document.createElement('button');
    btn.style.background = opt.accent;
    btn.title = opt.name;
    btn.setAttribute('aria-label', 'เปลี่ยนสีธีมเป็น' + opt.name);
    if (saved === opt.accent || (!saved && opt.accent === '#4fd1ff')) btn.classList.add('active');
    btn.addEventListener('click', () => {
      document.documentElement.style.setProperty('--accent', opt.accent);
      localStorage.setItem('ai_news_accent', opt.accent);
      picker.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
    picker.appendChild(btn);
  });
})();
"""

LANG_SCRIPT = """
(function() {
  function currentLang() {
    const m = document.cookie.match(/googtrans=\\/th\\/(\\w+)/);
    return m ? m[1] : 'th';
  }
  function setLang(lang) {
    if (lang === currentLang()) return;
    document.cookie = 'googtrans=/th/' + lang + '; path=/';
    location.reload();
  }
  const buttons = document.querySelectorAll('.lang-toggle button');
  const active = currentLang();
  buttons.forEach(function(b) {
    if (b.dataset.lang === active) b.classList.add('active');
    b.addEventListener('click', function() { setLang(b.dataset.lang); });
  });
})();
"""

FOLLOW_SCRIPT = """
(function() {
  const dataEl = document.getElementById('all-sources');
  const panel = document.getElementById('followPanel');
  const toggleBtn = document.getElementById('followToggle');
  if (!dataEl || !panel || !toggleBtn) return;
  const sources = JSON.parse(dataEl.textContent);
  if (!sources.length) { toggleBtn.hidden = true; return; }

  function getFollowed() {
    try { return JSON.parse(localStorage.getItem('ai_news_follow') || '[]'); }
    catch (e) { return []; }
  }
  function saveFollowed(list) { localStorage.setItem('ai_news_follow', JSON.stringify(list)); }

  const followed = new Set(getFollowed());
  const checks = sources.map(s => `<label><input type="checkbox" value="${s}" ${followed.has(s) ? 'checked' : ''}> ${s}</label>`).join('');
  panel.innerHTML = `<div>${checks}</div><div class="fp-actions"><button id="fpAll">เลือกทั้งหมด</button><button id="fpNone">ล้างทั้งหมด (แสดงทุกบริษัท)</button></div>`;

  function applyFilter() {
    const current = new Set(getFollowed());
    document.querySelectorAll('.card[data-source]').forEach(card => {
      const show = current.size === 0 || current.has(card.dataset.source);
      if (!show) card.style.display = 'none';
    });
  }
  panel.querySelectorAll('input[type=checkbox]').forEach(cb => cb.addEventListener('change', () => {
    const list = [...panel.querySelectorAll('input[type=checkbox]:checked')].map(c => c.value);
    saveFollowed(list);
    document.querySelectorAll('.card[data-source]').forEach(c => { c.style.display = ''; });
    applyFilter();
  }));
  document.getElementById('fpAll')?.addEventListener('click', () => {
    panel.querySelectorAll('input[type=checkbox]').forEach(cb => cb.checked = true);
    saveFollowed(sources);
    applyFilter();
  });
  document.getElementById('fpNone')?.addEventListener('click', () => {
    panel.querySelectorAll('input[type=checkbox]').forEach(cb => cb.checked = false);
    saveFollowed([]);
    document.querySelectorAll('.card[data-source]').forEach(c => { c.style.display = ''; });
  });
  toggleBtn.addEventListener('click', () => panel.classList.toggle('open'));
  applyFilter();
})();
"""

QUIZ_SCRIPT = """
(function() {
  const dataEl = document.getElementById('quiz-data');
  const arena = document.getElementById('quizArena');
  if (!dataEl || !arena) return;
  const questions = JSON.parse(dataEl.textContent);
  let score = 0, answered = 0;

  function renderQuestion(q, idx) {
    const div = document.createElement('div');
    div.className = 'quiz-q';
    div.innerHTML = `<h3>${idx + 1}. ${q.q}</h3>` + q.options.map(opt =>
      `<button class="quiz-opt" data-opt="${opt}">${opt}</button>`
    ).join('');
    div.querySelectorAll('.quiz-opt').forEach(btn => btn.addEventListener('click', () => {
      if (div.dataset.done) return;
      div.dataset.done = '1';
      answered++;
      const correct = btn.dataset.opt === q.answer;
      if (correct) score++;
      div.querySelectorAll('.quiz-opt').forEach(b => {
        if (b.dataset.opt === q.answer) b.classList.add('correct');
        else if (b === btn) b.classList.add('wrong');
      });
      if (answered === questions.length) {
        const scoreDiv = document.createElement('div');
        scoreDiv.className = 'quiz-score';
        scoreDiv.textContent = `คะแนนของคุณ: ${score} / ${questions.length}`;
        arena.appendChild(scoreDiv);
      }
    }));
    return div;
  }
  questions.forEach((q, idx) => arena.appendChild(renderQuestion(q, idx)));
})();
"""

WARP_SCRIPT = """
(function() {
  const overlay = document.createElement('div');
  overlay.className = 'warp-overlay';
  document.body.appendChild(overlay);
  document.querySelectorAll('nav a').forEach(a => {
    a.addEventListener('click', (e) => {
      if (a.classList.contains('active')) return;
      e.preventDefault();
      const href = a.getAttribute('href');
      overlay.classList.add('active');
      setTimeout(() => { window.location.href = href; }, 260);
    });
  });
})();
"""

DOGFIGHT_SCRIPT = """
(function() {
  const dataEl = document.getElementById('dogfight-data');
  const canvas = document.getElementById('dogfightCanvas');
  if (!dataEl || !canvas) return;
  const champs = JSON.parse(dataEl.textContent);
  if (champs.length < 2) return;

  const ctx = canvas.getContext('2d');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let W = 0, H = 0;

  function resize() {
    const rect = canvas.getBoundingClientRect();
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    W = rect.width; H = rect.height;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    layout();
  }

  const homePositions3 = [[0.24,0.62],[0.76,0.62],[0.5,0.24]];
  const homePositions2 = [[0.3,0.5],[0.7,0.5]];
  let ships = [];

  function layout() {
    const positions = champs.length >= 3 ? homePositions3 : homePositions2;
    const maxPower = Math.max(...champs.map(c => c.power)) || 1;
    ships = champs.map((c, i) => {
      const [hx, hy] = positions[i];
      const scale = 0.75 + (c.power / maxPower) * 0.55;
      return {
        name: c.name, medal: c.medal, power: c.power, color: c.color, dark: shade(c.color),
        homeX: W*hx, homeY: H*hy, x: W*hx, y: H*hy,
        dir: i % 2 === 0 ? 1 : -1, t: i*2, tSpeed: 0.65+Math.random()*0.25, bank: 0,
        scale, fireGap: 1700 - (c.power/maxPower)*1000, nextFire: 300 + i*400,
      };
    });
  }

  function shade(hex) {
    const map = {'#4fd1ff':'#0a2a38','#ff4fd8':'#380a2e','#35ffb0':'#0a3826','#ffb020':'#3a2405'};
    return map[hex] || '#101018';
  }

  const stars = Array.from({length: 60}, () => ({x: Math.random(), y: Math.random(), r: Math.random()*1.1+0.3, a: Math.random()*0.5+0.2}));
  let bolts = [], sparks = [];

  function drawShip(s) {
    ctx.save();
    ctx.translate(s.x, s.y);
    ctx.rotate(s.bank * 0.3 * s.dir);
    ctx.scale(s.dir * s.scale, s.scale);

    const flicker = 2.5 + Math.sin(performance.now()*0.02 + s.t) * 1.2;
    const flameGrad = ctx.createRadialGradient(-30,0,1,-30,0,9+flicker);
    flameGrad.addColorStop(0, '#fff');
    flameGrad.addColorStop(0.3, s.color);
    flameGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = flameGrad;
    ctx.beginPath();
    ctx.ellipse(-30, 0, 8+flicker, 4+flicker*0.4, 0, 0, Math.PI*2);
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(34, 0);
    ctx.lineTo(10, -3); ctx.lineTo(2, -6); ctx.lineTo(-22, -24); ctx.lineTo(-14, -8);
    ctx.lineTo(-30, -4); ctx.lineTo(-34, 0); ctx.lineTo(-30, 4);
    ctx.lineTo(-14, 8); ctx.lineTo(-22, 24); ctx.lineTo(2, 6); ctx.lineTo(10, 3);
    ctx.closePath();
    const hullGrad = ctx.createLinearGradient(-20,0,34,0);
    hullGrad.addColorStop(0, s.dark);
    hullGrad.addColorStop(0.6, s.color);
    hullGrad.addColorStop(1, '#f5feff');
    ctx.fillStyle = hullGrad;
    ctx.fill();
    ctx.strokeStyle = s.color;
    ctx.lineWidth = 1.3;
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(30,0); ctx.lineTo(-28,0);
    ctx.strokeStyle = 'rgba(255,255,255,0.35)';
    ctx.lineWidth = 0.8;
    ctx.stroke();

    const glassGrad = ctx.createLinearGradient(10,-4,24,4);
    glassGrad.addColorStop(0, 'rgba(190,245,255,0.95)');
    glassGrad.addColorStop(1, 'rgba(255,255,255,0.55)');
    ctx.beginPath();
    ctx.ellipse(18, 0, 7, 3, 0, 0, Math.PI*2);
    ctx.fillStyle = glassGrad;
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.5)';
    ctx.lineWidth = 0.6;
    ctx.stroke();
    ctx.restore();

    ctx.save();
    ctx.font = '600 11px "Leelawadee UI", sans-serif';
    ctx.textAlign = 'center';
    const labelY = s.y - 34*s.scale - 6;
    const label = `${s.medal} ${s.name} · ${s.power}`;
    const textW = ctx.measureText(label).width;
    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.fillRect(s.x - textW/2 - 6, labelY - 12, textW + 12, 16);
    ctx.fillStyle = s.color;
    ctx.fillText(label, s.x, labelY);
    ctx.restore();
  }

  function weightedTarget(from) {
    const others = ships.filter(s => s !== from);
    const stronger = others.filter(s => s.power > from.power);
    const pool = stronger.length ? stronger : others;
    return pool[Math.floor(Math.random()*pool.length)];
  }

  function fire(from) {
    const to = weightedTarget(from);
    if (!to) return;
    const dx = to.x - from.x, dy = to.y - from.y;
    const dist = Math.hypot(dx, dy) || 1;
    bolts.push({ x: from.x + (dx/dist)*32*from.dir, y: from.y, vx: (dx/dist)*7.5, vy: (dy/dist)*7.5, color: from.color, target: to });
  }

  function addSpark(x, y, color) {
    for (let i=0;i<10;i++) {
      const ang = Math.random()*Math.PI*2, spd = 1+Math.random()*2.2;
      sparks.push({x,y,vx:Math.cos(ang)*spd,vy:Math.sin(ang)*spd,life:1,color});
    }
  }

  function update(dt, now) {
    ships.forEach(s => {
      s.t += dt*s.tSpeed;
      s.x = s.homeX + Math.sin(s.t*0.6)*Math.min(34, W*0.06) + Math.sin(s.t*1.9)*8;
      s.y = s.homeY + Math.sin(s.t*1.05+1)*Math.min(22, H*0.18);
      s.bank = Math.cos(s.t*1.05+1);
      if (now > s.nextFire) { fire(s); s.nextFire = now + s.fireGap + Math.random()*300; }
    });
    bolts.forEach(b => { b.x += b.vx; b.y += b.vy; });
    bolts = bolts.filter(b => {
      const d = Math.hypot(b.x - b.target.x, b.y - b.target.y);
      if (d < 18) { addSpark(b.target.x, b.target.y, b.color); return false; }
      return b.x > -20 && b.x < W+20 && b.y > -20 && b.y < H+20;
    });
    sparks.forEach(s => { s.x += s.vx; s.y += s.vy; s.life -= 0.045; });
    sparks = sparks.filter(s => s.life > 0);
  }

  function draw(now) {
    ctx.clearRect(0,0,W,H);
    ctx.fillStyle = '#000';
    ctx.fillRect(0,0,W,H);
    stars.forEach(s => {
      ctx.globalAlpha = s.a + Math.sin(now*0.001+s.x*10)*0.15;
      ctx.fillStyle = '#fff';
      ctx.beginPath(); ctx.arc(s.x*W, s.y*H, s.r, 0, Math.PI*2); ctx.fill();
    });
    ctx.globalAlpha = 1;
    bolts.forEach(b => {
      ctx.save(); ctx.translate(b.x,b.y); ctx.rotate(Math.atan2(b.vy,b.vx));
      ctx.fillStyle = b.color; ctx.shadowColor = b.color; ctx.shadowBlur = 9;
      ctx.fillRect(-9,-1.5,18,3); ctx.restore();
    });
    ctx.shadowBlur = 0;
    sparks.forEach(s => {
      ctx.globalAlpha = Math.max(0,s.life); ctx.fillStyle = s.color;
      ctx.beginPath(); ctx.arc(s.x,s.y,2,0,Math.PI*2); ctx.fill();
    });
    ctx.globalAlpha = 1;
    ships.forEach(drawShip);
  }

  resize();
  window.addEventListener('resize', resize);
  let last = performance.now();
  function frame(now) {
    const dt = Math.min(0.05, (now-last)/1000);
    last = now;
    if (!reduceMotion) update(dt, now);
    draw(now);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
"""

MASCOT_SCRIPT = """
(function() {
  const hasMajor = document.querySelector('.card.major');
  const el = document.getElementById('mascot');
  if (!el) return;
  el.textContent = hasMajor ? '🧑‍🚀✨' : '🧑‍🚀';
  el.title = hasMajor ? 'มีข่าวใหญ่วันนี้!' : 'วันนี้ข่าวปกติ';
  if (hasMajor && !sessionStorage.getItem('ai_news_beeped')) {
    sessionStorage.setItem('ai_news_beeped', '1');
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = 'sine'; o.frequency.value = 880;
      g.gain.setValueAtTime(0.06, ctx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      o.connect(g); g.connect(ctx.destination);
      o.start(); o.stop(ctx.currentTime + 0.5);
    } catch (e) {}
  }
})();
"""


def nav_html(active: str) -> str:
    links = [
        ("index.html", "วันนี้", "index"),
        ("weekly.html", "รายสัปดาห์", "weekly"),
        ("archive.html", "คลังข่าวย้อนหลัง", "archive"),
        ("stats.html", "สถิติ", "stats"),
        ("timeline.html", "ไทม์ไลน์", "timeline"),
        ("wrapped.html", "สรุปประจำเดือน", "wrapped"),
        ("capabilities.html", "ความสามารถ AI", "capabilities"),
        ("quiz.html", "ควิซ", "quiz"),
        ("bookmarks.html", "บันทึกไว้อ่าน", "bookmarks"),
    ]
    return "<nav>" + "".join(
        f'<a href="{href}" class="{"active" if key == active else ""}">{label}</a>'
        for href, label, key in links
    ) + "</nav>"


SITE_NAME = "MEW Station"


def page_shell(title: str, active: str, body: str, random_urls: list = None) -> str:
    urls_script = ""
    if random_urls is not None:
        urls_script = f'<script type="application/json" id="all-urls">{json.dumps(random_urls, ensure_ascii=False)}</script>'
    sources_script = f'<script type="application/json" id="all-sources">{json.dumps(ALL_SOURCES, ensure_ascii=False)}</script>'
    return f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(SITE_NAME)} — {esc(title)}</title>
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="icon-192.png">
<meta name="theme-color" content="#4fd1ff">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{esc(SITE_NAME)}">
<style>{SHARED_STYLE}</style>
</head>
<body data-page="{active}">
<canvas id="starfield"></canvas>
<div class="celestial-body body-earth"></div>
<div class="celestial-body body-moon"></div>
<div class="celestial-body body-sun"></div>
<div class="celestial-body body-saturn"></div>
<div class="celestial-body body-uranus"></div>
<div class="celestial-body body-mars"></div>
<div class="lang-toggle" id="langToggle">
  <button data-lang="th" title="ภาษาไทย" aria-label="เปลี่ยนเป็นภาษาไทย">TH</button>
  <button data-lang="en" title="English" aria-label="Switch to English">EN</button>
</div>
<div class="brand">🛰️ {esc(SITE_NAME)} <span id="mascot" title=""></span></div>
<div class="streak-badge" id="streakBadge"></div>
<div class="accent-picker" id="accentPicker"></div>
<button id="followToggle" class="follow-toggle">⚙️ ติดตามเฉพาะบริษัท</button>
<div id="followPanel" class="follow-panel"></div>
{nav_html(active)}
{body}
<footer class="site-footer">🛰️ {esc(SITE_NAME)} · ดูแลและคัดสรรข่าวโดย MEW · อัปเดตอัตโนมัติทุกวัน</footer>
{urls_script}
{sources_script}
<div id="google_translate_element"></div>
<script>function googleTranslateElementInit(){{new google.translate.TranslateElement({{pageLanguage:'th',includedLanguages:'en',autoDisplay:false}},'google_translate_element');}}</script>
<script src="https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit" async></script>
<script>{STARFIELD_SCRIPT}</script>
<script>{FILTER_SCRIPT}</script>
<script>{BOOKMARK_SCRIPT}</script>
<script>{SHARE_SCRIPT}</script>
<script>{READ_SCRIPT}</script>
<script>{RANDOM_SCRIPT}</script>
<script>{SPEAK_SCRIPT}</script>
<script>{DIALOGUE_SCRIPT}</script>
<script>{LISTEN_SCRIPT}</script>
<script>{LIKE_SCRIPT}</script>
<script>{SEARCH_SCRIPT}</script>
<script>{QUICKREAD_SCRIPT}</script>
<script>{PRINT_SCRIPT}</script>
<script>{STREAK_SCRIPT}</script>
<script>{ACCENT_SCRIPT}</script>
<script>{MASCOT_SCRIPT}</script>
<script>{DOGFIGHT_SCRIPT}</script>
<script>{FOLLOW_SCRIPT}</script>
<script>{QUIZ_SCRIPT}</script>
<script>{WARP_SCRIPT}</script>
<script>{LANG_SCRIPT}</script>
</body>
</html>
"""


def filters_html(categories_present: set, show_major_toggle: bool = False) -> str:
    buttons = ['<button data-cat="all" class="active">ทั้งหมด</button>']
    for cat, label in CATEGORY_LABELS.items():
        if cat in categories_present:
            buttons.append(f'<button data-cat="{cat}">{esc(label)}</button>')
    html = '<div class="filters">' + "".join(buttons) + "</div>"
    if show_major_toggle:
        html += '<label class="major-toggle"><input type="checkbox" id="majorOnly"> แสดงเฉพาะข่าวใหญ่ 🔥</label>'
    return html


def compute_related(item: dict, all_items: list, limit: int = 2) -> list:
    same_cat_source = [
        i for i in all_items
        if i is not item and i.get("url") != item.get("url")
        and (i.get("category") == item.get("category") or i.get("source") == item.get("source"))
    ]
    same_cat_source.sort(key=lambda i: i["date"], reverse=True)
    return same_cat_source[:limit]


def card_html(item: dict, group: str = "", all_items: list = None) -> str:
    cat = item.get("category", "other")
    label = CATEGORY_LABELS.get(cat, "อื่นๆ")
    importance = item.get("importance", "normal")
    is_major = importance == "major"
    group_attr = f' data-group="{esc(group)}"' if group else ""
    major_class = " major" if is_major else ""
    major_badge = '<span class="badge major">🔥 ข่าวใหญ่</span>' if is_major else ""
    url = esc(item.get("url", "#"))
    title_th = item.get("title_th", "")
    summary_th = item.get("summary_th", "")
    share_title = esc(title_th)
    speak_text = esc(f"{title_th}. {summary_th}")
    context = item.get("context_th", "").strip()
    context_html = f'<p class="context">🔗 {esc(context)}</p>' if context else ""

    related_html = ""
    if all_items is not None:
        related = compute_related(item, all_items)
        if related:
            links = "".join(
                f'<li><a href="{esc(r.get("url","#"))}" target="_blank" rel="noopener">{esc(r.get("title_th",""))}</a></li>'
                for r in related
            )
            related_html = f'<div class="related"><span>ข่าวใกล้เคียง:</span><ul>{links}</ul></div>'

    return f"""<div class="card{major_class}" data-category="{esc(cat)}" data-importance="{esc(importance)}" data-url="{url}" data-source="{esc(item.get('source',''))}"{group_attr}>
  <div class="card-actions">
    <button class="bookmark-btn" data-url="{url}" title="บันทึกไว้อ่านทีหลัง" aria-label="บันทึกไว้อ่านทีหลัง">☆</button>
    <button class="like-btn" data-url="{url}" data-v="up" title="ชอบข่าวนี้" aria-label="ชอบข่าวนี้">👍</button>
    <button class="like-btn" data-url="{url}" data-v="down" title="ไม่สนใจข่าวแบบนี้" aria-label="ไม่สนใจข่าวแบบนี้">👎</button>
    <button class="listen-btn" data-text="{speak_text}" title="ฟังข่าวนี้" aria-label="ฟังข่าวนี้">🔈</button>
    <button class="share-btn" data-url="{url}" data-title="{share_title}" title="แชร์ข่าวนี้" aria-label="แชร์ข่าวนี้">🔗</button>
  </div>
  {major_badge}<span class="badge">{esc(label)}</span>
  <h3><a href="{url}" target="_blank" rel="noopener">{esc(title_th)}</a></h3>
  <p>{esc(summary_th)}</p>
  {context_html}
  <div class="meta">{esc(item.get('source', ''))} · {thai_date(item['date'])}</div>
  {related_html}
</div>"""


def build_index(all_items):
    if not all_items:
        write("index.html", page_shell("ข่าว AI วันนี้", "index", '<h1>ข่าว AI วันนี้</h1><p class="empty">ยังไม่มีข่าว — รอรอบดึงข่าวถัดไป</p>'))
        return
    latest_date = all_items[0]["date"]
    today_items = [i for i in all_items if i["date"] == latest_date]
    cats_present = {i.get("category", "other") for i in today_items}
    major_items = [i for i in today_items if i.get("importance") == "major"]
    normal_items = [i for i in today_items if i.get("importance") != "major"]

    today_bkk_dt = datetime.now(BANGKOK)
    today_bkk = today_bkk_dt.strftime("%Y-%m-%d")
    is_fresh = latest_date == today_bkk
    day_ref = "วันนี้" if is_fresh else f"วันที่ {thai_date(latest_date)}"

    sections = []
    if major_items:
        sections.append(f'<div class="group-heading" data-group="major">🔥 ข่าวใหญ่{day_ref}</div>')
        sections.append("".join(card_html(i, group="major", all_items=all_items) for i in major_items))
    if normal_items:
        heading = f"ข่าวอื่นๆ {day_ref}" if major_items else ""
        if heading:
            sections.append(f'<div class="group-heading" data-group="normal">{heading}</div>')
        sections.append("".join(card_html(i, group="normal", all_items=all_items) for i in normal_items))

    if is_fresh:
        heading_html = f"""<h1>ข่าว AI ประจำวันที่ {thai_date(latest_date)}</h1>
<div class="freshness fresh">✓ เป็นข่าวล่าสุดของวันนี้</div>"""
    else:
        heading_html = f"""<h1>วันนี้ ({thai_date(today_bkk)}) ยังไม่มีข่าวใหม่</h1>
<div class="freshness stale">⏳ รอบดึงข่าวของวันนี้ยังไม่เข้ามา — ด้านล่างคือข่าวล่าสุดที่มี ({thai_date(latest_date)})</div>"""

    memory_html = ""
    try:
        one_year_ago = today_bkk_dt.replace(year=today_bkk_dt.year - 1).strftime("%Y-%m-%d")
    except ValueError:
        one_year_ago = today_bkk_dt.replace(year=today_bkk_dt.year - 1, day=28).strftime("%Y-%m-%d")
    memory_items = [i for i in all_items if i["date"] == one_year_ago]
    if memory_items:
        memory_html = f"""<div class="memory-section">
<h2>🪐 1 ปีที่แล้ววันนี้ ({thai_date(one_year_ago)})</h2>
{''.join(card_html(i, all_items=all_items) for i in memory_items)}
</div>"""

    quick_read_text = " ".join(f"{i.get('source','')}: {i.get('summary_th','')}" for i in today_items)
    quick_read_html = f"""<div id="quickRead" class="quick-read" hidden>
<p>{esc(quick_read_text)}</p>
</div>"""

    narrative_text = load_narrative(latest_date)
    narrative_html = f"""<div class="narrative-section">
<h2>📖 เล่าเป็นเรื่องราว</h2>
<p>{esc(narrative_text)}</p>
</div>""" if narrative_text else ""

    tool_row = f"""<div class="tool-row">
<button id="randomOldNews" class="tool-btn">🎲 สุ่มข่าวเก่า</button>
<button id="quickReadToggle" class="tool-btn">⚡ อ่านเร็ว 60 วิ</button>
<button id="dialogueListen" class="tool-btn">🎙️ ฟังพิธีกรอ่านข่าว</button>
<button id="qrToggle" class="tool-btn">📱 สแกนเปิดมือถือ</button>
<a href="mew-station-major-news.ics" class="tool-btn ics-btn" download>📅 บันทึกข่าวใหญ่ลงปฏิทิน</a>
</div>
{quick_read_html}
<div id="qrBox" class="quick-read" hidden><img src="assets/qr.png" alt="QR code เปิดเว็บบนมือถือ" style="display:block;max-width:180px;border-radius:8px;"></div>"""

    champions = compute_champions(all_items)
    champ_html = champion_cards_html(champions)
    dogfight = dogfight_html(champions)

    body = f"""{dogfight}
{champ_html}
{heading_html}
<div class="sub">{len(today_items)} ข่าว{f" · ข่าวใหญ่ {len(major_items)} ข่าว" if major_items else ""}</div>
{tool_row}
{narrative_html}
{memory_html}
{filters_html(cats_present, show_major_toggle=bool(major_items))}
{''.join(sections)}"""
    page_title = f"ข่าว AI {thai_date(latest_date)}" if is_fresh else f"ยังไม่มีข่าวใหม่วันนี้ ({thai_date(today_bkk)})"
    write("index.html", page_shell(page_title, "index", body, random_urls=[i["url"] for i in all_items]))


def build_weekly(weeks):
    if not weeks:
        write("weekly.html", page_shell("สรุปข่าว AI รายสัปดาห์", "weekly", '<h1>สรุปข่าว AI รายสัปดาห์</h1><p class="empty">ยังไม่มีสรุปรายสัปดาห์ — จะสร้างให้ทุกวันอาทิตย์</p>'))
        return
    sections = []
    for w in weeks:
        items = w.get("items", [])
        cats_present = {i.get("category", "other") for i in items}
        highlights = "".join(f"<li>{esc(h)}</li>" for h in w.get("highlights", []))
        directions = w.get("directions", {})
        directions_html = ""
        if directions:
            rows = "".join(
                f"<li><strong>{esc(company)}:</strong> {esc(desc)}</li>"
                for company, desc in directions.items()
            )
            directions_html = f"""<div class="memory-section">
<h2>🧭 ทิศทางแต่ละบริษัทสัปดาห์นี้</h2>
<ul>{rows}</ul>
</div>"""
        sections.append(f"""<h2>สัปดาห์ {esc(w.get('week', ''))} ({esc(w.get('start_date', ''))} – {esc(w.get('end_date', ''))})</h2>
<ul>{highlights}</ul>
{directions_html}
{filters_html(cats_present)}
{''.join(card_html(i, all_items=items) for i in items)}""")
    body = "<h1>สรุปข่าว AI รายสัปดาห์</h1>" + "<hr>".join(sections)
    write("weekly.html", page_shell("สรุปข่าว AI รายสัปดาห์", "weekly", body))


def build_archive(all_items):
    if not all_items:
        write("archive.html", page_shell("คลังข่าว AI ย้อนหลัง", "archive", '<h1>คลังข่าว AI ย้อนหลัง</h1><p class="empty">ยังไม่มีข้อมูล</p>'))
        return
    by_month = defaultdict(list)
    for item in all_items:
        ym = item["date"][:7]  # YYYY-MM
        by_month[ym].append(item)
    body_parts = [
        "<h1>คลังข่าว AI ย้อนหลัง</h1>",
        '<input type="text" id="searchBox" class="search-box" placeholder="🔎 ค้นหาข่าวเก่า... (หัวข้อ/สรุป/บริษัท)">',
        '<div id="searchEmpty" class="empty" hidden>ไม่พบข่าวที่ตรงกับคำค้นหา</div>',
        '<div class="tool-row"><button id="randomOldNews" class="tool-btn">🎲 สุ่มข่าวเก่า</button><button id="printPdf" class="tool-btn">🖨️ บันทึกเป็น PDF</button></div>',
    ]
    for ym in sorted(by_month.keys(), reverse=True):
        d = datetime.strptime(ym, "%Y-%m")
        month_label = f"{THAI_MONTHS[d.month]} {d.year + 543}"
        month_items = by_month[ym]
        cards = "".join(card_html(i, all_items=all_items) for i in month_items)
        body_parts.append(f"""<details class="month-group" id="month-{ym}" data-month="{ym}">
<summary>{month_label} ({len(month_items)} ข่าว)</summary>
{cards}
</details>""")
    write("archive.html", page_shell("คลังข่าว AI ย้อนหลัง", "archive", "\n".join(body_parts), random_urls=[i["url"] for i in all_items]))


def bar_rows(counts: list, max_items: int = 12) -> str:
    """counts: list of (label, count) already sorted descending."""
    counts = counts[:max_items]
    if not counts:
        return '<p class="empty">ยังไม่มีข้อมูล</p>'
    max_count = counts[0][1]
    rows = []
    for label, count in counts:
        pct = max(4, round(count / max_count * 100))
        rows.append(f"""<div class="stat-row">
  <div class="stat-label" title="{esc(label)}">{esc(label)}</div>
  <div class="stat-bar-wrap"><div class="stat-track"><div class="stat-bar" style="width:{pct}%" title="{esc(label)}: {count} ข่าว"></div></div><span class="stat-value">{count}</span></div>
</div>""")
    return "\n".join(rows)


STOP_EXTRA = {"ai", "การ", "ความ", "ได้", "ให้", "แล้ว", "จะ", "ที่", "เป็น", "มี", "ใน", "และ", "ของ", "กับ", "ว่า", "ไป", "มา", "ก็", "ยัง", "อยู่", "นี้"}

COMPANY_REGION = {
    "OpenAI": "🇺🇸 สหรัฐฯ", "Anthropic": "🇺🇸 สหรัฐฯ", "Google DeepMind": "🇺🇸 สหรัฐฯ",
    "Google": "🇺🇸 สหรัฐฯ", "Meta AI": "🇺🇸 สหรัฐฯ", "Meta": "🇺🇸 สหรัฐฯ",
    "Microsoft AI": "🇺🇸 สหรัฐฯ", "Microsoft": "🇺🇸 สหรัฐฯ", "xAI": "🇺🇸 สหรัฐฯ",
    "xAI (SpaceXAI)": "🇺🇸 สหรัฐฯ", "Hugging Face": "🇺🇸 สหรัฐฯ", "Nvidia": "🇺🇸 สหรัฐฯ",
    "Amazon": "🇺🇸 สหรัฐฯ", "Apple": "🇺🇸 สหรัฐฯ", "TechCrunch": "🇺🇸 สหรัฐฯ (สื่อ)",
    "The Verge": "🇺🇸 สหรัฐฯ (สื่อ)", "VentureBeat": "🇺🇸 สหรัฐฯ (สื่อ)", "Ars Technica": "🇺🇸 สหรัฐฯ (สื่อ)",
    "Future of Life Institute": "🇺🇸 สหรัฐฯ (องค์กร)",
    "Mistral AI": "🇫🇷 ฝรั่งเศส", "Mistral": "🇫🇷 ฝรั่งเศส",
    "DeepSeek": "🇨🇳 จีน", "Alibaba": "🇨🇳 จีน", "Alibaba Cloud": "🇨🇳 จีน",
    "Baidu": "🇨🇳 จีน", "Tencent": "🇨🇳 จีน", "ByteDance": "🇨🇳 จีน", "Z.ai": "🇨🇳 จีน",
    "EU Commission": "🇪🇺 ยุโรป (นโยบาย)",
}


def region_for(source: str) -> str:
    return COMPANY_REGION.get(source, "🌐 อื่นๆ/ไม่ทราบ")


CATEGORY_CLASS = {
    "model_release": ("⚔️", "นักบุกเบิก"),
    "product": ("🛠️", "นักสร้างสรรค์"),
    "funding": ("💰", "นักธุรกิจ"),
    "research": ("🔬", "นักปราชญ์"),
    "policy": ("⚖️", "ผู้พิทักษ์"),
    "other": ("🌌", "นักผจญภัย"),
}
AVATAR_COLORS = ["#4fd1ff", "#ff4fd8", "#35ffb0", "#ffb020"]
RANK_MEDALS = ["🥇", "🥈", "🥉"]


def compute_champions(all_items: list, top_n: int = 3) -> list:
    sources = sorted({i.get("source", "") for i in all_items if i.get("source")})
    champions = []
    for src in sources:
        items = [i for i in all_items if i.get("source") == src]
        major = len([i for i in items if i.get("importance") == "major"])
        total = len(items)
        cat_counts = Counter(i.get("category", "other") for i in items)
        top_cat = cat_counts.most_common(1)[0][0] if cat_counts else "other"
        icon, class_name = CATEGORY_CLASS.get(top_cat, CATEGORY_CLASS["other"])
        power = major * 5 + total
        champions.append({"name": src, "major": major, "total": total, "power": power, "icon": icon, "class_name": class_name})
    champions.sort(key=lambda c: c["power"], reverse=True)
    return champions[:top_n]


def champion_cards_html(champions: list) -> str:
    if not champions:
        return ""
    cards = []
    for idx, c in enumerate(champions):
        medal = RANK_MEDALS[idx] if idx < len(RANK_MEDALS) else "🎖️"
        cards.append(f"""<div class="champ-card">
  <div class="champ-rank">{medal}</div>
  <div class="champ-name">{esc(c['name'])}</div>
  <div class="champ-class">{c['icon']} {esc(c['class_name'])}</div>
  <div class="champ-power"><span>{c['power']}</span> พลัง</div>
  <div class="champ-detail">🔥 {c['major']} ข่าวใหญ่ · {c['total']} ข่าวรวม</div>
</div>""")
    return f"""<div class="champ-section">
  <h2>🏆 แชมป์ตลอดช่วงที่เก็บข้อมูล</h2>
  <div class="champ-disclaimer">จัดอันดับจากความถี่ข่าวในสื่อเท่านั้น ไม่ใช่การตัดสินความเก่งทางเทคนิคจริง</div>
  <div class="champ-row">{''.join(cards)}</div>
</div>"""


def dogfight_html(champions: list) -> str:
    if len(champions) < 2:
        return ""
    ships = []
    for idx, c in enumerate(champions[:3]):
        ships.append({
            "medal": RANK_MEDALS[idx] if idx < len(RANK_MEDALS) else "🎖️",
            "name": c["name"],
            "power": c["power"],
            "color": AVATAR_COLORS[idx % len(AVATAR_COLORS)],
        })
    data_script = f'<script type="application/json" id="dogfight-data">{json.dumps(ships, ensure_ascii=False)}</script>'
    return f"""<div class="dogfight-wrap">
  <canvas id="dogfightCanvas"></canvas>
</div>
{data_script}"""


def compute_word_cloud(items: list, top_n: int = 25):
    if not THAI_NLP_AVAILABLE:
        return []
    stopwords = _thai_stopwords()
    counts = Counter()
    for item in items:
        text = f"{item.get('title_th', '')} {item.get('summary_th', '')}"
        for tok in _thai_word_tokenize(text, engine="newmm"):
            tok_clean = tok.strip()
            tok_lower = tok_clean.lower()
            if len(tok_clean) < 2:
                continue
            if tok_lower in stopwords or tok_lower in STOP_EXTRA:
                continue
            if re.fullmatch(r"[\s\W\d]+", tok_clean):
                continue
            counts[tok_clean] += 1
    return counts.most_common(top_n)


def word_cloud_html(word_counts: list) -> str:
    if not word_counts:
        return ""
    max_count = word_counts[0][1]
    min_count = word_counts[-1][1]
    spans = []
    for word, count in word_counts:
        if max_count == min_count:
            scale = 1.0
        else:
            scale = (count - min_count) / (max_count - min_count)
        size = 13 + round(scale * 20)
        spans.append(f'<span style="font-size:{size}px" title="{count} ครั้ง">{esc(word)}</span>')
    return f'<div class="word-cloud">{"".join(spans)}</div>'


def build_stats(all_items):
    if not all_items:
        write("stats.html", page_shell("สถิติข่าว AI", "stats", '<h1>สถิติข่าว AI</h1><p class="empty">ยังไม่มีข้อมูล</p>'))
        return

    source_counts = Counter(i.get("source", "ไม่ทราบแหล่งที่มา") for i in all_items)
    category_counts = Counter(i.get("category", "other") for i in all_items)
    category_labeled = Counter()
    for cat, n in category_counts.items():
        category_labeled[CATEGORY_LABELS.get(cat, "อื่นๆ")] = n

    date_range = f"{thai_date(min(i['date'] for i in all_items))} – {thai_date(max(i['date'] for i in all_items))}"

    # AI Wars leaderboard: rank companies by MAJOR-news count (this month)
    today_bkk = datetime.now(BANGKOK)
    this_month = today_bkk.strftime("%Y-%m")
    month_items = [i for i in all_items if i["date"].startswith(this_month)]
    major_counts = Counter(i.get("source", "ไม่ทราบ") for i in month_items if i.get("importance") == "major")
    leaderboard_html = ""
    if major_counts:
        rows = "".join(
            f'<li><span class="lb-name">{esc(name)}</span><span class="lb-count">{n} ข่าวใหญ่</span></li>'
            for name, n in major_counts.most_common(10)
        )
        leaderboard_html = f"""<div class="stat-section">
  <h2>🏆 AI Wars — กระดานคะแนนข่าวใหญ่เดือนนี้</h2>
  <ul class="leaderboard">{rows}</ul>
</div>"""

    # Week-over-week comparison
    week_ago_start = (today_bkk - timedelta(days=7)).strftime("%Y-%m-%d")
    two_weeks_ago_start = (today_bkk - timedelta(days=14)).strftime("%Y-%m-%d")
    this_week_count = len([i for i in all_items if week_ago_start <= i["date"] <= today_bkk.strftime("%Y-%m-%d")])
    last_week_count = len([i for i in all_items if two_weeks_ago_start <= i["date"] < week_ago_start])
    wow_html = ""
    if last_week_count > 0:
        delta_pct = round((this_week_count - last_week_count) / last_week_count * 100)
        arrow = "📈" if delta_pct > 0 else ("📉" if delta_pct < 0 else "➡️")
        sign = "+" if delta_pct > 0 else ""
        wow_html = f"""<div class="stat-section">
  <h2>เทียบกับสัปดาห์ก่อน</h2>
  <p>{arrow} สัปดาห์นี้มีข่าว {this_week_count} ข่าว เทียบกับสัปดาห์ก่อน {last_week_count} ข่าว ({sign}{delta_pct}%)</p>
</div>"""

    word_cloud = word_cloud_html(compute_word_cloud(all_items))
    word_cloud_section = f"""<div class="stat-section">
  <h2>คำที่ถูกพูดถึงบ่อยที่สุด</h2>
  {word_cloud if word_cloud else '<p class="empty">ยังไม่มีข้อมูลพอ</p>'}
</div>""" if THAI_NLP_AVAILABLE else ""

    region_counts = Counter(region_for(i.get("source", "")) for i in all_items)

    body = f"""<h1>สถิติข่าว AI</h1>
<div class="sub">รวมข่าวทั้งหมด {len(all_items)} ข่าว ({date_range})</div>
{leaderboard_html}
{wow_html}
{word_cloud_section}
<div class="stat-section">
  <h2>บริษัท/แหล่งข่าวที่ถูกพูดถึงบ่อยที่สุด</h2>
  {bar_rows(source_counts.most_common())}
</div>
<div class="stat-section">
  <h2>🌍 แหล่งกำเนิดข่าวตามภูมิภาค</h2>
  {bar_rows(region_counts.most_common())}
</div>
<div class="stat-section">
  <h2>หมวดข่าวที่มีมากที่สุด</h2>
  {bar_rows(category_labeled.most_common())}
</div>"""
    write("stats.html", page_shell("สถิติข่าว AI", "stats", body))


def build_timeline(all_items):
    major_items = sorted([i for i in all_items if i.get("importance") == "major"], key=lambda i: i["date"])
    if not major_items:
        write("timeline.html", page_shell("ไทม์ไลน์ข่าวใหญ่", "timeline", '<h1>ไทม์ไลน์ข่าวใหญ่</h1><p class="empty">ยังไม่มีข่าวใหญ่ให้แสดงไทม์ไลน์</p>'))
        return
    points = "".join(f"""<div class="tl-point">
  <div class="tl-dot"></div>
  <div class="tl-date">{thai_date(item['date'])}</div>
  <div class="tl-card">
    <div class="tl-source">{esc(item.get('source',''))}</div>
    <a href="{esc(item.get('url','#'))}" target="_blank" rel="noopener">{esc(item.get('title_th',''))}</a>
  </div>
</div>""" for item in major_items)
    body = f"""<h1>🔥 ไทม์ไลน์ข่าวใหญ่</h1>
<div class="sub">ลากดูข่าวใหญ่ทั้งหมด {len(major_items)} ข่าว เรียงตามเวลา</div>
<div class="timeline">{points}</div>"""
    write("timeline.html", page_shell("ไทม์ไลน์ข่าวใหญ่", "timeline", body))


def build_quiz(all_items):
    if len(all_items) < 2 or len({i.get("source", "") for i in all_items}) < 2:
        write("quiz.html", page_shell("ควิซข่าว AI", "quiz", '<h1>🧠 ควิซข่าว AI</h1><p class="empty">ต้องมีข่าวจากอย่างน้อย 2 บริษัทถึงจะเล่นได้ — รอสะสมข้อมูลเพิ่มก่อนครับ</p>'))
        return

    all_sources = sorted({i.get("source", "") for i in all_items if i.get("source")})
    today_bkk = datetime.now(BANGKOK)
    this_month = today_bkk.strftime("%Y-%m")
    pool = [i for i in all_items if i["date"].startswith(this_month)] or all_items
    rng = random.Random(today_bkk.strftime("%Y-%m-%d"))  # stable per day
    sample = rng.sample(pool, min(5, len(pool)))

    questions = []
    for item in sample:
        correct = item.get("source", "")
        distractors = [s for s in all_sources if s != correct]
        rng.shuffle(distractors)
        options = [correct] + distractors[:3]
        rng.shuffle(options)
        questions.append({"q": item.get("title_th", ""), "options": options, "answer": correct})

    data_script = f'<script type="application/json" id="quiz-data">{json.dumps(questions, ensure_ascii=False)}</script>'
    body = f"""<h1>🧠 ควิซข่าว AI</h1>
<div class="sub">ทายว่าแต่ละข่าวเป็นของบริษัทไหน วัดความแม่นของคุณ</div>
<div id="quizArena"></div>
{data_script}"""
    write("quiz.html", page_shell("ควิซข่าว AI", "quiz", body))


def build_wrapped(all_items):
    if not all_items:
        write("wrapped.html", page_shell("สรุปประจำเดือน", "wrapped", '<h1>สรุปประจำเดือน</h1><p class="empty">ยังไม่มีข้อมูล</p>'))
        return
    today_bkk = datetime.now(BANGKOK)
    this_month = today_bkk.strftime("%Y-%m")
    month_items = [i for i in all_items if i["date"].startswith(this_month)]
    if not month_items:
        write("wrapped.html", page_shell("สรุปประจำเดือน", "wrapped", '<h1>สรุปประจำเดือน</h1><p class="empty">เดือนนี้ยังไม่มีข่าว</p>'))
        return

    month_label = f"{THAI_MONTHS[today_bkk.month]} {today_bkk.year + 543}"
    source_counts = Counter(i.get("source", "") for i in month_items)
    category_counts = Counter(CATEGORY_LABELS.get(i.get("category", "other"), "อื่นๆ") for i in month_items)
    major_items = [i for i in month_items if i.get("importance") == "major"]
    top_source = source_counts.most_common(1)[0] if source_counts else ("-", 0)
    top_category = category_counts.most_common(1)[0] if category_counts else ("-", 0)

    month_anchor = f"archive.html#month-{this_month}"

    cards = [
        f'<a class="wrap-card" href="{month_anchor}"><div class="wrap-emoji">🛰️</div><div class="wrap-big">{len(month_items)}</div><div class="wrap-label">ข่าว AI เดือน {esc(month_label)} · แตะดูทั้งหมด</div></a>',
        f'<a class="wrap-card" href="{month_anchor}"><div class="wrap-emoji">🏆</div><div class="wrap-big">{esc(top_source[0])}</div><div class="wrap-label">บริษัทที่ถูกพูดถึงบ่อยสุด ({top_source[1]} ข่าว) · แตะดูข่าว</div></a>',
        f'<a class="wrap-card" href="{month_anchor}"><div class="wrap-emoji">📂</div><div class="wrap-big">{esc(top_category[0])}</div><div class="wrap-label">หมวดข่าวที่แข่งขันดุที่สุด ({top_category[1]} ข่าว) · แตะดูข่าว</div></a>',
    ]
    if major_items:
        biggest = major_items[0]
        cards.append(
            f'<a class="wrap-card" href="{esc(biggest.get("url","#"))}" target="_blank" rel="noopener"><div class="wrap-emoji">🔥</div><div class="wrap-big" style="font-size:20px">{esc(biggest.get("title_th",""))}</div><div class="wrap-label">ข่าวใหญ่ประจำเดือน · {esc(biggest.get("source",""))} · แตะอ่านข่าวเต็ม</div></a>'
        )
    cards.append(f'<a class="wrap-card" href="{month_anchor}"><div class="wrap-emoji">🚀</div><div class="wrap-big" style="font-size:18px">แล้วเจอกันเดือนหน้า</div><div class="wrap-label">MEW Station · แตะดูข่าวทั้งหมดเดือนนี้</div></a>')

    detail_cards = "".join(card_html(i, all_items=month_items) for i in sorted(month_items, key=lambda i: i["date"], reverse=True))

    body = f"""<h1>✨ สรุปประจำเดือน {esc(month_label)}</h1>
<div class="sub">ลากดูทีละใบ เหมือน Spotify Wrapped ของวงการ AI — แตะการ์ดไหนก็ได้เพื่อดูรายละเอียด</div>
<div class="wrap-carousel">{''.join(cards)}</div>
<details class="month-group">
<summary>📋 รายละเอียดข่าวทั้งหมดเดือนนี้ ({len(month_items)} ข่าว)</summary>
{detail_cards}
</details>"""
    write("wrapped.html", page_shell("สรุปประจำเดือน", "wrapped", body))


def stars_html(stars: float) -> str:
    full = round(stars)
    empty = 5 - full
    return "★" * full + "☆" * empty


def skills_section_html() -> str:
    skills_data = load_skills()
    skills = skills_data.get("skills", [])
    if not skills:
        return ""

    updated = skills_data.get("updated", "")
    try:
        cutoff = (datetime.strptime(updated, "%Y-%m-%d") - timedelta(days=14)) if updated else None
    except ValueError:
        cutoff = None

    def is_new(sk):
        if not cutoff:
            return False
        try:
            return datetime.strptime(sk.get("first_seen", ""), "%Y-%m-%d") >= cutoff
        except ValueError:
            return False

    ordered = sorted(skills, key=lambda sk: (not is_new(sk), sk.get("name", "")))
    cards = []
    for sk in ordered:
        badge = '<span class="cap-score-label">🆕 ใหม่</span> ' if is_new(sk) else ""
        cards.append(f"""<div class="cap-tool-card">
  <div class="cap-tool-name">{badge}{esc(sk.get('name',''))}</div>
  <p class="cap-verdict">{esc(sk.get('description','')[:150])}</p>
</div>""")

    updated_label = thai_date(updated) if updated else ""
    return f"""<div class="cap-category" id="cap-skills">
  <h2>🧰 เครื่องมือที่คุณมีอยู่แล้วตอนนี้ (Claude Code)</h2>
  <p class="cap-summary">รายชื่อ skill/เครื่องมือจริงที่ติดตั้งอยู่ในเครื่อง ตรวจทุกสัปดาห์อัตโนมัติ (ไม่ใช้ AI) ตัวไหนขึ้น "🆕 ใหม่" คือเพิ่งพบใน 14 วันล่าสุด · อัปเดตล่าสุด {esc(updated_label)}</p>
  <div class="cap-tool-grid">{''.join(cards)}</div>
</div>"""


def build_capabilities():
    data = load_capabilities()
    if not data or not data.get("categories"):
        write("capabilities.html", page_shell("ความสามารถ AI ตอนนี้", "capabilities", '<h1>ความสามารถ AI ตอนนี้</h1><p class="empty">ยังไม่มีข้อมูล</p>'))
        return

    updated_label = thai_date(data["updated"]) if data.get("updated") else ""
    sections = []
    for cat in data["categories"]:
        tool_cards = []
        for idx, tool in enumerate(cat.get("tools", [])):
            medal = RANK_MEDALS[idx] if idx < len(RANK_MEDALS) else f"#{idx + 1}"
            tool_cards.append(f"""<div class="cap-tool-card">
  <div class="cap-tool-rank">{medal}</div>
  <div class="cap-tool-name">{esc(tool['name'])}</div>
  <div class="cap-stars" title="ตีความจากอันดับ/ผลสอบเทียบจริง ไม่ใช่ตัวเลขทางการที่เทียบข้ามหมวดได้">{stars_html(tool['stars'])}</div>
  <div class="cap-score-label">{esc(tool['score_label'])}</div>
  <p class="cap-verdict">{esc(tool['verdict_th'])}</p>
</div>""")
        sources_html = " · ".join(
            f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a>' for s in cat.get("sources", [])
        )
        sections.append(f"""<div class="cap-category" id="cap-{esc(cat['id'])}">
  <h2>{cat['icon']} {esc(cat['name_th'])}</h2>
  <p class="cap-summary">{esc(cat['summary_th'])}</p>
  <div class="cap-scale-note">📏 {esc(cat['scale_note_th'])}</div>
  <div class="cap-tool-grid">{''.join(tool_cards)}</div>
  <div class="cap-sources">แหล่งอ้างอิง: {sources_html}</div>
</div>""")

    body = f"""<h1>🤖 ความสามารถ AI ตอนนี้</h1>
<div class="sub">ภาพรวมว่า AI แต่ละแบบทำอะไรได้ถึงระดับไหนแล้ว · อัปเดตล่าสุด {esc(updated_label)}</div>
<div class="cap-methodology">⭐ คะแนนดาวเป็นการตีความของเราจากอันดับ/ผลสอบเทียบจริงที่แหล่งข้อมูลรายงาน ไม่ใช่ตัวเลขทางการที่เทียบข้ามหมวดกันได้ (เช่น ดาวของหมวดภาพ เทียบกับดาวของหมวดโค้ดตรงๆ ไม่ได้) ตัวเลขจริงที่อ้างอิงแสดงอยู่ใต้ชื่อแต่ละตัวเสมอ ข้อมูลเปลี่ยนเร็ว อัปเดตหน้านี้เป็นรอบ (ไม่ใช่รายวัน) เพื่อคุมคุณภาพเนื้อหา</div>
{skills_section_html()}
{''.join(sections)}"""
    write("capabilities.html", page_shell("ความสามารถ AI ตอนนี้", "capabilities", body))


def build_bookmarks(all_items):
    if not all_items:
        body = '<h1>ข่าวที่บันทึกไว้อ่าน</h1><p class="empty">ยังไม่มีข้อมูล</p>'
        write("bookmarks.html", page_shell("ข่าวที่บันทึกไว้อ่าน", "bookmarks", body))
        return
    cards = "".join(card_html(i, all_items=all_items) for i in all_items)
    body = f"""<h1>ข่าวที่บันทึกไว้อ่าน</h1>
<div class="sub">กดดาวค้าง ☆ ที่มุมข่าวไหนก็ได้เพื่อบันทึกไว้ที่นี่ (บันทึกไว้ในเบราว์เซอร์นี้เท่านั้น)</div>
<div class="tool-row"><button id="speakBookmarks" class="tool-btn">🔊 ฟังข่าวที่บันทึกไว้ทั้งหมด</button></div>
<div class="speak-hint">กดแล้วเบราว์เซอร์จะอ่านออกเสียงให้ฟัง (ใช้เสียงพูดในตัวเครื่อง/มือถือของคุณเอง มือถือส่วนใหญ่มีเสียงไทยอยู่แล้ว)</div>
<p class="empty" id="noBookmarks">ยังไม่มีข่าวที่บันทึกไว้ — ลองกด ☆ ที่ข่าวหน้าอื่นดูก่อนครับ</p>
{cards}"""
    write("bookmarks.html", page_shell("ข่าวที่บันทึกไว้อ่าน", "bookmarks", body))


def write(filename: str, content: str):
    path = os.path.join(ROOT, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote {path}")


def ics_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def build_ics(all_items):
    major_items = [i for i in all_items if i.get("importance") == "major"]
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MEW Station//AI News TH//EN", "CALSCALE:GREGORIAN"]
    for idx, item in enumerate(major_items):
        date_compact = item["date"].replace("-", "")
        next_day = (datetime.strptime(item["date"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y%m%d")
        uid = f"{date_compact}-{idx}@mewuserr.github.io"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART;VALUE=DATE:{date_compact}",
            f"DTEND;VALUE=DATE:{next_day}",
            f"SUMMARY:🔥 {ics_escape(item.get('title_th', ''))}",
            f"DESCRIPTION:{ics_escape(item.get('summary_th', ''))}",
            f"URL:{item.get('url', '')}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    write("mew-station-major-news.ics", "\r\n".join(lines) + "\r\n")


def update_latest_cache(all_items, keep_days: int = 14):
    dates = sorted({i["date"] for i in all_items}, reverse=True)[:keep_days]
    recent = [i for i in all_items if i["date"] in dates]
    with open(LATEST_PATH, "w", encoding="utf-8") as f:
        json.dump(recent, f, ensure_ascii=False, indent=2)
    print(f"wrote {LATEST_PATH} ({len(recent)} items, {len(dates)} days)")


def main():
    global ALL_SOURCES
    all_items = load_all_news()
    weeks = load_weekly()
    ALL_SOURCES = sorted({i.get("source", "") for i in all_items if i.get("source")})
    build_index(all_items)
    build_weekly(weeks)
    build_archive(all_items)
    build_stats(all_items)
    build_timeline(all_items)
    build_quiz(all_items)
    build_wrapped(all_items)
    build_capabilities()
    build_bookmarks(all_items)
    build_ics(all_items)
    update_latest_cache(all_items)


if __name__ == "__main__":
    main()
