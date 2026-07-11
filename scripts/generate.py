"""Regenerate index.html / weekly.html / archive.html from data/*.json.

Pure stdlib, no server needed - output is opened directly via file://.
Run manually or from engine-prompt.md after data/ is updated.
"""
import json
import glob
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

BANGKOK = timezone(timedelta(hours=7))

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
  color: var(--text); position: relative;
}
canvas#starfield { position: fixed; inset: 0; z-index: -3; }
.earth-peek {
  position: fixed; top: -130px; right: -130px; width: 340px; height: 340px; z-index: -2;
  background-image: url('assets/earth.webp'); background-size: cover; pointer-events: none;
  opacity: 0.92; animation: floatPlanet 9s ease-in-out infinite;
}
@keyframes floatPlanet { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-16px); } }
@media (prefers-reduced-motion: reduce) { .earth-peek { animation: none; } }
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
.card h3 a { color: var(--text); text-decoration: none; }
.card h3 a:hover { color: var(--accent); text-decoration: underline; }
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
.bookmark-btn { background: none; border: none; cursor: pointer; font-size: 19px; line-height: 1; padding: 0 2px; opacity: 0.65; float: right; color: var(--major); }
.bookmark-btn:hover { opacity: 1; }
.bookmark-btn.saved { opacity: 1; }
.share-btn { background: none; border: none; cursor: pointer; font-size: 17px; line-height: 1; padding: 0 2px; opacity: 0.65; float: right; margin-right: 6px; color: var(--accent); }
.share-btn:hover { opacity: 1; }
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
function pickThaiVoice() {
  const voices = window.speechSynthesis.getVoices();
  return voices.find(v => v.lang && v.lang.toLowerCase().startsWith('th')) || null;
}
function speakBookmarked() {
  if (!('speechSynthesis' in window)) {
    alert('เบราว์เซอร์นี้ไม่รองรับการอ่านออกเสียง ลองเปิดจาก Chrome หรือ Safari บนมือถือดูครับ');
    return;
  }
  const cards = [...document.querySelectorAll('.card')].filter(c => c.style.display !== 'none');
  if (!cards.length) { alert('ยังไม่มีข่าวที่บันทึกไว้ให้ฟัง'); return; }
  window.speechSynthesis.cancel();
  const thaiVoice = pickThaiVoice();
  const btn = document.getElementById('speakBookmarks');
  cards.forEach((card, idx) => {
    const title = card.querySelector('h3 a')?.textContent || '';
    const summary = card.querySelector('p')?.textContent || '';
    const utter = new SpeechSynthesisUtterance(`${title}. ${summary}`);
    utter.lang = 'th-TH';
    if (thaiVoice) utter.voice = thaiVoice;
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


def nav_html(active: str) -> str:
    links = [
        ("index.html", "วันนี้", "index"),
        ("weekly.html", "รายสัปดาห์", "weekly"),
        ("archive.html", "คลังข่าวย้อนหลัง", "archive"),
        ("stats.html", "สถิติ", "stats"),
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
<div class="earth-peek"></div>
<div class="brand">🛰️ {esc(SITE_NAME)}</div>
{nav_html(active)}
{body}
<footer class="site-footer">🛰️ {esc(SITE_NAME)} · ดูแลและคัดสรรข่าวโดย MEW · อัปเดตอัตโนมัติทุกวัน</footer>
{urls_script}
<script>{STARFIELD_SCRIPT}</script>
<script>{FILTER_SCRIPT}</script>
<script>{BOOKMARK_SCRIPT}</script>
<script>{SHARE_SCRIPT}</script>
<script>{READ_SCRIPT}</script>
<script>{RANDOM_SCRIPT}</script>
<script>{SPEAK_SCRIPT}</script>
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


def card_html(item: dict, group: str = "") -> str:
    cat = item.get("category", "other")
    label = CATEGORY_LABELS.get(cat, "อื่นๆ")
    importance = item.get("importance", "normal")
    is_major = importance == "major"
    group_attr = f' data-group="{esc(group)}"' if group else ""
    major_class = " major" if is_major else ""
    major_badge = '<span class="badge major">🔥 ข่าวใหญ่</span>' if is_major else ""
    url = esc(item.get("url", "#"))
    share_title = esc(item.get("title_th", ""))
    context = item.get("context_th", "").strip()
    context_html = f'<p class="context">🔗 {esc(context)}</p>' if context else ""
    return f"""<div class="card{major_class}" data-category="{esc(cat)}" data-importance="{esc(importance)}" data-url="{url}"{group_attr}>
  <button class="bookmark-btn" data-url="{url}" title="บันทึกไว้อ่านทีหลัง" aria-label="บันทึกไว้อ่านทีหลัง">☆</button>
  <button class="share-btn" data-url="{url}" data-title="{share_title}" title="แชร์ข่าวนี้" aria-label="แชร์ข่าวนี้">🔗</button>
  {major_badge}<span class="badge">{esc(label)}</span>
  <h3><a href="{url}" target="_blank" rel="noopener">{esc(item.get('title_th', ''))}</a></h3>
  <p>{esc(item.get('summary_th', ''))}</p>
  {context_html}
  <div class="meta">{esc(item.get('source', ''))} · {thai_date(item['date'])}</div>
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

    sections = []
    if major_items:
        sections.append('<div class="group-heading" data-group="major">🔥 ข่าวใหญ่วันนี้</div>')
        sections.append("".join(card_html(i, group="major") for i in major_items))
    if normal_items:
        heading = "ข่าวอื่นๆ วันนี้" if major_items else ""
        if heading:
            sections.append(f'<div class="group-heading" data-group="normal">{heading}</div>')
        sections.append("".join(card_html(i, group="normal") for i in normal_items))

    today_bkk_dt = datetime.now(BANGKOK)
    today_bkk = today_bkk_dt.strftime("%Y-%m-%d")
    is_fresh = latest_date == today_bkk
    freshness = (
        '<div class="freshness fresh">✓ เป็นข่าวล่าสุดของวันนี้</div>' if is_fresh
        else '<div class="freshness stale">ยังไม่มีข่าวใหม่ของวันนี้ — นี่คือข่าวล่าสุดที่มี</div>'
    )

    memory_html = ""
    try:
        one_year_ago = today_bkk_dt.replace(year=today_bkk_dt.year - 1).strftime("%Y-%m-%d")
    except ValueError:
        one_year_ago = today_bkk_dt.replace(year=today_bkk_dt.year - 1, day=28).strftime("%Y-%m-%d")
    memory_items = [i for i in all_items if i["date"] == one_year_ago]
    if memory_items:
        memory_html = f"""<div class="memory-section">
<h2>🪐 1 ปีที่แล้ววันนี้ ({thai_date(one_year_ago)})</h2>
{''.join(card_html(i) for i in memory_items)}
</div>"""

    tool_row = '<div class="tool-row"><button id="randomOldNews" class="tool-btn">🎲 สุ่มข่าวเก่า</button></div>'

    body = f"""<h1>ข่าว AI ประจำวันที่ {thai_date(latest_date)}</h1>
{freshness}
<div class="sub">{len(today_items)} ข่าว{f" · ข่าวใหญ่ {len(major_items)} ข่าว" if major_items else ""}</div>
{tool_row}
{memory_html}
{filters_html(cats_present, show_major_toggle=bool(major_items))}
{''.join(sections)}"""
    write("index.html", page_shell(f"ข่าว AI {thai_date(latest_date)}", "index", body, random_urls=[i["url"] for i in all_items]))


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
{''.join(card_html(i) for i in items)}""")
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
        '<div class="tool-row"><button id="randomOldNews" class="tool-btn">🎲 สุ่มข่าวเก่า</button></div>',
    ]
    for ym in sorted(by_month.keys(), reverse=True):
        d = datetime.strptime(ym, "%Y-%m")
        month_label = f"{THAI_MONTHS[d.month]} {d.year + 543}"
        month_items = by_month[ym]
        cards = "".join(card_html(i) for i in month_items)
        body_parts.append(f"""<details>
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

    body = f"""<h1>สถิติข่าว AI</h1>
<div class="sub">รวมข่าวทั้งหมด {len(all_items)} ข่าว ({date_range})</div>
<div class="stat-section">
  <h2>บริษัท/แหล่งข่าวที่ถูกพูดถึงบ่อยที่สุด</h2>
  {bar_rows(source_counts.most_common())}
</div>
<div class="stat-section">
  <h2>หมวดข่าวที่มีมากที่สุด</h2>
  {bar_rows(category_labeled.most_common())}
</div>"""
    write("stats.html", page_shell("สถิติข่าว AI", "stats", body))


def build_bookmarks(all_items):
    if not all_items:
        body = '<h1>ข่าวที่บันทึกไว้อ่าน</h1><p class="empty">ยังไม่มีข้อมูล</p>'
        write("bookmarks.html", page_shell("ข่าวที่บันทึกไว้อ่าน", "bookmarks", body))
        return
    cards = "".join(card_html(i) for i in all_items)
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


def update_latest_cache(all_items, keep_days: int = 14):
    dates = sorted({i["date"] for i in all_items}, reverse=True)[:keep_days]
    recent = [i for i in all_items if i["date"] in dates]
    with open(LATEST_PATH, "w", encoding="utf-8") as f:
        json.dump(recent, f, ensure_ascii=False, indent=2)
    print(f"wrote {LATEST_PATH} ({len(recent)} items, {len(dates)} days)")


def main():
    all_items = load_all_news()
    weeks = load_weekly()
    build_index(all_items)
    build_weekly(weeks)
    build_archive(all_items)
    build_stats(all_items)
    build_bookmarks(all_items)
    update_latest_cache(all_items)


if __name__ == "__main__":
    main()
