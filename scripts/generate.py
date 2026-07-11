"""Regenerate index.html / weekly.html / archive.html from data/*.json.

Pure stdlib, no server needed - output is opened directly via file://.
Run manually or from engine-prompt.md after data/ is updated.
"""
import json
import glob
import os
from datetime import datetime
from collections import defaultdict, Counter

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
:root { color-scheme: light dark; }
body { font-family: -apple-system, "Segoe UI", "Noto Sans Thai", sans-serif; max-width: 880px; margin: 0 auto; padding: 24px 16px 64px; line-height: 1.6; }
nav { display: flex; gap: 16px; margin-bottom: 24px; font-size: 15px; }
nav a { text-decoration: none; padding: 6px 12px; border-radius: 8px; opacity: 0.75; }
nav a.active { background: color-mix(in srgb, currentColor 12%, transparent); opacity: 1; font-weight: 600; }
h1 { font-size: 22px; margin-bottom: 4px; }
.sub { opacity: 0.6; font-size: 14px; margin-bottom: 20px; }
.filters { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
.filters button { border: 1px solid color-mix(in srgb, currentColor 25%, transparent); background: transparent; color: inherit; border-radius: 999px; padding: 5px 12px; font-size: 13px; cursor: pointer; }
.filters button.active { background: color-mix(in srgb, currentColor 15%, transparent); font-weight: 600; }
.card { border: 1px solid color-mix(in srgb, currentColor 15%, transparent); border-radius: 12px; padding: 16px; margin-bottom: 14px; }
.card.major { border: 1.5px solid #e0912f; background: color-mix(in srgb, #e0912f 8%, transparent); }
.badge { display: inline-block; font-size: 12px; padding: 2px 9px; border-radius: 999px; background: color-mix(in srgb, currentColor 12%, transparent); margin-bottom: 8px; margin-right: 6px; }
.badge.major { background: #e0912f; color: #1a1300; font-weight: 700; }
.card h3 { margin: 0 0 8px; font-size: 17px; }
.card h3 a { color: inherit; text-decoration: none; }
.card h3 a:hover { text-decoration: underline; }
.card p { margin: 0 0 8px; }
.meta { font-size: 13px; opacity: 0.55; }
.group-heading { margin-top: 32px; margin-bottom: 12px; font-size: 16px; opacity: 0.85; font-weight: 700; }
.major-toggle { display: flex; align-items: center; gap: 6px; font-size: 13px; margin-bottom: 16px; opacity: 0.85; cursor: pointer; }
details { margin-bottom: 10px; }
summary { cursor: pointer; font-weight: 600; padding: 4px 0; }
.empty { opacity: 0.6; padding: 20px 0; }
.stat-section { margin-bottom: 36px; }
.stat-section h2 { font-size: 16px; margin-bottom: 14px; }
.stat-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.stat-label { width: 130px; flex-shrink: 0; font-size: 13px; text-align: right; opacity: 0.85; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.stat-track { flex: 1; position: relative; height: 20px; }
.stat-bar { height: 20px; max-height: 20px; background: #e0912f; border-radius: 4px; min-width: 4px; }
.stat-value { font-size: 12px; opacity: 0.7; margin-left: 8px; font-variant-numeric: tabular-nums; }
.stat-bar-wrap { display: flex; align-items: center; flex: 1; }
.bookmark-btn { background: none; border: none; cursor: pointer; font-size: 18px; line-height: 1; padding: 0 2px; opacity: 0.5; float: right; }
.bookmark-btn:hover { opacity: 0.9; }
.bookmark-btn.saved { opacity: 1; }
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


def page_shell(title: str, active: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="icon-192.png">
<meta name="theme-color" content="#e0912f">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="ข่าว AI">
<style>{SHARED_STYLE}</style>
</head>
<body data-page="{active}">
{nav_html(active)}
{body}
<script>{FILTER_SCRIPT}</script>
<script>{BOOKMARK_SCRIPT}</script>
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
    return f"""<div class="card{major_class}" data-category="{esc(cat)}" data-importance="{esc(importance)}" data-url="{url}"{group_attr}>
  <button class="bookmark-btn" data-url="{url}" title="บันทึกไว้อ่านทีหลัง" aria-label="บันทึกไว้อ่านทีหลัง">☆</button>
  {major_badge}<span class="badge">{esc(label)}</span>
  <h3><a href="{url}" target="_blank" rel="noopener">{esc(item.get('title_th', ''))}</a></h3>
  <p>{esc(item.get('summary_th', ''))}</p>
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

    body = f"""<h1>ข่าว AI ประจำวันที่ {thai_date(latest_date)}</h1>
<div class="sub">{len(today_items)} ข่าว{f" · ข่าวใหญ่ {len(major_items)} ข่าว" if major_items else ""}</div>
{filters_html(cats_present, show_major_toggle=bool(major_items))}
{''.join(sections)}"""
    write("index.html", page_shell(f"ข่าว AI {thai_date(latest_date)}", "index", body))


def build_weekly(weeks):
    if not weeks:
        write("weekly.html", page_shell("สรุปข่าว AI รายสัปดาห์", "weekly", '<h1>สรุปข่าว AI รายสัปดาห์</h1><p class="empty">ยังไม่มีสรุปรายสัปดาห์ — จะสร้างให้ทุกวันอาทิตย์</p>'))
        return
    sections = []
    for w in weeks:
        items = w.get("items", [])
        cats_present = {i.get("category", "other") for i in items}
        highlights = "".join(f"<li>{esc(h)}</li>" for h in w.get("highlights", []))
        sections.append(f"""<h2>สัปดาห์ {esc(w.get('week', ''))} ({esc(w.get('start_date', ''))} – {esc(w.get('end_date', ''))})</h2>
<ul>{highlights}</ul>
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
    body_parts = ["<h1>คลังข่าว AI ย้อนหลัง</h1>"]
    for ym in sorted(by_month.keys(), reverse=True):
        d = datetime.strptime(ym, "%Y-%m")
        month_label = f"{THAI_MONTHS[d.month]} {d.year + 543}"
        month_items = by_month[ym]
        cards = "".join(card_html(i) for i in month_items)
        body_parts.append(f"""<details>
<summary>{month_label} ({len(month_items)} ข่าว)</summary>
{cards}
</details>""")
    write("archive.html", page_shell("คลังข่าว AI ย้อนหลัง", "archive", "\n".join(body_parts)))


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
