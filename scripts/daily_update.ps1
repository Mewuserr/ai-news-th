# MEW Station - daily news engine (runs LOCALLY on the PC via Task Scheduler)
# Design: the AI does ONLY research + writes the news JSON. Everything that must
# not fail (generate.py, git commit/push, the run log) is done by plain script
# code below, so an AI hiccup can never block publishing.
# Root cause this replaces: the cloud routine fired daily but could never git push
# (read-only clone, no credentials). This machine already has working push creds.
# NOTE: keep this file ASCII-only. Windows PowerShell 5.1 misreads UTF-8 without BOM.

$ErrorActionPreference = 'Continue'
$repo = 'E:\ai-news-th'
Set-Location $repo

# Make sure the npm global bin (where 'claude' lives) is on PATH when launched by Task Scheduler
$env:PATH = "$env:APPDATA\npm;$env:PATH"

$today = (Get-Date).ToString('yyyy-MM-dd')          # local time = ICT (UTC+7)
$utc   = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm')
$newsPath = Join-Path $repo "data\news\$today.json"

Write-Output "=== daily_update run $utc UTC (today=$today) ==="

# 1) Sync with GitHub first (in case a session pushed from elsewhere)
git pull --rebase --autostash

# 2) AI step: research + write today's news JSON. NO git, NO generate here.
$prompt = @"
Today is $today (Asia/Bangkok timezone, UTC+7). You are the daily AI/space news engine for this repository.
Steps:
1. Read scripts/engine-prompt.md (follow its sourcing list and JSON schema in sections 1-4).
2. Read data/latest.json and dedupe by 'url' so you never repeat a story already published.
3. Use WebSearch/WebFetch to find REAL AI and space news from roughly the last 24-48 hours from the official company blogs and tech/space press listed in engine-prompt.md. Never invent news or URLs.
4. Write 4-10 genuinely important or interesting items to data/news/$today.json as a JSON array, each object exactly matching the schema: source, title_th, summary_th, category (model_release|product|funding|research|policy|space|other), importance (major|normal), url, and optional context_th. Write all Thai text naturally (not word-for-word translation). For any new feature/model, emphasize what it can actually DO. Keep 'major' to 0-2 truly big stories.
5. If you have at least 2 items, also write data/narrative/$today.json as {"narrative_th":"one flowing Thai paragraph weaving today's stories together"}.
Hard rules: WRITE ONLY these files - data/news/$today.json and optionally data/narrative/$today.json. Do NOT create or modify any other file (in particular do NOT touch data/engine-log.md). Do NOT run git, do NOT run python/generate.py, do NOT run any shell/Bash command. Only use WebSearch, WebFetch, Read, Write, Edit, Glob, Grep. The wrapper script publishes; your only job is to produce the JSON file(s).
"@

claude -p $prompt --allowedTools "WebSearch" "WebFetch" "Read" "Write" "Edit" "Glob" "Grep" --permission-mode acceptEdits |
    Out-File -Encoding utf8 (Join-Path $repo "scripts\daily_update_claude.log")

# 3) Validate what the AI produced (list, non-empty, valid JSON)
$count = 0
$valid = $false
if (Test-Path $newsPath) {
    $count = & python -c "import json;d=json.load(open(r'$newsPath',encoding='utf-8'));print(len(d) if isinstance(d,list) else -1)" 2>$null
    if ($LASTEXITCODE -eq 0 -and [int]$count -gt 0) { $valid = $true }
}
if ((-not $valid) -and (Test-Path $newsPath)) {
    # bad/empty file would break generate.py - remove it so the site stays on the last good day
    Remove-Item $newsPath -Force
    Write-Output "AI output invalid/empty - removed $newsPath"
}

# 4) Rebuild the whole site from JSON (deterministic, safe even with no new file)
python scripts\generate.py
$genOk = ($LASTEXITCODE -eq 0)

# 5) Write the run log (always - this is the daily heartbeat in git history)
if ($valid -and $genOk)            { $status = "OK: wrote $count news items, generate.py ok, pushing" }
elseif ((-not $valid) -and $genOk) { $status = "NO NEW NEWS (or AI produced nothing usable) - site rebuilt, heartbeat only" }
else                               { $status = "FAIL: generate.py error - see scripts\daily_update_claude.log" }
"- $utc UTC [LOCAL PC]: $status" | Out-File -Append -Encoding utf8 (Join-Path $repo "data\engine-log.md")

# 6) Publish to GitHub (this machine has working push credentials)
git add -A
git commit -m "News auto-update $today ($status)"
git push origin main
if ($LASTEXITCODE -eq 0) { Write-Output "PUSH OK" } else { Write-Output "PUSH FAILED (exit $LASTEXITCODE)" }
Write-Output "=== done ==="
