"""Fire a Windows toast notification summarizing today's AI news headlines.

Usage: python notify.py
Reads data/news/<latest-date>.json, shows top headlines, clicking opens index.html.
"""
import glob
import json
import os
import sys

from winotify import Notification

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_NEWS_DIR = os.path.join(ROOT, "data", "news")
INDEX_PATH = os.path.join(ROOT, "index.html")

TOP_N = 3


def latest_news_file():
    files = sorted(glob.glob(os.path.join(DATA_NEWS_DIR, "*.json")))
    return files[-1] if files else None


def main():
    path = latest_news_file()
    if not path:
        print("no news files found, skipping notification")
        return

    with open(path, encoding="utf-8") as f:
        items = json.load(f)

    if not items:
        print("no items for latest date, skipping notification")
        return

    date_str = os.path.splitext(os.path.basename(path))[0]
    major = [i for i in items if i.get("importance") == "major"]
    ranked = major + [i for i in items if i.get("importance") != "major"]
    titles = [("🔥 " if item.get("importance") == "major" else "• ") + item.get("title_th", "") for item in ranked[:TOP_N]]
    body = "\n".join(titles)
    if len(items) > TOP_N:
        body += f"\n…และอีก {len(items) - TOP_N} ข่าว"

    title = f"ข่าว AI วันที่ {date_str} ({len(items)} ข่าว)"
    if major:
        title = f"🔥 มีข่าวใหญ่! " + title

    toast = Notification(
        app_id="ข่าว AI รายวัน",
        title=title,
        msg=body,
        launch=f"file:///{INDEX_PATH.replace(os.sep, '/')}",
    )
    toast.show()
    print(f"notification sent for {date_str} ({len(items)} items)")


if __name__ == "__main__":
    main()
