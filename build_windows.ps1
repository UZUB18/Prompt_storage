param(
  [ValidateSet("onedir","onefile")]
  [string]$Mode = "onedir"
)

$ErrorActionPreference = "Stop"

Write-Host "== Prompt Library Pro: Windows build ($Mode) =="

# Pick a Python launcher
$PY = $null
# Prefer the Windows launcher (`py`) because `python` can be a Microsoft Store alias stub.
if (Get-Command "py" -ErrorAction SilentlyContinue) {
  $PY = "py"
} elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
  $PY = "python"
} else {
  throw "Python not found. Install Python 3.x and ensure 'python' (or 'py') is on PATH."
}

# Create / reuse venv
if (-not (Test-Path ".\\.venv\\Scripts\\python.exe")) {
  & $PY -m venv .venv
}

& .\\.venv\\Scripts\\python.exe -m pip install --upgrade pip
& .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
& .\\.venv\\Scripts\\python.exe -m pip install pyinstaller

$oneFlag = if ($Mode -eq "onefile") { "--onefile" } else { "" }

# NOTE:
# - --windowed avoids a console window for GUI apps.
# - --add-data ensures the window icon file is available at runtime (PyInstaller extracts it).
& .\\.venv\\Scripts\\python.exe -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  $oneFlag `
  --paths "." `
  --name "PromptLibraryPro" `
  --icon "prompt_library.ico" `
  --add-data "prompt_library.ico;." `
  --collect-submodules "src" `
  main.py

Write-Host ""
Write-Host "Build complete:"
if ($Mode -eq "onefile") {
  Write-Host "  dist\\PromptLibraryPro.exe"
} else {
  Write-Host "  dist\\PromptLibraryPro\\PromptLibraryPro.exe"
}
Write-Host ""
Write-Host "Tip: for 'portable mode' (store prompts next to the exe), create an empty file named:"
Write-Host "  portable.txt"
