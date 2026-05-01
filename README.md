# EVI Daily Task Log

A lightweight, browser-based daily task logger for datacenter operations at **EVI01**. Runs as a static GitHub Pages site with localStorage + JSON file backend.

## Features

- **Task Logging** — Record daily tasks with date, location (DH1-DH6 + custom), DC code, description, and additional info
- **Weekly View** — Browse tasks week-by-week with prev/next navigation and a "Today" button
- **Weekly Summary** — Modal with AI-generated summary, stats, location breakdown, and day-by-day detail
- **Search & Filter** — Real-time search across all records
- **Stats Dashboard** — At-a-glance counts for today, this week, and all time
- **Inline Edit/Delete** — Edit or delete any record directly from the table
- **Export/Import** — CSV export, JSON export/import for backup and transfer
- **Data Persistence** — Records stored in localStorage and seeded from `data.json` in the repo
- **CST Timezone** — All dates and timestamps locked to America/Chicago (CST/CDT)
- **Theme Switcher** — 6 themes: Classic Blue, Dark, Emerald, Sunset, Purple, Steel
- **Keyboard Shortcuts** — Ctrl+S (save), Ctrl+E (export CSV), Ctrl+F (search), Esc (close modals)
- **Print** — Print-friendly weekly summary modal

## Versioning Scheme

Format: **vX.Y.Z**

| Part | When to change | Example |
|------|---------------|---------|
| **X** (Major) | New feature release or stable version | v1.0.0 |
| **Y** (Minor) | Major bug fix or significant improvement | v0.2.0 |
| **Z** (Patch) | Minor bug fix or small tweak | v0.1.2 |

## Version History

### v1.3.1 (2026-05-01)
**Design:**
- Added a **mirror/shine sweep** effect to the date and day tabs in the date display — matches the existing button shine on hover (soft diagonal highlight glides across, plus a subtle lift)

### v1.3.0 (2026-04-30)
**New Features:**
- Added a **Rack** dropdown next to the Location dropdown on the SAVE ENTRY form (and a matching Rack dropdown in the EDIT modal)
- Rack options activate based on the selected location:
  - **DH1** → R001 – R320
  - **DH2** → R001 – R260
  - **DH3** → R001 – R200
  - **DH4** → R001 – R120
  - **DH5 / DH6** → "Coming in a later version" placeholder (disabled)
  - **L3-Optics Cage / Others** → no rack list (disabled)
- Rack value is persisted on the record and rendered inline with location (e.g. `DH1 / R042`) in the All Records table, Weekly View, Weekly Summary, and PDF export

### v1.2.0 (2026-04-29)
**Removed:**
- Removed the **TEMPLATES** feature (button, modal, save/load/delete handlers, and `evi_templates` localStorage key)
- Removed the **BULK ENTRY** feature (button, modal, location radios, and save handler)

### v1.1.1 (2026-04-29)
**New Features:**
- Added **"L3-Optics Cage"** as a built-in location option (SAVE ENTRY dropdown, plus EDIT / BULK ENTRY / RECURRING RULE forms)

### v1.1.0 (2026-04-28)
**Improvements:**
- Location field on the SAVE ENTRY form is now a **dropdown menu** with no default selection (placeholder: "-- Select location --")
- **SAVE ENTRY** button stays disabled until a location is chosen (and "Others" requires a non-empty custom value)
- Disabled-state styling added for `.btn` (reduced opacity, grayscale, `not-allowed` cursor)

### v1.0.3 (2026-04-27)
**Removed:**
- Removed the row-action **DUP** (duplicate) button and its handler from the All Records table

### v1.0.2 (2026-04-22)
**UI Polish:**
- Added a mirror/shine sweep effect to all buttons (main `.btn` and row-action `.act-btn`) — a soft diagonal highlight glides across on hover

### v1.0.1 (2026-04-21)
**Improvements:**
- All Records table now sorts by record ID descending — the most recently added log shows at the top regardless of its entry date

