# Prompt Library Pro

Desktop app for managing and searching your prompt library (CustomTkinter).

## Download (Windows)

1. Go to **Releases**:
   - https://github.com/UZUB18/Prompt_storage/releases/latest
2. Download `PromptLibraryProSetup.exe`
3. Run the installer, then launch **Prompt Library Pro** from Start Menu / Windows Search.

> Note: On some PCs, Windows SmartScreen may warn because the installer is not code-signed.
> Use **More info → Run anyway**.

## Data location

By default, prompts are stored per-user in:
`%APPDATA%\PromptLibraryPro\prompts.json`

## Build from source (dev)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python main.py
```

## Build installer (Windows)

Prereqs:
- Python 3.x
- Inno Setup 6

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\build_installer.ps1
```

Output:
`dist-installer\PromptLibraryProSetup.exe`

## Releasing (GitHub)

See `RELEASING.md`.
