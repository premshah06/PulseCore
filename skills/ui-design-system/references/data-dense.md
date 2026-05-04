# Data-Dense

For: dashboards, admin panels, analytics, monitoring tools, ops consoles, log viewers, status pages, CRUD interfaces. The aesthetic is **functional, premium, information-rich** — Linear, Vercel dashboard, Datadog, Stripe Dashboard, Figma admin. Density is a feature, not a flaw.

## When this aesthetic fits

- Tool people log into to do work
- Tables, charts, metrics as primary content
- Filters, sorts, search, date ranges
- Time-series data or real-time updates
- Status indicators (operational / degraded / down)

## When it doesn't

- Marketing pages selling the dashboard → use conversion-focused for those
- Documentation about the dashboard → use documentation aesthetic
- Personal portfolios that happen to show data → cinematic-editorial

## The core principle

Information density is high but not chaotic. The grid is tight, line-heights are compact, type sizes are small but legible. Color is used sparingly and **always semantically** — never decoratively.

## Palette (dark by default, with light variant)

```css
:root {
  /* Surfaces — three-layer hierarchy */
  --bg: #08090b;            /* page */
  --bg-surface: #0e0f12;    /* card / panel */
  --bg-elevated: #16181d;   /* nested / hover state */
  --bg-overlay: #1c1f26;    /* dropdowns, modals */

  /* Text — four-step hierarchy */
  --text-primary: #e8e9ed;
  --text-secondary: rgba(232, 233, 237, 0.72);
  --text-tertiary: rgba(232, 233, 237, 0.50);
  --text-disabled: rgba(232, 233, 237, 0.30);

  /* Borders */
  --border: rgba(255, 255, 255, 0.06);
  --border-strong: rgba(255, 255, 255, 0.12);
  --border-focus: rgba(105, 162, 255, 0.4);

  /* Brand — single accent, used sparingly */
  --brand: #69a2ff;
  --brand-bg: rgba(105, 162, 255, 0.08);
  --brand-hover: #82b4ff;

  /* Semantic — these are the workhorse colors */
  --success: #3fb950;
  --success-bg: rgba(63, 185, 80, 0.10);
  --warning: #d29922;
  --warning-bg: rgba(210, 153, 34, 0.10);
  --danger: #f85149;
  --danger-bg: rgba(248, 81, 73, 0.10);
  --info: #58a6ff;
  --info-bg: rgba(88, 166, 255, 0.10);

  /* Data viz — qualitative palette for chart series */
  --chart-1: #69a2ff;
  --chart-2: #b48cff;
  --chart-3: #3fb950;
  --chart-4: #f85149;
  --chart-5: #d29922;
  --chart-6: #58d4d4;
  --chart-7: #ff7a9c;
  --chart-8: #8be8a8;
}

/* Light variant */
[data-theme="light"] {
  --bg: #fafbfc;
  --bg-surface: #ffffff;
  --bg-elevated: #f4f5f7;
  --bg-overlay: #ffffff;
  --text-primary: #1a1d23;
  --text-secondary: rgba(26, 29, 35, 0.74);
  --text-tertiary: rgba(26, 29, 35, 0.55);
  --text-disabled: rgba(26, 29, 35, 0.32);
  --border: rgba(0, 0, 0, 0.08);
  --border-strong: rgba(0, 0, 0, 0.14);
}
```

## Typography

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

Inter is the workhorse — designed for screens at small sizes. JetBrains Mono for any numeric or code content.

```css
:root {
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
  font-feature-settings: 'cv11', 'ss01', 'ss03';  /* Inter humanist alternates */
}

/* Tight, dense type scale */
.text-xs   { font-size: 11px; line-height: 16px; }
.text-sm   { font-size: 12px; line-height: 16px; }
.text-base { font-size: 13px; line-height: 18px; }  /* default body */
.text-md   { font-size: 14px; line-height: 20px; }
.text-lg   { font-size: 16px; line-height: 22px; }
.text-xl   { font-size: 20px; line-height: 26px; font-weight: 600; }
.text-2xl  { font-size: 24px; line-height: 30px; font-weight: 600; }
.text-3xl  { font-size: 32px; line-height: 38px; font-weight: 600; letter-spacing: -0.01em; }

/* Numbers always use tabular figures so columns align */
.tabular { font-variant-numeric: tabular-nums; }

/* Labels are uppercase mono small */
.label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-tertiary); }
```

Default body is 13px. That's small on purpose — it lets dashboards breathe at high information density without horizontal scrolling.

