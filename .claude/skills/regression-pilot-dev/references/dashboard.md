# Dashboard reference

## Stack

- React 18 + Vite 5
- Recharts for charts
- JetBrains Mono (code/body) + Syne (display/headings)
- No Tailwind — all styling via inline styles using CSS variables

## Running

```bash
cd dashboard
npm install
npm run dev    # → http://localhost:5173
```

Works standalone with mock data (no backend needed). When API is up at `localhost:8000`, switches to live data automatically via the proxy in `vite.config.js`.

---

## Design system

Dark industrial monochrome theme. CSS variables defined in `src/index.css`:

| Variable | Value | Use |
|---|---|---|
| `--bg` | `#0a0a0a` | Page background |
| `--bg2` | `#111111` | Cards, panels |
| `--bg3` | `#1a1a1a` | Hover states |
| `--border` | `#2a2a2a` | Default borders |
| `--text` | `#e8e8e8` | Primary text |
| `--muted` | `#666666` | Secondary text, labels |
| `--healed` | `#00e5a0` | Success / healed status |
| `--bug` | `#ff4d4d` | Error / bug status |
| `--flaky` | `#f5a623` | Warning / flaky status |
| `--review` | `#7b8cff` | Info / needs review |
| `--font-display` | Syne | Headers, metric values |
| `--font-mono` | JetBrains Mono | Everything else |

All border styles: `1px solid var(--border)` (not 0.5px — this is a dark theme).
Border radius: `var(--radius)` = 4px (tight), `var(--radius2)` = 8px (cards).

---

## Components

### `StatusBadge` — `components/StatusBadge.jsx`
Props: `status: string`
Statuses: `healed | failed | quarantined | needs_review | pending | healing`
`healing` shows a pulsing dot animation.

### `ConfidenceBar` — `components/ConfidenceBar.jsx`
Props: `value: number | null` (0.0–1.0)
Shows a 60px bar + percentage. Color: green ≥75%, amber ≥50%, red <50%.
Renders `—` when value is null.

### `SelectorDiff` — `components/SelectorDiff.jsx`
Props: `before: string | null`, `after: string | null`
Renders a git-diff style block — red minus line for before, green plus line for after.
Returns null if both are null.

### `MetricCard` — `components/MetricCard.jsx`
Props: `label: string`, `value: string | number`, `unit?: string`, `accent?: string`
Surface card with muted label above, large Syne number below.

### `HealDrawer` — `components/HealDrawer.jsx`
Props: `heal: object | null`, `onClose: () => void`
Slide-in panel from right (480px wide). Shows full heal detail: all fields, selector diff, PR link.
Renders backdrop + panel. Closes on backdrop click or ESC button.

### `Charts` — `components/Charts.jsx`
Two exports:
- `ActivityChart` — AreaChart of healed/bugs per day, last 7 days
- `FrameworkChart` — Horizontal BarChart of Playwright vs Selenium counts

Both use Recharts. Canvas colors are hardcoded hex (CSS variables don't work in canvas).

---

## Data flow

```
useHeals hook (polls /api/heals every 15s)
  → App.jsx (filter + search state)
    → MetricCard grid (stats)
    → Charts (ActivityChart, FrameworkChart)
    → heal log table (filtered rows)
      → HealDrawer (on row click)
```

### `hooks/useHeals.js`
Polls `fetchHeals(100)` every 15s. Computes `stats` object:
```js
{
  healed, failed, quarantined, needs_review,  // counts
  timeSaved,       // sum of time_saved_minutes
  avgConfidence,   // average % of heals with confidence != null
}
```

### `lib/api.js`
`fetchHeals(limit)` and `fetchHealDetail(runId)` — try the real API, fall back to `MOCK_HEALS` on error.

`MOCK_HEALS` array is the source of truth for the mock data schema. Every field the UI uses must be present in mock heals.

---

## Heal object schema (from API / mock data)

```js
{
  run_id: string,           // 8-char ID
  status: string,           // healed | failed | quarantined | needs_review | pending
  failure_type: string,     // ui_change | real_bug | flaky | unknown
  test_name: string,
  test_file: string,
  framework: string,        // playwright | selenium
  confidence: number|null,  // 0.0–1.0, null for non-ui-change
  selector_before: string|null,
  selector_after: string|null,
  jira_ticket: string|null, // e.g. "QA-1042"
  pr_url: string|null,
  commit_sha: string|null,
  time_saved_minutes: number,
  retries: number,
  error: string|null,
  timestamp: string,        // ISO 8601
}
```

---

## Adding a new field to the dashboard

1. Add field to `agent/models.py` (Python dataclass)
2. Add field to `agent/server.py` `_heal_log` dict population in `_run_heal()`
3. Add field to `MOCK_HEALS` in `dashboard/src/lib/api.js`
4. Use the field in whichever component needs it
5. If it's a new status — add it to `StatusBadge.jsx` CONFIG object

## Adding a new component

1. Create `dashboard/src/components/NewComponent.jsx`
2. Use inline styles with CSS variables only — no hardcoded colors
3. Import and use in `App.jsx`
4. Export as default

---

## API proxy (vite.config.js)

All `/api/*` requests proxied to `VITE_API_URL` (default `http://localhost:8000`) with `/api` prefix stripped. So `fetch('/api/heals')` hits `http://localhost:8000/heals`.