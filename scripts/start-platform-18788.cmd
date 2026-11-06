@echo off
rem Governance / scanner platform lives in Kali WSL (8788/8790/worker).
rem This wrapper exists so the JySecAIPlatform scheduled task no longer fails.
call "C:\ProgramData\jysecai\ensure-stack.cmd"
exit /b %ERRORLEVEL%
