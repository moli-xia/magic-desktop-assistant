@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ========================================
echo   Wallpaper Downloader - GitHub Upload
echo ========================================
echo.

REM Optional: allow custom remote via env var GIT_REMOTE_URL
if not defined GIT_REMOTE_URL (
  for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul') do set GIT_REMOTE_URL=%%i
)

REM 0) Check git (with PortableGit fallback)
where git >nul 2>&1
if errorlevel 1 (
  if exist .tools\PortableGit\bin\git.exe (
    set "PATH=%CD%\.tools\PortableGit\bin;%CD%\.tools\PortableGit\cmd;%PATH%"
  ) else (
    echo Git not found. Trying to install PortableGit now...
    powershell -ExecutionPolicy Bypass -File install_git.ps1 || (
      echo Install failed. Please check your network and try again.
      pause & exit /b 1
    )
    if exist .tools\PortableGit\bin\git.exe (
      set "PATH=%CD%\.tools\PortableGit\bin;%CD%\.tools\PortableGit\cmd;%PATH%"
    ) else (
      echo PortableGit not found after install.
      pause & exit /b 1
    )
  )
)

REM 1) Ensure repo
if not exist .git (
  git init || (echo ERROR: git init failed. & pause & exit /b 1)
)

REM Basic identity (safe defaults; you can override globally)
git config user.name >nul 2>&1 || git config user.name "moli-xia" >nul 2>&1
git config user.email >nul 2>&1 || git config user.email "moli-xia@users.noreply.github.com" >nul 2>&1

REM 2) Stage and commit
git add -A
for /f %%s in ('git status --porcelain') do set HAS_CHANGES=1
if defined HAS_CHANGES (
  set MSG=%~1
  if not defined MSG set MSG=chore: auto upload
  git commit -m "%MSG%" || echo WARN: commit failed or aborted.
) else (
  echo No changes to commit.
)

REM Ensure at least one commit exists (for new repos)
git rev-parse --verify HEAD >nul 2>&1
if errorlevel 1 (
  set MSG=%~1
  if not defined MSG set MSG=chore: initial empty commit
  git commit --allow-empty -m "%MSG%" >nul 2>&1
)

REM 3) Determine branch
for /f %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set BRANCH=%%b
if not defined BRANCH set BRANCH=main
if /i "!BRANCH!"=="HEAD" set BRANCH=main
git branch -M !BRANCH! >nul 2>&1

REM 4) Ensure remote origin
if not defined GIT_REMOTE_URL (
  for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul') do set GIT_REMOTE_URL=%%i
)
if not defined GIT_REMOTE_URL (
  set "GIT_REMOTE_URL=https://github.com/moli-xia/desk-wallpapers.git"
  echo Using default remote: !GIT_REMOTE_URL!
)
git remote remove origin >nul 2>&1
git remote add origin "!GIT_REMOTE_URL!" 2>nul || git remote set-url origin "!GIT_REMOTE_URL!"

REM 5) Pull --rebase (ignore errors on first push)
git pull --rebase origin !BRANCH! >nul 2>&1

REM 6) Push
git push --set-upstream origin !BRANCH!
if errorlevel 1 (
  echo.
  echo Upload FAILED.
  echo If authentication is required, run: git config --global credential.helper manager
  echo Or use: git remote set-url origin https://<TOKEN>@github.com/<user>/desk-wallpapers.git
  echo If you do not own the default remote, set your own and rerun:
  echo   setx GIT_REMOTE_URL https://github.com/<your-username>/desk-wallpapers.git
  echo   ^(reopen terminal^) and run upload.bat again.
  echo You can also try: powershell -ExecutionPolicy Bypass -File upload.ps1
  pause & exit /b 1
) else (
  echo.
  echo Upload SUCCEEDED.
)

endlocal
pause