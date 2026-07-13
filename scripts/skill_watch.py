"""Local-only, PRIVATE "did I gain a new capability?" watcher.

Not part of the AI news engine, and NOT connected to the public git repo or
website in any way - this only touches files on the user's own PC outside
E:\\ai-news-th, so nothing here can ever end up on the public site or in git
history. Scans installed Claude Code skills (~/.claude/skills) and diffs
against a private local snapshot.

Delivery mechanism (how the user actually finds out) is intentionally left
unimplemented pending a decision on the right private channel - see
STATUS.md 2026-07-13 entry.

Usage: python skill_watch.py
"""
import json
import os
import re
from datetime import datetime, timezone, timedelta

SKILLS_DIR = r"C:\Users\User\.claude\skills"
PRIVATE_STATE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", r"C:\Users\User\AppData\Local"), "ClaudeSkillWatch")
STATE_PATH = os.path.join(PRIVATE_STATE_DIR, "skills.json")
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
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return {sk["name"]: sk for sk in data.get("skills", [])}
    return {}


def main():
    current = scan_current_skills()
    previous = load_previous()
    today = today_str()
    is_first_run = not previous

    new_names = [name for name in current if name not in previous]

    baseline_date = "2020-01-01" if is_first_run else today
    merged = []
    for name in sorted(current):
        prev = previous.get(name)
        merged.append({
            "name": name,
            "description": current[name],
            "first_seen": prev["first_seen"] if prev else baseline_date,
        })

    os.makedirs(PRIVATE_STATE_DIR, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"updated": today, "skills": merged}, f, ensure_ascii=False, indent=2)

    if is_first_run:
        print(f"first run: recorded {len(current)} skills as private baseline at {STATE_PATH}")
        return

    if not new_names:
        print(f"no new skills since last check ({len(current)} total)")
        return

    print(f"{len(new_names)} new skill(s) found: {', '.join(new_names)}")
    print("(delivery mechanism not yet decided - this only updates the private local file for now)")


if __name__ == "__main__":
    main()
