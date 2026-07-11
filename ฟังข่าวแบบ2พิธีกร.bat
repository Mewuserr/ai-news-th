@echo off
chcp 65001 >nul
title ฟังข่าว AI แบบ 2 พิธีกร
echo กำลังเตรียมเสียง 2 พิธีกร รอสักครู่...
"C:\Users\User\AppData\Local\Programs\Python\Python310\python.exe" -c "import sys; sys.path.insert(0, 'scripts'); from audio_briefing import generate_and_play_dialogue; generate_and_play_dialogue(play=True)"
echo.
echo จบข่าววันนี้แล้วครับ กด Enter เพื่อปิดหน้าต่างนี้
pause >nul