### v1.0.0 (2026-04-21)
**Stable Release:**
- Graduated from Beta to stable — Beta badge removed from the version label
- Unified **EXPORT** button — opens a format picker: CSV (spreadsheet), JSON (full backup incl. attachments), or PDF (printable report via browser Save-as-PDF dialog)
- Unified **IMPORT** button — picker lets the user choose JSON (full backup) or CSV (Date, Location, DC Code, Description, Add. Info columns)
- New CSV import supports any file with at minimum Date and Description columns; validates YYYY-MM-DD dates and skips malformed rows
- New PDF export opens a formatted report in a new window and triggers the print dialog
- Ctrl+E now opens the Export picker (was: direct CSV export)

### v0.6.3 (2026-04-21)
**New Features:**
- Weekly AI summary now lists actual task descriptions day-by-day, not just counts — e.g., "Monday (2026-04-20) — patch panel install; rack audit; cable cleanup"
- Up to 6 task names per day shown, with "+N more" overflow; long descriptions truncated at 120 chars
- Summary box now honors newlines (`white-space: pre-wrap`) so the day-by-day list is readable

### v0.6.2 (2026-04-21)
**Design:**
- New cohesive button palette (theme-independent): save/primary → emerald, blue → indigo, clear → amber, delete → rose, export → slate
- Row-action buttons (edit / delete / duplicate) updated to match the new palette

### v0.6.1 (2026-04-21)
**New Features:**
- TODAY button in the RECALL bar — one click filters the table to every record logged for today, switching to the All Records tab if needed

### v0.6.0 (2026-04-21)
**Design — complete UI remake (Design v2):**
- System font stack, tighter typography, soft radial background gradients in the active theme
- Glass-morphism sticky banner with gradient + subtle inset highlight, rounded-square settings button with blur
- Frosted-glass cards (Select Date, Task Details) with hairline borders, layered drop shadows, and an accent bar on each title
- Location pills redesigned as rounded chips with gradient fill when selected
- Buttons redone with subtle linear gradients, inner highlight/shadow, focus ring, and hover lift
- Stats dashboard: accent bar on left of each card, bolder display numerals, adaptive number color so dark themes stay readable
- Frosted sticky RECALL toolbar; record count as a pill badge with live dot
- Table: uppercase letter-spaced column headers, softer zebra rows, blue-tinted hover
- Modals: backdrop blur, larger radius, gradient header, rotate-on-hover close button
- AI Summary card, day sections, and summary stat cards refined with layered shadows and gradient accents
- Glass toast pill, pill-shaped version badge, custom thin scrollbars
- Gentle fade-in on load that respects `prefers-reduced-motion`

Implemented as a single `<style id="design-v2">` block appended after the base stylesheet — delete it to revert to the previous look without losing any functionality.

### v0.5.5 (2026-04-21)
**Design:**
- View tabs (All Records / Weekly View) now have a glossy mirror finish — layered gradients, inner highlight and shadow, and a shine sweep that animates across on hover

### v0.5.4 (2026-04-21)
**Bug Fixes:**
- Fixed: week number was off by one for Monday dates after DST spring-forward (e.g., 2026-04-20 was filed under Week 15 instead of Week 16) — `getWeekNumber()` used raw millisecond arithmetic that lost an hour across the DST boundary
- Now computes week from day-of-year using UTC arithmetic, which is DST-immune
- Added a one-time repair pass on load that recomputes `week_number` / `year` for every record from its `entry_date`, with a toast showing how many records were fixed

### v0.5.3 (2026-04-21)
**Bug Fixes:**
- Fixed: version badge in the top-left corner was hardcoded to v0.5.0; it now renders from `CURRENT_VERSION` so future bumps update automatically

### v0.5.2 (2026-04-21)
**New Features:**
- COPY ALL WEEKS button — copies a paragraph-per-week work log of every week with data to the clipboard
- Each week is labeled with its number, year, and date range, followed by the AI-generated narrative

### v0.5.1 (2026-04-21)
**New Features:**
- Past Weeks dropdown next to the Week # input — lists every prior week with data (e.g. "Week 14, 2026 (Apr 6 – Apr 12) — 15 tasks")
- Selecting a week auto-fills Week #/Year and opens the Weekly Summary for that week

