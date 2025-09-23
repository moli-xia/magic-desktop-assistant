Param(
  [string]$Version = '2.47.0'
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host 'Installing PortableGit ...'
$file = "PortableGit-$Version-64-bit.7z.exe"
$urls = @(
  # 1) Latest channel (no version in filename)
  "https://github.com/git-for-windows/git/releases/latest/download/PortableGit-64-bit.7z.exe",
  "https://ghproxy.com/https://github.com/git-for-windows/git/releases/latest/download/PortableGit-64-bit.7z.exe",
  # 2) Version-specific mirrors
  "https://github.com/git-for-windows/git/releases/download/v$Version.windows.1/$file",
  "https://ghproxy.com/https://github.com/git-for-windows/git/releases/download/v$Version.windows.1/$file",
  "https://download.fastgit.org/git-for-windows/git/releases/download/v$Version.windows.1/$file"
)

$tmp = Join-Path $env:TEMP $file
$dest = Join-Path (Get-Location) '.tools/PortableGit'
New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null

$downloaded = $false
function Test-ValidDownload($path) {
  try {
    if (Test-Path $path) {
      $len = (Get-Item $path).Length
      return ($len -gt 5242880)  # > 5MB
    }
  } catch {}
  return $false
}
foreach ($u in $urls) {
  try {
    Write-Host "Downloading: $u"
    if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
    Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile $tmp -TimeoutSec 300
    if (Test-ValidDownload $tmp) { $downloaded = $true; break }
  } catch { Write-Warning $_.Exception.Message }
}
if (-not $downloaded) { throw 'Failed to download PortableGit from all mirrors.' }

New-Item -ItemType Directory -Force -Path $dest | Out-Null
Start-Process -FilePath $tmp -ArgumentList '-y', ("-o$dest") -Wait

$gitBin = Join-Path $dest 'bin'
$gitCmd = Join-Path $dest 'cmd'
$env:Path = "$gitBin;$gitCmd;" + $env:Path

git --version
Write-Host 'PortableGit installed to' $dest

