"""Regenerate index.html / weekly.html / archive.html from data/*.json.

Pure stdlib, no server needed - output is opened directly via file://.
Run manually or from engine-prompt.md after data/ is updated.
"""
import json
import glob
import os
from datetime import datetime
from collections import defaultdict

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
.badge { display: inline-block; font-size: 12px; padding: 2px 9px; border-radius: 999px; background: color-mix(in srgb, currentColor 12%, transparent); margin-bottom: 8px; }
.card h3 { margin: 0 0 8px; font-size: 17px; }
.card h3 a { color: inherit; text-decoration: none; }
.card h3 a:hover { text-decoration: underline; }
.card p { margin: 0 0 8px; }
.meta { font-size: 13px; opacity: 0.55; }
.group-heading { margin-top: 32px; font-size: 16px; opacity: 0.8; }
details { margin-bottom: 10px; }
summary { cursor: pointer; font-weight: 600; padding: 4px 0; }
.empty { opacity: 0.6; padding: 20px 0; }
"""

FILTER_SCRIPT = """
function applyFilter(cat) {
  document.querySelectorAll('.filters button').forEach(b => b.classList.toggle('active', b.dataset.cat === cat));
  document.querySelectorAll('.card').forEach(c => {
    c.style.display = (cat === 'all' || c.dataset.category === cat) ? '' : 'none';
  });
}
document.querySelectorAll('.filters button').forEach(b => b.addEventListener('click', () => applyFilter(b.dataset.cat)));
"""


def nav_html(active: str) -> str:
    links = [
        ("index.html", "วันนี้", "index"),
        ("weekly.html", "รายสัปดาห์", "weekly"),
        ("archive.html", "คลังข่าวย้อนหลัง", "archive"),
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
<style>{SHARED_STYLE}</style>
</head>
<body>
{nav_html(active)}
{body}
<script>{FILTER_SCRIPT}</script>
</body>
</html>
"""


def filters_html(categories_present: set) -> str:
    buttons = ['<button data-cat="all" class="active">ทั้งหมด</button>']
    for cat, label in CATEGORY_LABELS.items():
        if cat in categories_present:
            buttons.append(f'<button data-cat="{cat}">{esc(label)}</button>')
    return '<div class="filters">' + "".join(buttons) + "</div>"


def card_html(item: dict) -> str:
    cat = item.get("category", "other")
    label = CATEGORY_LABELS.get(cat, "อื่นๆ")
    return f"""<div class="card" data-category="{esc(cat)}">
  <span class="badge">{esc(label)}</span>
  <h3><a href="{esc(item.get('url', '#'))}" target="_blank" rel="noopener">{esc(item.get('title_th', ''))}</a></h3>
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
    body = f"""<h1>ข่าว AI ประจำวันที่ {thai_date(latest_date)}</h1>
<div class="sub">{len(today_items)} ข่าว</div>
{filters_html(cats_present)}
{''.join(card_html(i) for i in today_items)}"""
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
    update_latest_cache(all_items)


if __name__ == "__main__":
    main()
