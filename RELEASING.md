# Releasing & Updating (GitHub + Windows Installer)

This repo ships a Windows installer via **GitHub Releases**. The installer is built automatically by **GitHub Actions** when you push a version tag like `v0.1.0`.

---

## What we set up

- **PyInstaller** builds the GUI app (Windows, no console).
- **Inno Setup** packages the PyInstaller build into a standard Windows installer (`PromptLibraryProSetup.exe`).
- **GitHub Actions** builds + attaches the installer to a GitHub Release whenever you push a tag matching `v*`.

Key files:
- `build_windows.ps1` — builds the app with PyInstaller
- `build_installer.ps1` — builds the app, then compiles the installer using Inno Setup
- `installer/PromptLibraryPro.iss` — Inno Setup script (per-user install, no admin/UAC)
- `.github/workflows/release-windows-installer.yml` — CI that builds and publishes the installer on tag push

---

## Day-to-day Git workflow (commits & pushes)

From repo root (PowerShell):

```powershell
git pull
git status

# make changes...

git add -A
git commit -m "your message here"
git push
```

Tip: keep commits small and descriptive (e.g., `fix:`, `feat:`, `docs:`).

---

## Release a new installer on GitHub (recommended path)

### 1) Pick a new version number

Use tags like:
- `v0.1.1` (small fixes)
- `v0.2.0` (new features)
- `v1.0.0` (stable major release)

### 2) Make sure main is pushed

```powershell
git status
git push
```

### 3) Create and push a tag (this triggers the installer build)

```powershell
git tag v0.1.1
git push origin v0.1.1
```

### 4) Wait for GitHub Actions

On GitHub:
- Repo → **Actions** → open **Build Windows Installer (Release)** → wait for ✅

When it finishes, the Release will contain an asset:
- `PromptLibraryProSetup.exe`

Users download here:
- https://github.com/UZUB18/Prompt_storage/releases/latest

---

## Build/test locally (optional but recommended before tagging)

### Build installer locally

Prereqs:
- Python 3.x installed
- Inno Setup 6 installed

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\build_installer.ps1
```

Output:
- `dist-installer\PromptLibraryProSetup.exe`

### Test the install

1. Run `PromptLibraryProSetup.exe`
2. Launch from Start Menu / Windows Search: **Prompt Library Pro**

---

## Notes / behaviors that matter when shipping

### Data storage location

When installed, prompts are stored per-user in:
- `%APPDATA%\PromptLibraryPro\prompts.json`

### Portable mode (optional)

If a file named `portable.txt` (or `PROMPTLIB_PORTABLE`) exists next to the executable, the app stores data in:
- `.\data\prompts.json` (next to the app)

### Why you still see “Source code (zip/tar.gz)” in Releases

GitHub always shows those. The important download is the **installer asset**:
- `PromptLibraryProSetup.exe`

---

## If the Release is missing the installer asset

1. GitHub → **Actions** → open the workflow run for your tag
2. If it failed, open the failing step and read the error
3. Fix the issue, commit/push, then create a new tag (e.g., `v0.1.2`)

Fast manual fallback:
- Edit the Release and upload `dist-installer\PromptLibraryProSetup.exe` yourself.

