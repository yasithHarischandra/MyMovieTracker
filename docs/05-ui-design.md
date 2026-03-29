# UI Design Specification

> Documents the approved UI design decisions and per-view specifications for the Personal Media Tracker.

---

## Design Philosophy

| Principle | Application |
|-----------|-------------|
| **Dark-mode first** | Background: `#0a0a0f` (near-black); Cards: `#13131a` |
| **Cinematic aesthetic** | Inspired by streaming platforms (rich contrast, poster-led layouts) |
| **Information density** | Stats readable at a glance; no wasted whitespace |
| **Non-intrusive optionals** | Ratings and notes are always optional; never blocking |
| **Responsive** | Single-column mobile → multi-column desktop |

### Typography
- **UI text:** Inter (Google Fonts)
- **Monospaced / stats:** JetBrains Mono
- **Icon set:** Phosphor Icons (`@phosphor-icons/vue`, `Ph` prefix naming convention)

### Colour Palette
| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0a0a0f` | Page background |
| Surface | `#13131a` | Card backgrounds |
| Border | `#1e1e2e` | Card borders |
| Accent | `#7c3aed` (purple) | Primary actions, progress bars |
| Accent alt | `#2563eb` (blue) | Secondary highlights |
| Success | `#22c55e` | Completed indicators |
| Text primary | `#f1f5f9` | Main content |
| Text muted | `#64748b` | Secondary labels |

---

## Views

### Dashboard

**Purpose:** At-a-glance overview of entire watch history.

**Layout sections:**
1. **Movie Stats panel** — Movies watched count + Total movie hours watched
2. **Series Stats panel** — Watched episodes, watched hours, in-progress count, remaining episodes, remaining hours, completion progress bar (% of all added series episodes watched)
3. **In-Progress** — Cards for each in-progress show, showing: poster, name, remaining episodes, remaining hours, mini progress bar
4. **Recent Activity** — Chronological feed showing movie/episode title, date watched, duration

**Specifications:**
- Stats panels use large, bold numbers with a label underneath
- Series stats include a horizontal progress bar showing `watched / total` percentage
- In-progress cards show remaining time prominently
- Recent activity entries include the runtime of the item watched

---

### Search

**Purpose:** Discover and add movies and TV shows.

**Layout:**
- Tab bar: **Movies** | **TV Shows**
- Search input with real-time debounced query (500ms)
- Grid of result cards with: poster, title, year, genre tags
- "Add to Library" button on each card
- "In Library" tag replaces button when already added

---

### History

**Purpose:** Browse full watch history with date filtering and period statistics.

**Layout:**
1. **Date range picker** — From / To date inputs
2. **Period stats** — For the selected range: movies watched, movie hours, episodes watched, series hours, total hours
3. **Activity feed** — Chronological list of all watch events (movie or episode) with delete option

**Specifications:**
- Period stats update reactively when date range changes
- Activity feed entries show media type (movie vs episode), title, date, duration

---

### In-Progress

**Purpose:** Shows currently-watching TV series.

**Layout:**
- Grid of show cards, each showing:
  - Poster image
  - Show name
  - Season progress (e.g., "S2 · Ep 5 of 10")
  - Remaining episodes count
  - Remaining hours
  - Mini horizontal progress bar

**Behaviour:**
- A show appears here once the first episode is watched
- A show disappears from this view once the last known episode is marked watched (on next page load)

---

### Movie Detail View

**Purpose:** View all metadata and watch history for a single movie.

**Layout:**
- Full-width poster backdrop (blurred) with foreground card
- Movie title, year, runtime, genres, overview
- Watch count badge
- Watch history list with timestamps, ratings, notes, delete buttons
- "Log Watch" button → modal with optional rating (1–5 stars) and note

---

### Show Detail View

**Purpose:** View all metadata, season list, and episode-level progress for a TV show.

**Layout:**
- Poster + metadata header (same style as movie detail)
- Global progress bar: `X of Y episodes watched` + remaining hours
- Season accordion list — each season expands to show episodes
- Per-episode row: episode number, name, runtime, watched checkbox, watched date

**Episode actions:**
- Click checkbox to mark/unmark a single episode
- Season header includes "Mark all as watched" button

---

### Settings

**Purpose:** Administrative functions.

**Sections:**
1. **TMDB Sync** — "Sync Now" button to manually trigger the background sync job
2. **Trakt.tv Import** — File upload for `watched_movies.json` and `watched_shows.json`; shows import result summary after processing

---

## Navigation

The persistent top navigation bar (`AppNav.vue`) contains:

| Route | Icon | Label |
|-------|------|-------|
| `/` | House | Dashboard |
| `/search` | MagnifyingGlass | Search |
| `/history` | ClockCounterClockwise | History |
| `/in-progress` | PlayCircle | In Progress |
| `/settings` | Gear | Settings |
| *(user menu)* | UserCircle | Logout |

---

## Responsive Breakpoints

| Breakpoint | Layout |
|------------|--------|
| Mobile (`< 768px`) | Single column; nav collapses to bottom bar or hamburger |
| Tablet (`768–1024px`) | 2-column cards, side-by-side stats panels |
| Desktop (`> 1024px`) | 3–4 column grids; full sidebar nav |
