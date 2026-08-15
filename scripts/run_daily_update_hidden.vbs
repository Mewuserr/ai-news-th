' Launch daily_update.ps1 with no visible console window.
' Called by the "MEW Station Daily News" scheduled task at logon.
' Runs in the logged-on user's session on purpose - the script does git push and
' calls "claude -p", and both need credentials that only this session can decrypt.
Set sh = CreateObject("WScript.Shell")
rc = sh.Run("powershell.exe -NoProfile -ExecutionPolicy Bypass -File ""E:\ai-news-th\scripts\daily_update.ps1""", 0, True)
WScript.Quit rc