### v0.5.0 (2026-04-17)
**New Features:**
- Attachments — insert images and PDFs into any task for more context
- Files stored in IndexedDB (separate from task records) so storage scales to many MBs
- Paperclip thumbnails in All Records table; click to open a full preview modal
- Drag-and-drop or click to add files; 10MB per-file limit; PDFs shown via embedded viewer
- Attachments follow edit/delete: removed with the task, editable from the edit modal

### v0.4.2 (2026-04-17)
**New Features:**
- Added two new themes: Rose (pink/magenta) and Teal (cyan/teal)
- Settings modal now shows 8 theme tiles

### v0.4.1 (2026-04-17)
**New Features:**
- Version badge is now clickable and opens a scrollable Version History modal
- Copy-to-clipboard icon on the weekly AI summary (top-right of the AI SUMMARY box)
- Version badge label changed from Alpha to Beta

### v0.4.0 (2026-04-17)
**New Features:**
- Task Templates — save the current form (location, DC code, description, add. info) as a named preset; one-click load to refill the form
- Bulk Entry — enter multiple descriptions (one per line) with a shared date, location, DC code and add. info; creates N records in one save
- Recurring Tasks — define daily or weekly (pick days) rules that auto-generate records from the start date onward each time the app loads; rules can be paused/resumed

### v0.3.0 (2026-04-15)
**New Features:**
- Auto-complete suggestions for description field based on previous entries
- Highlights matching text in orange, shows up to 8 suggestions
- Click a suggestion to fill the description field instantly

### v0.2.0 (2026-04-15)
**New Features:**
- Auto-detect Jira ticket numbers in descriptions and make them clickable links to CoreWeave Jira
- Supports standard keys (e.g., `DO-103333`) and bare numbers near "Jira"/"Ticket" keywords
- Links appear in All Records table, Weekly View, and Weekly Summary modal

### v0.1.2 (2026-04-15)
**Bug Fixes:**
- Fixed date input text invisible in dark mode (font color matched dark background)

### v0.1.1 (2026-04-15)
**Bug Fixes:**
- Fixed date picker showing wrong day (tomorrow instead of today) due to UTC/local timezone mismatch
- Fixed `toISOString()` returning UTC date instead of local date across all date operations
- Fixed stats dashboard showing incorrect "today" and "this week" counts

**New Features:**
- Added CST (America/Chicago) timezone enforcement for all dates and timestamps
- Added weekly view navigation with Prev/Next buttons and Today shortcut
- Added `data.json` in repo — records auto-load from git file into localStorage on page load
- Renamed "Current Week" tab to "Weekly View" with browse capability

### v0.1.0 (2026-04-13)
**Features:**
- Search and filter across all records
- Export to CSV
- Duplicate record to quickly create similar entries
- Stats dashboard (today, this week, all time)
- Keyboard shortcuts (Ctrl+S, Ctrl+E, Ctrl+F, Esc)
- Import/Export JSON for transferring records between devices

### v0.0.3 (2026-04-12)
**Features:**
- Current Week tab view with day-by-day card layout
- "Others" custom location option

### v0.0.2 (2026-04-11)
**Features:**
- 6-theme switcher (Classic Blue, Dark, Emerald, Sunset, Purple, Steel)
- Inline edit and delete records via modal
- Weekly summary modal with AI-generated insights
- Fixed record ID sequencing

### v0.0.1 (2026-04-10)
**Initial Release:**
- Daily task logging with date, location, DC code, description, and additional info
- GitHub Pages static site with localStorage backend
- Table view with all records
- Clipboard favicon for browser tab identity

## Setup

The app runs entirely in the browser. To use:

1. Visit the GitHub Pages URL, or
2. Open `docs/index.html` locally

Records are stored in the browser's localStorage. The `docs/data.json` file provides seed data that auto-merges on first load.

## Tech Stack

- Single-file HTML/CSS/JavaScript (no build step, no dependencies)
- localStorage for data persistence
- GitHub Pages for hosting
