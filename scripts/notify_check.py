"""Local-only companion to the cloud news engine.

The news-gathering + summarizing + publishing runs as a Claude Code CLOUD
routine (sandboxed, no desktop access). This script runs on the user's own
PC via Windows Task Scheduler, fetches today's published news from the live
GitHub Pages site, and fires a local Windows toast notification if there's
something new. No AI calls, no API key - just an HTTP GET + winotify.

Usage: python notify_check.py
"""
import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

from winotify import Notification

SITE_LATEST_URL = "https://mewuserr.github.io/ai-news-th/data/latest.json"
INDEX_URL = "https://mewuserr.github.io/ai-news-th/index.html"
STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".notify_state.json")
TOP_N = 3
BANGKOK = timezone(timedelta(hours=7))


def today_str() -> str:
    return datetime.now(BANGKOK).strftime("%Y-%m-%d")


def load_last_notified_date() -> str:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f).get("last_notified_date", "")
    return ""


def save_last_notified_date(date_str: str):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"last_notified_date": date_str}, f)


def fetch_latest_items():
    req = urllib.request.Request(SITE_LATEST_URL, headers={"User-Agent": "ai-news-th-notify"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    today = today_str()

    try:
        items = fetch_latest_items()
    except Exception as e:
        print(f"could not fetch site data: {e}")
        return

    if not items:
        print("no published items at all yet, skipping")
        return

    today_items = [i for i in items if i.get("date") == today]
    if today_items:
        use_date, use_items, is_stale = today, today_items, False
    else:
        latest_date = max(i["date"] for i in items)
        use_date = latest_date
        use_items = [i for i in items if i["date"] == latest_date]
        is_stale = True

    if load_last_notified_date() == use_date:
        print(f"already notified for {use_date}, skipping")
        return

    major = [i for i in use_items if i.get("importance") == "major"]
    ranked = major + [i for i in use_items if i.get("importance") != "major"]
    titles = [("🔥 " if i.get("importance") == "major" else "• ") + i.get("title_th", "") for i in ranked[:TOP_N]]
    body = "\n".join(titles)
    if len(use_items) > TOP_N:
        body += f"\n…และอีก {len(use_items) - TOP_N} ข่าว"

    title = f"ข่าว AI วันที่ {use_date} ({len(use_items)} ข่าว)"
    if is_stale:
        title = "(ยังไม่มีข่าวใหม่วันนี้) " + title
    if major:
        title = "🔥 มีข่าวใหญ่! " + title

    Notification(app_id="ข่าว AI รายวัน", title=title, msg=body, launch=INDEX_URL).show()
    save_last_notified_date(use_date)
    print(f"notification sent for {use_date} ({len(use_items)} items, stale={is_stale})")


if __name__ == "__main__":
    main()
