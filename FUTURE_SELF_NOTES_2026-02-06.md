# Future-self notes (iterative timeline)

Quick history in clear step order.

## Day 1 — Feb 6, 2026 (Core throughput upgrades)

### Step 1 — Command palette expansion
- Added prompt search/open in palette.
- Added action execution: new prompt, duplicate, focus search, snippets, variable fill, preview toggle, token mode toggle, pin toggle.

### Step 2 — Snippet workflow
- Added `SnippetPickerDialog`.
- Insert snippet at caret or replace selection.
- Wired to button, `Ctrl+I`, and command palette.

### Step 3 — Variable fill workflow
- Detects `{variable}` placeholders.
- Uses `VariableInputDialog`.
- Replaces placeholders while leaving empty values unchanged.

### Step 4 — Split preview toggle
- Added preview split toggle in UI.
- Added shortcut `Ctrl+Shift+M`.
- Persisted with `preview_split_enabled`.

### Step 5 — Draft autosave + recovery
- Added `drafts.json` support in storage.
- Methods: `load_drafts`, `load_draft`, `save_draft`, `clear_draft`.
- Debounced draft autosave while typing.
- Restore draft on prompt select.
- Clear draft on explicit save/delete.

### Step 6 — Token count mode
- Added token mode config:
  - `approx` (default)
  - `exact` (optional with `PROMPTLIB_TOKENIZER=tiktoken` + dependency)

### Step 7 — Markdown preview readability
- Improved rendering for headings, bullets, numbered lists, quotes.
- Added inline bold/italic/code rendering.
- Added fenced code block rendering.
- Render links as label + URL text.

### Step 8 — Tag chip recursion crash fix
- Fixed `RecursionError` in `TagChipsInput` layout.
- Added layout re-entry guard.
- Added debounced/scheduled relayout.
- Added width-change gating.
- Forced relayout only on add/remove/clear events.

---

## Day 2 — Feb 7, 2026 (UI polish iteration)

### Step 9 — Sidebar filter menu responsiveness (`src/app.py`)
- Made filter chips shrink correctly at small widths.
- Added adaptive label modes: `full` / `compact` / `tight`.
- Reduced overlap across window sizes and UI scales.

### Step 10 — Tags input polish (`src/components/tag_chips.py`)
- Fixed hidden/clipped placeholder behavior.
- Improved text centering/readability (font/height/placeholder color).
- Entry now expands to remaining row width while preserving chip wrap.

### Step 11 — Prompt editor form layout redesign (`src/components/prompt_editor.py`)
- Name field moved to full-width top row and made larger.
- Category + Tags moved below (Category left, Tags right).
- Normalized tags placeholder text to `...`.

---

## Files touched (combined)
- `src/app.py`
- `src/components/dialogs.py`
- `src/components/prompt_editor.py`
- `src/components/tag_chips.py`
- `src/config.py`
- `src/storage.py`

## Next-pass checklist
- Clean duplicate legacy methods in `prompt_editor.py`.
- Consider moving snippet definitions from hardcoded list to persistent config/storage.
- Add regression checks for:
  - prompt select + draft restore
  - snippet insert
  - variable fill
  - tag chip layout stability