## Spacing — tighter than other aesthetics

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-7: 32px;
  --space-8: 48px;
}
```

Cards have 16–24px padding. Section gaps are 24–32px. Page padding is 24px. No `--section-py` of 200px here.

## Layout shell

Standard data-dense layout: fixed top bar + fixed left sidebar + main content area.

```html
<div class="app">
  <header class="topbar">
    <div class="topbar-left">
      <div class="logo"><!-- product name from source --></div>
      <nav class="breadcrumbs"><!-- from source --></nav>
    </div>
    <div class="topbar-right">
      <input class="search" placeholder="Search..." />
      <div class="user-menu"><!-- avatar + name from source --></div>
    </div>
  </header>

  <aside class="sidebar">
    <nav>
      <!-- one item per nav entry from source -->
      <a class="nav-item active">
        <svg class="nav-icon">...</svg>
        <span><!-- nav label from source --></span>
      </a>
    </nav>
  </aside>

  <main class="main">
    <!-- page content from source -->
  </main>
</div>
```

```css
.app { display: grid; grid-template-areas: 'topbar topbar' 'sidebar main'; grid-template-columns: 240px 1fr; grid-template-rows: 48px 1fr; min-height: 100vh; }
.topbar { grid-area: topbar; display: flex; justify-content: space-between; align-items: center; padding: 0 16px; border-bottom: 1px solid var(--border); background: var(--bg-surface); }
.sidebar { grid-area: sidebar; padding: 12px; border-right: 1px solid var(--border); background: var(--bg-surface); overflow-y: auto; }
.main { grid-area: main; padding: 24px; overflow-y: auto; background: var(--bg); }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 6px 10px; border-radius: 6px; color: var(--text-secondary); font-size: 13px; }
.nav-item:hover { background: var(--bg-elevated); color: var(--text-primary); }
.nav-item.active { background: var(--brand-bg); color: var(--brand); }
```

## Cards

```css
.card { background: var(--bg-surface); border: 1px solid var(--border); border-radius: 8px; }
.card-header { padding: 12px 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.card-body { padding: 16px; }
```

8px border-radius — not 16px (too soft), not 4px (too utilitarian).

## Tables

The single most important component. Get this right and the whole thing feels professional.

```css
.table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }
.table th { text-align: left; font-weight: 500; color: var(--text-tertiary); font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; padding: 8px 12px; border-bottom: 1px solid var(--border); background: var(--bg-surface); position: sticky; top: 0; }
.table td { padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text-secondary); }
.table tbody tr:hover { background: var(--bg-elevated); }
.table tbody tr:hover td { color: var(--text-primary); }
.table .num { font-variant-numeric: tabular-nums; text-align: right; }
.table .mono-cell { font-family: var(--font-mono); font-size: 12px; }
```

Row hover changes both background AND text color. Numbers are always tabular and right-aligned.

## Status indicators

```css
.status { display: inline-flex; align-items: center; gap: 6px; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; font-family: var(--font-mono); }
.status::before { content: ''; width: 6px; height: 6px; border-radius: 50%; }
.status-success { background: var(--success-bg); color: var(--success); }
.status-success::before { background: var(--success); }
.status-warning { background: var(--warning-bg); color: var(--warning); }
.status-warning::before { background: var(--warning); }
.status-danger { background: var(--danger-bg); color: var(--danger); }
.status-danger::before { background: var(--danger); }
```

For live indicators, add a pulse on the dot:

```css
.status-live::before { animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; box-shadow: 0 0 0 3px currentColor; } }
```

## Metric cards (KPI tiles)

```html
<div class="metric">
  <div class="metric-label label"><!-- label from source --></div>
  <div class="metric-value tabular"><!-- value from source --></div>
  <div class="metric-delta metric-delta-up">
    <svg><!-- arrow up --></svg>
    <span><!-- delta from source --></span>
  </div>
