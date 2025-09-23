Param(
  [string]$Repo="https://github.com/moli-xia/desk-wallpapers.git",
  [string]$Branch="main"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Wallpaper Downloader - GitHub Upload" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Ensure UTF-8 output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Check git
try { git --version | Out-Null } catch {
  Write-Error "Git not found. Install: https://git-scm.com/download/win"
  exit 1
}

if (-not (Test-Path .git)) {
  git init | Out-Null
}

git config user.name "moli-xia" | Out-Null
git config user.email "moli-xia@users.noreply.github.com" | Out-Null

git add -A
try {
  git commit -m "chore: build and docs updates; cross-platform CI" | Out-Null
} catch {
  Write-Host "No changes to commit."
}

git branch -M $Branch | Out-Null
try { git remote add origin $Repo | Out-Null } catch {}

try { git pull --rebase origin $Branch | Out-Null } catch {}

git push -u origin $Branch

Write-Host "Done. Repo: $Repo" -ForegroundColor Green
