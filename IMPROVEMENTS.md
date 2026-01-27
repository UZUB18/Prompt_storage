# Prompt Library (PROMPT_storage_v1) - Improvement Ideas

This app is a solid, clean CustomTkinter "prompt library" with:
- JSON persistence (`src/storage.py` -> `data/prompts.json`)
- Search + category filter (`src/components/prompt_list.py`, `src/app.py`)
- Editor with save/copy/delete and "test in AI" shortcuts (`src/components/prompt_editor.py`)
- Import/export (`src/app.py`, `src/storage.py`)

Below is a purely additive / improvement-only backlog. Items are grouped by impact area and tagged with rough effort:
- **S** = small (hours)
- **M** = medium (1-3 days)
- **L** = larger (multi-day / bigger refactor)

## UX + workflow (high impact)

### Search + browse quality upgrades (done)

- **S** Sort options: **Recently updated**, **Name A->Z**, **Created**; default to recently updated. ✅
- **S** Show a 1-2 line preview snippet in list items (first non-empty line of content). ✅
- **S** Add "empty results" state ("No prompts match your search/filter"). ✅
- **S** Debounce search input (avoid rebuilding list on every keystroke for large libraries). ✅
- **S** Add "Clear search" (x button) and `Esc` to clear/focus logic. ✅

- **S** Add "Unsaved changes" guard when switching prompts (confirm Save / Discard / Cancel).
- **S** Add "Unsaved changes" guard on window close (`WM_DELETE_WINDOW`).
- **S** Add keyboard shortcuts: `Ctrl+N` (new), `Ctrl+S` (save), `Ctrl+F` (focus search), `Del` (delete), `Ctrl+D` (duplicate).
- **S** Add "Duplicate prompt" action (keeps content/tags/category, new `id`, new name like "(copy)").
- **S** Add quick "Copy" from list items (context menu / right-click), not only from the editor.
- **S** Add "Rename" from list context menu (no need to open editor first).
- **S** Make filter chips include **Other** (currently hidden) and optionally "All categories" dropdown.
- **S** Show counts per category (e.g., Persona (12)).
- **M** Add multi-select + bulk actions (delete, export, tag). ✅
- **M** Add tag chips UI (clickable tags, quick add/remove, tag autocomplete from existing tags). ✅
- **M** Add favorites/pins (star a prompt; pin section at top). ✅
- **M** Add "history / versions" for a prompt (lightweight: keep last N revisions per prompt). ✅
- **M** Add "scratchpad" panel (temporary text you can copy into prompts).
- **L** Add a command palette (Ctrl+P) to jump to prompts/actions quickly. ✅

## Data integrity + reliability

- **S** Write JSON atomically (write temp file + replace) to avoid corruption on crash/power loss. ✅
- **S** Add a simple backup rotation (e.g., `prompts.json.bak1..bak5`) on each save. ✅
- **S** Add file-locking / concurrency protection (avoid losing updates if two app instances run).
- **S** Handle corrupted JSON gracefully: show an error toast + offer "restore from backup".
- **S** Make `Prompt.from_dict()` tolerant to unknown categories (fallback to `Other` instead of raising).
- **S** Validate imported JSON structure (and show useful error messages instead of crashing). ✅
- **S** Add "Export single prompt" and "Export selected prompts" (not only full library).
- **M** Support import merge strategies: by `id`, by `name`, or "create duplicates".
- **M** Add schema versioning + migrations (future-proof file format).
- **L** Consider switching persistence to SQLite (optional) for large libraries + fast search + reliability.

## Storage location + portability

- **S** Move default storage out of the repo folder into an OS-appropriate user data directory:
  - Windows: `%APPDATA%\\PromptLibraryPro\\prompts.json` (or via `platformdirs`)
- **S** Add "Choose library location..." setting (store path in a small config file).✅
- **S** Add "Open data folder" button for quick backups.
- **M** Add "portable mode" (store data alongside the executable when a flag/file is present).

