# Prompt Library Pro — UI Polish (Less Buttons, More macOS/Linux‑like)

## What I looked at (UI surface area)

- Main window + sidebar layout: `src/app.py` (`_build_sidebar`, `_build_main_area`)
- Prompt list + list item chrome: `src/components/prompt_list.py`
- Editor header/content/footer actions: `src/components/prompt_editor.py`
- Dialog patterns (confirm/find/history/tag/command palette): `src/components/dialogs.py`
- Tag chips + toast styling: `src/components/tag_chips.py`, `src/components/toast.py`

## The core issue (why it feels “busy”)

On first launch the sidebar shows **many always-visible controls** (New, Select, Search+Clear, 6 filter buttons *with counts*, Sort dropdown, Dark mode toggle, UI Scale dropdown, and 3 footer buttons). After selecting a prompt the editor adds another dense action strip (AI buttons, Pin, Copy, Copy as, Sensitive+Reveal, Format, Version+, History, Delete, Save).

macOS/Linux apps typically reduce this via **progressive disclosure**: keep 1–3 primary actions visible, move secondary actions into **menus/overflow**, and rely on **context menus + keyboard shortcuts** for power features.

## Goals (what “more user friendly” looks like)

1. **Button budget:** fewer persistent buttons; actions appear *when relevant*.
2. **Clear hierarchy:** Search + List are the “home”; Editing has one obvious primary action.
3. **Progressive disclosure:** advanced controls in an overflow menu / preferences, not the main layout.
4. **Consistent patterns:** one place to change settings; one “More (⋯)” menu for secondary actions.

---

# Recommended visual upgrades (prioritized)

## 1) Replace “button clusters” with 1 overflow menu (biggest win)

### Sidebar footer (currently: Import / Export / Library…)
**Change:** Replace the 3 footer buttons with **one** icon button: **Settings (⚙) / More (⋯)**.

**Menu items (example):**
- Import…
- Export…
- Change Library Location…
- Preferences…
- Select mode…

**Where:** `src/app.py` (Row 8 footer)

### Editor actions (currently: Format / Version+ / History + Delete visible)
**Change:** Add a single **More (⋯)** button and move secondary actions into it:
- Format… (existing format menu can be reused)
- Version bump
- History…
- Delete… (destructive actions live in menus, not beside primary actions)

**Where:** `src/components/prompt_editor.py` (footer)

## 2) Collapse “Test in AI” into one control (not three buttons)

**Change:** Replace Gemini/GPT/Grok buttons with a single **“Test in…”** dropdown or icon button.
- Remember last used provider (so it’s 1 click next time).
- Optional: keep one “default” provider as the main click + a small arrow for the menu.

**Where:** `src/components/prompt_editor.py` (header `ai_container`)

## 3) Simplify filtering (remove the 6-button segmented control)

The current segmented control becomes especially noisy once it appends counts: `All (123)`, `Persona (42)`, etc.

**Change (recommended):** Replace the 6 buttons with **one** “Filter” control:
- `Filter: All ▾` (or `All ▾`)
  - Pinned only (toggle)
  - Category (submenu or radio list)
  - (Optional) “Show counts” toggle inside the menu

**Alternative (also mac-like):** Replace the segmented control with a **Finder-style sidebar list** (one column list with icons + counts as subtle badges).

**Where:** `src/app.py` (Row 2 filter container + `_update_filter_counts`)

## 4) Move “Dark mode” + “UI Scale” out of the main sidebar

These are important settings, but they don’t need to compete with the primary workflow every time.

**Change:** Put them in **Preferences…** (opened via the sidebar gear/overflow).
- Theme: Light / Dark / System (if possible)
- UI Scale: Auto + presets

**Where:** `src/app.py` (Row 4/5 area)

## 5) Reduce per-row visual noise in the prompt list

### Pin star visibility
**Change:** Show the star only when:
- the item is pinned **or**
- the row is hovered/selected

This matches common macOS patterns (Mail/Notes often hide row actions until hover).

**Where:** `src/components/prompt_list.py` (`PromptListItem.pin_btn`, hover handlers)

### Consider a “compact list” mode
**Change:** In compact mode, show either:
- just name + faint metadata **or**
- a single preview line, but hide some metadata

**Where:** `src/components/prompt_list.py` (`_build_metadata`, `_build_snippet`, row layout)

## 6) Consolidate Copy actions

**Change:** Replace “Copy” + “Copy as” with a single `Copy ▾` control.
- Primary click: Copy
- Dropdown: Copy as Markdown / JSON / etc.

**Where:** `src/components/prompt_editor.py` (header)

## 7) Hide “Reveal” unless it’s needed

Right now “Reveal” is always present, even when Sensitive is off (it becomes disabled, but still adds noise).

**Change:**
- If Sensitive is OFF: hide Reveal entirely.
- If Sensitive is ON: show a single lock/reveal control (button or icon).

**Where:** `src/components/prompt_editor.py` (`sensitive_toggle`, `reveal_btn`, `_apply_sensitive_view`)

---

# Smaller but noticeable “macOS/Linux polish” tweaks

## Typography + labels
- Reduce “shouty” UI: replace ALL‑CAPS section labels (NAME/CATEGORY/TAGS/…) with sentence case and/or lighter weight.
- Avoid hard-coding `Segoe UI` everywhere; prefer system defaults (or a platform-aware fallback list).

## Spacing + alignment
- Standardize an 8px rhythm (8/16/24) across sidebar + editor.
- Keep only one dominant accent element per area (e.g., New in sidebar, Save in editor).

## Visual hierarchy
- Counts: if kept, render as subtle badges (small, muted) rather than injecting text into every filter label.
- Destructive actions: keep red, but avoid placing them beside primary actions unless necessary.

---

# “Minimal UI” target (what the first glance should show)

## Sidebar (ideal)
- New (+)
- Search (with an inline clear “×” that appears only when typing)
- List of prompts
- One More/Settings button (⋯/⚙)

## Editor (ideal)
- Title
- One Copy control (Copy ▾)
- One More menu (⋯) for secondary actions
- One primary action (Save) **only when there are unsaved changes** (or switch to auto-save)

---

## Priority order (what to do first)

1. **Overflow menus first:** Replace the sidebar footer button row (Import/Export/Library…) with **one** “More/Settings” control, and move secondary actions into it (including Select mode). Then do the same in the editor footer (move Format/Version/History/Delete into “More”).  
2. **Simplify filtering:** Replace the 6 filter buttons (Pinned/All/Persona/System/Template/Other) with a single Filter control (dropdown/sidebar list) and move counts into subtle badges (or make counts optional).  
3. **Collapse “Test in AI”:** Replace Gemini/GPT/Grok with a single “Test in…” control (remember last provider).  
4. **Consolidate Copy actions:** Replace Copy + Copy as with a single Copy dropdown.  
5. **Hide conditional controls:** Hide Reveal unless Sensitive is ON (and consider an icon-style lock/reveal control).  
6. **Trim list row chrome:** Hide the pin star until hover/selected (unless pinned), and optionally add a compact density mode.  
7. **Final polish pass:** Typography (reduce ALL-CAPS), spacing rhythm, and visual hierarchy tweaks.
