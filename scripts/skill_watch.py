"""Local-only "did I gain a new capability?" watcher.

Not part of the AI news engine. Runs on the user's own PC via Windows Task
Scheduler, scans installed Claude Code skills (~/.claude/skills), diffs
against data/skills.json from last run, and - only if something changed -
regenerates the site and commits+pushes so the update shows up on
capabilities.html ("🧰 เครื่องมือที่คุณมีอยู่แล้วตอนนี้").

No AI calls, no API key, no desktop notification - just a directory listing +
YAML frontmatter read + git. The website itself is the notification.

Usage: python skill_watch.py
"""
import json
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta

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
    has_changes = bool(new_names) or bool(changed_desc) or is_first_run

    if not has_changes:
        print(f"no new skills since last check ({len(current)} total)")
        return

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

    with open(SKILLS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump({"updated": today, "skills": merged}, f, ensure_ascii=False, indent=2)

    subprocess.run(["python", "scripts/generate.py"], cwd=ROOT, check=True)
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    if is_first_run:
        commit_msg = f"Skill inventory baseline ({len(current)} skills)"
    else:
        commit_msg = f"Skill watch: {len(new_names)} new skill(s), {len(changed_desc)} description update(s)"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=ROOT, check=False)
    push_result = subprocess.run(["git", "push"], cwd=ROOT, check=False, capture_output=True, text=True)

    print(f"updated site: {len(new_names)} new skill(s), {len(changed_desc)} description update(s)")
    if push_result.returncode != 0:
        print(f"WARNING: git push failed: {push_result.stderr}")


if __name__ == "__main__":
    main()
