param(
  [ValidateSet("onedir")]
  [string]$Mode = "onedir"
)

$ErrorActionPreference = "Stop"

Write-Host "== Prompt Library Pro: Installer build =="

# 1) Build the app (PyInstaller onedir)
& .\\build_windows.ps1 -Mode $Mode

# 2) Find Inno Setup Compiler
$iscc = $null
$candidates = @(
  "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
  "C:\\Program Files\\Inno Setup 6\\ISCC.exe"
)
foreach ($c in $candidates) {
  if (Test-Path $c) { $iscc = $c; break }
}
if (-not $iscc -and (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue)) {
  $iscc = "ISCC.exe"
}
if (-not $iscc) {
  throw "Inno Setup not found. Install Inno Setup 6, then re-run. (Expected ISCC.exe.)"
}

# 3) Compile installer
New-Item -ItemType Directory -Force -Path ".\\dist-installer" | Out-Null
& $iscc ".\\installer\\PromptLibraryPro.iss"

Write-Host ""
Write-Host "Installer created:"
Write-Host "  dist-installer\\PromptLibraryProSetup.exe"