## Security + privacy (prompts often contain secrets)

- **S** Add "Sensitive prompt" toggle: hide content until "reveal" (prevents shoulder-surfing).
- **S** Add "Copy warning" for sensitive prompts (confirm before clipboard copy).
- **M** Add optional encryption-at-rest (password-based; keep salt/params with file).
- **M** Store encryption key via OS credential store when available.
- **M** Add auto-lock after inactivity (requires unlock to reveal/copy).

## "Test in AI" improvements (current Brave + paste flow)

- **S** Make `pyautogui` optional (feature-gated); if unavailable, just copy + open URL.
- **S** Replace "auto paste" with a safer flow: copy to clipboard + open site + toast "Copied; paste when ready".
- **S** Add a settings dropdown for preferred browser and/or "use system default".
- **S** Add per-service URLs and allow custom endpoints (some people use self-hosted/UIs).
- **M** Add "Send selection" vs "Send full prompt" (copy only highlighted text from editor).
- **M** Add a "Prompt runner" concept: pick model/site + open with prefilled text when supported.
- **L** Optional: direct API integrations (OpenAI/Anthropic/etc.) with keys stored securely.

## Editor quality-of-life

- **S** Add token/word/line count (word count is dependency-free; token count could be optional).
- **S** Add "Find" (`Ctrl+F`) and "Find/Replace" (`Ctrl+H`) inside the editor.
- **S** Add "Format" helpers: trim trailing spaces, normalize line endings.
- **S** Add "Copy as..." options: plain text, Markdown code block, JSON object.
- **M** Add snippets / variables:
  - Use placeholder syntax like `{project}` and the existing `VariableInputDialog` as a "Fill variables" action.
- **M** Add undo/redo improvements (ensure `Ctrl+Z/Ctrl+Y` behave consistently).
- **M** Add a read-only preview mode (e.g., rendered Markdown) next to the editor.
- **L** Add syntax highlighting / structured prompt blocks (system/user/assistant sections).

## Discoverability + onboarding

- **S** Add a `README.md` with install/run steps, screenshots, and data location.
- **S** Add an "About" dialog (version, data path, export location).
- **S** Add sample prompts on first run (optional "import starter library").
- **M** Add in-app help: tooltip hints for filters, tags, copy, AI buttons.

## Visual polish + accessibility

- **S** Dark mode toggle (and persist preference).
- **S** Improve contrast checks (muted text on light gray can get low-contrast).
- **S** Ensure scaling works on high-DPI displays (font sizes + padding).
- **S** Add proper window icon (`.ico`) and taskbar icon; use existing icon files.
- **M** Add UI state persistence: last selected prompt, last filter/search, window size/position.
- **M** Add accessible focus order + keyboard-only navigation in list/editor.

## Engineering / maintainability

- **S** Remove unused imports (e.g., `urllib.parse`, optional PIL block if not used).
- **S** Separate concerns: keep UI layout code, actions, and persistence clearly layered.
- **S** Add type-check friendly patterns (a few more type hints; avoid bare `except:`).
- **S** Add logging (to a file in the data directory) for import/export errors and unexpected exceptions.
- **M** Add unit tests for storage: atomic save, import merge behavior, category fallback.
- **M** Add a simple CI step (run tests, lint) if you publish the repo.

## Distribution

- **S** Add a one-command run guide (`python -m venv ...`, `pip install -r requirements.txt`, `python main.py`).
- **M** Add packaging (PyInstaller) to produce a single Windows executable + include icons.
- **M** Add automatic updates (optional; depends on how you want to ship it).

## Nice-to-have "power features"

- **M** Quick "copy prompt name + content" template for sharing.
- **M** Cross-library diff: compare two prompts side-by-side.
- **M** Global hotkey to search/copy a prompt without opening the full app.
- **L** Cloud sync (Dropbox/GDrive/iCloud-like) with conflict resolution.