</div>
```

```css
.metric { padding: 16px; background: var(--bg-surface); border: 1px solid var(--border); border-radius: 8px; }
.metric-value { font-size: 28px; font-weight: 600; color: var(--text-primary); margin: 4px 0; font-variant-numeric: tabular-nums; }
.metric-delta { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; font-family: var(--font-mono); }
.metric-delta-up { color: var(--success); }
.metric-delta-down { color: var(--danger); }
```

## Charts

Use **Chart.js** or **Recharts** — both render at this density well. Configure with these conventions:

- Grid lines: `var(--border)`, dashed `[2, 4]`, very subtle
- Axis labels: `var(--text-tertiary)`, 11px
- Tooltip: dark background `var(--bg-overlay)`, 1px border `var(--border-strong)`
- Series colors: cycle through `--chart-1` through `--chart-8`
- No 3D, no gradient fills (a single subtle gradient under a line chart is fine, no rainbow)
- No legend if there's only one series

Example Chart.js config snippet:

```js
const baseChartOpts = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { backgroundColor: getCSSVar('--bg-overlay'), borderColor: getCSSVar('--border-strong'), borderWidth: 1, titleColor: getCSSVar('--text-primary'), bodyColor: getCSSVar('--text-secondary') } },
  scales: { x: { grid: { color: getCSSVar('--border'), borderDash: [2, 4] }, ticks: { color: getCSSVar('--text-tertiary'), font: { size: 11 } } }, y: { grid: { color: getCSSVar('--border'), borderDash: [2, 4] }, ticks: { color: getCSSVar('--text-tertiary'), font: { size: 11 } } } },
};
```

## Filters and controls

```css
.input, .select, .button { height: 28px; padding: 0 10px; border-radius: 6px; border: 1px solid var(--border-strong); background: var(--bg-surface); color: var(--text-primary); font-size: 12px; font-family: inherit; }
.input:focus, .select:focus { outline: none; border-color: var(--border-focus); box-shadow: 0 0 0 3px rgba(105, 162, 255, 0.12); }
.button { cursor: pointer; transition: background 0.1s; }
.button:hover { background: var(--bg-elevated); }
.button-primary { background: var(--brand); border-color: var(--brand); color: #0a0b0d; }
.button-primary:hover { background: var(--brand-hover); }
```

28px control height — small enough for dense toolbars, large enough to hit. Standard.

## Empty states

Empty tables, empty search results, empty filters — these matter in dashboards. Pattern:

```html
<div class="empty">
  <svg class="empty-icon">...</svg>
  <div class="empty-title"><!-- from source if present, else "No results" --></div>
  <div class="empty-hint"><!-- from source if present, else "Adjust filters and try again" --></div>
</div>
```

```css
.empty { padding: 48px 24px; text-align: center; color: var(--text-tertiary); }
.empty-icon { width: 32px; height: 32px; margin: 0 auto 12px; opacity: 0.5; }
.empty-title { font-size: 14px; color: var(--text-secondary); margin-bottom: 4px; }
.empty-hint { font-size: 12px; }
```

## Motion

Minimal. The dashboard's job is to surface information instantly, not perform.

- Loading skeletons (animated background gradient on placeholder rectangles) instead of spinners for content that's coming
- Subtle fades (`opacity 150ms`) on hover/focus
- Numbers in metric cards animate when they change (count-up over 600ms)
- No scroll-triggered reveals
- No smooth-scroll libraries

```css
.skeleton { background: linear-gradient(90deg, var(--bg-elevated) 0%, var(--bg-surface) 50%, var(--bg-elevated) 100%); background-size: 200% 100%; animation: shimmer 1.4s infinite; border-radius: 4px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
```

## Anti-patterns (do not do these)

- Marketing-style hero with a giant headline and "Try the Dashboard" CTA — that belongs on the marketing site, not the product
- Soft pastel palette with rounded-everything — Notion-template aesthetic, fine for some products but reads as toy
- Center-aligned large type — dashboards left-align everything
- Dark mode with pure black `#000` background — too harsh; use `#08090b`
- Decorative icons inside every metric card — adds noise
- Charts with rainbow gradients or 3D effects
- Animating numbers continuously (only when they change)
- Big rounded corners (>12px) on cards — feels casual
- Custom cursor — productivity tools use the native cursor
- Background canvas particles — never in a dashboard

## Light mode is mandatory here

Unlike cinematic-editorial which is dark-only by intent, data-dense MUST support both. Many users in long sessions prefer light. Implement a theme toggle that swaps `data-theme` on `<html>` and persists to localStorage (or sessionStorage if the user explicitly disallows persistence).

## Accessibility specifics

- Tables get `<th scope="col">` and `<caption>` (visually hidden if not visible)
- Status indicators have aria-label so screen readers get "operational" not just a green dot
- Charts have a textual fallback (a hidden `<table>` of the underlying data)
- All form controls have visible labels (not just placeholders)
- Color is never the only signal — use icons + color for status

## Mobile

Dashboards on mobile are inherently compromised but not optional. Pattern:

- Sidebar collapses to a drawer (toggle button in topbar)
- Multi-column metric grids stack to single column
- Tables get horizontal scroll inside their container, with a sticky first column for row identifiers
- Filter toolbars collapse into a "Filters" button that opens a sheet