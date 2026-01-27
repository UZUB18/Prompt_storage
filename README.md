# Prompt Library Pro

Desktop app for managing, versioning, and searching your prompt library (CustomTkinter).

## Highlights

- **Pinned prompts** (★) with a dedicated **Pinned** filter
- **Tag chips UI** (add/remove tags with Enter or comma)
- **Command palette** (`Ctrl+P`) to jump to prompts instantly
- **Version history** with one-click restore + **Version+** button
- **Multi-select + bulk actions** (export, delete, add/remove tags)
- Privacy options: **Sensitive** prompts hide content until revealed

## Download (Windows)

1. Go to **Releases**:
   - https://github.com/UZUB18/Prompt_storage/releases/latest
2. Download `PromptLibraryProSetup.exe`
3. Run the installer, then launch **Prompt Library Pro** from Start Menu / Windows Search.

> Note: On some PCs, Windows SmartScreen may warn because the installer is not code-signed.  
> Use **More info → Run anyway**.

## Everyday usage tips

### Keyboard shortcuts

- `Ctrl+N` — New prompt
- `Ctrl+S` — Save
- `Ctrl+F` — Find (editor) / focus search
- `Ctrl+H` — Replace (editor)
- `Ctrl+D` — Duplicate prompt
- `Ctrl+P` — Command palette
- `Delete` — Delete selected prompt
- `Esc` — Clear search or exit selection mode

### Pinned prompts

Click the **★** icon in the list or editor header to pin/unpin.  
Pinned prompts float to the top and are available in the **Pinned** filter.

### Tag chips

Type a tag and press **Enter** or **comma** to create a chip.  
Use **Backspace** on empty input to remove the last chip.

### Versioning

- **History** button shows the last 10 versions of the prompt.
- **Version+** automatically bumps the name: `v1 → v2 → v3`.
- Restoring a version also creates a new version of the current state.

### Multi-select + bulk actions

Click **Select** (top right of the Library) to enter multi-select mode.  
You can click anywhere on a prompt card to select it.  
**Shift‑click** selects a range.

Bulk actions include:
- **Export** selected prompts
- **Delete** selected prompts
- **Tags** → add or remove a tag across selection

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
