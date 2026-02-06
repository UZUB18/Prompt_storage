# Future-self notes (Feb 6, 2026)

Quick summary of what was implemented in this session.

## Main feature work

- Added a **throughput-focused editor/list upgrade** foundation.
- Extended **command palette** to support:
  - prompt search/open
  - action execution (new prompt, duplicate, focus search, snippets, variable fill, preview toggle, token mode toggle, pin toggle)
- Added **snippet workflow**:
  - new `SnippetPickerDialog`
  - insert snippet at caret or replace selection
  - wired to button, shortcut (`Ctrl+I`), and command palette
- Added **variable fill workflow**:
  - detects `{variable}` placeholders
  - uses `VariableInputDialog`
  - replaces placeholders while leaving empty ones unchanged
- Added **split preview toggle** with persistence in config
  - button + shortcut (`Ctrl+Shift+M`)
  - persisted with `preview_split_enabled`

## Draft autosave + recovery

- Added lightweight draft storage:
  - new `drafts.json` in storage data dir
  - methods: `load_drafts`, `load_draft`, `save_draft`, `clear_draft`
- Editor now autosaves draft (debounced) while typing.
- Selecting a prompt restores saved draft if present.
- Explicit save/delete clears that prompt's draft.

## Token count mode

- Token/word/line count area now supports throughput token mode behavior.
- Added config for token mode:
  - `approx` (default)
  - `exact` (optional via `PROMPTLIB_TOKENIZER=tiktoken` and dependency availability)

## Markdown reading preview improvement

- Reworked preview rendering to display human-readable styled text:
  - headings, bullets, numbered lists, block quotes
  - inline bold/italic/code
  - fenced code blocks
  - links rendered as label + URL text

## Crash fix performed

- Fixed a `RecursionError` in tag chip layout (`TagChipsInput`) caused by configure/layout feedback loops.
- Added:
  - layout re-entry guard
  - scheduled/debounced layout
  - width-change gating
  - forced relayout on tag add/remove/clear only

## Files touched

- `src/app.py`
- `src/components/dialogs.py`
- `src/components/prompt_editor.py`
- `src/components/tag_chips.py`
- `src/config.py`
- `src/storage.py`

## Notes for next pass

- Clean up duplicate legacy methods in `prompt_editor.py` now that override-style additions exist.
- Consider moving snippet definitions from in-code list to persisted storage/config.
- Add small regression checks around:
  - prompt select + draft restore
  - snippet insert
  - variable fill
  - tag chip layout stability
