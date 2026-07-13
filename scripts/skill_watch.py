"""Local-only "did I gain a new capability?" watcher.

Not part of the AI news engine. Runs on the user's own PC via Windows Task
Scheduler, scans installed Claude Code skills (~/.claude/skills), diffs
against data/skills.json from last run, and:
  1. fires a local Windows toast notification if anything new showed up
  2. writes data/skills.json (with first_seen dates) so the change is also
     visible on the public site (capabilities.html) - Windows toasts get
     missed, the site does not.
  3. regenerates the site and commits+pushes, but ONLY if something changed.

No AI calls, no API key - just a directory listing + YAML frontmatter read +
winotify + git.

Usage: python skill_watch.py
"""
import json
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta

from winotify import Notification

SKILLS_DIR = r"C:\Users\User\.claude\skills"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_JSON_PATH = os.path.join(ROOT, "data", "skills.json")
BANGKOK = timezone(timedelta(hours=7))


def today_str() -> str:
    return datetime.now(BANGKOK).strftime("%Y-%m-%d")


def read_description(skill_path: str) -> str:
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.exists(skill_md):
        return ""
    with open(skill_md, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^description:\s*>?\s*\n?(.*?)(?=\nmetadata:|\n---|\Z)", text, re.DOTALL | re.MULTILINE)
    if not m:
        return ""
    desc = " ".join(line.strip() for line in m.group(1).splitlines() if line.strip())
    return desc[:150]


def scan_current_skills() -> dict:
    if not os.path.isdir(SKILLS_DIR):
        return {}
    skills = {}
    for name in sorted(os.listdir(SKILLS_DIR)):
        path = os.path.join(SKILLS_DIR, name)
        if os.path.isdir(path):
            skills[name] = read_description(path)
    return skills


def load_previous() -> dict:
    if os.path.exists(SKILLS_JSON_PATH):
        with open(SKILLS_JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return {sk["name"]: sk for sk in data.get("skills", [])}
    return {}


def main():
    current = scan_current_skills()
    previous = load_previous()
    today = today_str()
    is_first_run = not previous

    new_names = [name for name in current if name not in previous]
    changed_desc = [
        name for name in current
        if name in previous and current[name] != previous[name].get("description", "")
    ]

    # On the very first run there's nothing to diff against, so the whole
    # inventory is the starting baseline, not "newly discovered" - backdate
    # first_seen so nothing wrongly shows a "new" badge on day one.
    baseline_date = "2020-01-01" if is_first_run else today

    merged = []
    for name in sorted(current):
        prev = previous.get(name)
        merged.append({
            "name": name,
            "description": current[name],
            "first_seen": prev["first_seen"] if prev else baseline_date,
        })

    has_changes = bool(new_names) or bool(changed_desc) or is_first_run

    with open(SKILLS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump({"updated": today, "skills": merged}, f, ensure_ascii=False, indent=2)

    if is_first_run:
        print(f"first run: recorded {len(current)} skills as baseline, no notification sent")
        subprocess.run(["python", "scripts/generate.py"], cwd=ROOT, check=True)
        subprocess.run(["git", "add", "data/skills.json"] + [f for f in os.listdir(ROOT) if f.endswith(".html")], cwd=ROOT, check=False)
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
        subprocess.run(["git", "commit", "-m", f"Skill inventory baseline ({len(current)} skills)"], cwd=ROOT, check=False)
        subprocess.run(["git", "push"], cwd=ROOT, check=False)
        return

    if not new_names and not changed_desc:
        print(f"no new skills since last check ({len(current)} total)")
        return

    if new_names:
        lines = [f"• {name}: {current[name][:80]}" for name in new_names[:5]]
        body = "\n".join(lines)
        if len(new_names) > 5:
            body += f"\n…และอีก {len(new_names) - 5} skill ใหม่"
        Notification(
            app_id="Claude Code Skills",
            title=f"มี skill ใหม่ {len(new_names)} ตัวที่คุณยังไม่เคยรู้! (ดูในเว็บ capabilities.html ด้วย)",
            msg=body,
        ).show()

    subprocess.run(["python", "scripts/generate.py"], cwd=ROOT, check=True)
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    commit_msg = f"Skill watch: {len(new_names)} new skill(s), {len(changed_desc)} description update(s)"
    result = subprocess.run(["git", "commit", "-m", commit_msg], cwd=ROOT, check=False, capture_output=True, text=True)
    push_result = subprocess.run(["git", "push"], cwd=ROOT, check=False, capture_output=True, text=True)

    print(f"notified about {len(new_names)} new skill(s): {', '.join(new_names)}")
    if push_result.returncode != 0:
        print(f"WARNING: git push failed: {push_result.stderr}")


if __name__ == "__main__":
    main()
