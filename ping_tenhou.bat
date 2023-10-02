@echo off
echo Running...
set seqno=0
:begin
ping b-ww.mjv.jp -n 1 > nul || (echo Ping NG %date% %time% %seqno% & echo Ping NG %date% %time% %seqno% >> pingNG.txt)
timeout -t 1 > nul
set /a seqno=seqno+1
goto begin
