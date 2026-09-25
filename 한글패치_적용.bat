@echo off
chcp 949 >nul
setlocal
title Black/Matrix Advanced 한글패치 v0.7
echo.
echo   Black/Matrix Advanced (Japan) 한글패치 v0.7
echo   ------------------------------------------
echo.
echo   원본 GDI(cue+bin 3트랙)의 Track 3 파일을 이 폴더에 두고 실행하세요.
echo   Track 1/2 와 cue 는 건드리지 않습니다.
echo.
set XD=%~dp0xdelta.exe
if not exist "%XD%" (
  echo   [오류] xdelta.exe 가 이 폴더에 없습니다.
  pause & exit /b 1
)
for %%D in (1 2) do call :patch %%D
echo.
echo   끝났습니다. 패치된 Track 3 로 교체해 주세요.
pause
exit /b 0

:patch
set N=%1
set SRC=Black-Matrix Advanced (Japan) (Disc %N%) (Track 3).bin
set OUT=Black-Matrix Advanced (Japan) (Disc %N%) (Track 3) [KR].bin
if not exist "%SRC%" (
  echo   [건너뜀] Disc %N% : "%SRC%" 이 없습니다.
  goto :eof
)
echo   Disc %N% 패치 중...
"%XD%" -d -f -s "%SRC%" "bmadv_kr_0.7_disc%N%_track3.xdelta" "%OUT%"
if errorlevel 1 (
  echo   [실패] Disc %N% : 원본이 다르거나 이미 패치된 파일입니다.
) else (
  echo   [완료] "%OUT%"
)
goto :eof
