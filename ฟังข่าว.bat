@echo off
chcp 65001 >nul
title ฟังข่าว AI วันนี้
echo กำลังโหลดข่าว AI วันนี้ ระบบจะเริ่มพูดในไม่ช้า...
"C:\Users\User\AppData\Local\Programs\Python\Python310\python.exe" "E:\ai-news-th\scripts\audio_briefing.py"
echo.
echo จบข่าววันนี้แล้วครับ กด Enter เพื่อปิดหน้าต่างนี้
pause >nul
