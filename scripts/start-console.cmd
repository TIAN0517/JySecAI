@echo off
rem Windows console (jysecai.exe :8855) — logon autostart + supervisor.
call "C:\ProgramData\jysecai\ensure-stack.cmd"
exit /b %ERRORLEVEL%
