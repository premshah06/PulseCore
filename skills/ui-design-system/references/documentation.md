# Documentation

For: API documentation, library guides, technical handbooks, knowledge bases, tutorials, changelogs. The job is to help readers find specific answers quickly. Density and scannability matter more than visual flair.

## When this aesthetic fits

- Reference material people search and scan
- Code examples throughout
- Sidebar table of contents structure
- Anchor links on every heading
- Cross-linked between pages

## When it doesn't

- Marketing pages about the product → conversion-focused
- The product itself (admin panels, etc.) → data-dense
- Personal blogs with discursive essays → cinematic-editorial

## Reference: Stripe docs, Linear docs, Vercel docs, MDN, Tailwind docs

These are the targets. They share specific traits: three-pane layout (sidebar / content / on-this-page), generous code examples with copy buttons, dense but scannable type, single-language identity (light or dark with a toggle), search prominent in the header.

## Layout — the three-pane standard

```html
<div class="docs">
  <header class="docs-header">
    <div class="docs-logo"><!-- product name from source --></div>
    <nav class="docs-nav-top">
      <!-- top nav links from source -->
    </nav>
    <div class="docs-search">
      <input placeholder="Search docs..." />
      <kbd>⌘K</kbd>
    </div>
  </header>

  <aside class="docs-sidebar">
    <!-- TOC from source, grouped by section -->
    <nav>
      <div class="sidebar-group">
        <div class="sidebar-group-title"><!-- section name from source --></div>
        <ul>
          <li><a href="#" class="sidebar-link active"><!-- page name --></a></li>
        </ul>
      </div>
    </nav>
  </aside>

  <main class="docs-content">
    <article class="prose">
      <!-- source content here, marked up properly with headings, code blocks, etc. -->
    </article>
    <nav class="docs-footer">
      <a class="docs-prev"><!-- prev page from source if exists --></a>
      <a class="docs-next"><!-- next page from source if exists --></a>
    </nav>
  </main>

  <aside class="docs-on-this-page">
    <div class="otp-title">On this page</div>
    <ul>
      <!-- generated from h2/h3 in current page -->
    </ul>
  </aside>
</div>
```

```css
.docs { display: grid; grid-template-areas: 'header header header' 'sidebar content otp'; grid-template-columns: 280px 1fr 240px; grid-template-rows: 56px 1fr; min-height: 100vh; }
.docs-header { grid-area: header; display: flex; align-items: center; padding: 0 24px; gap: 24px; border-bottom: 1px solid var(--border); background: var(--bg); position: sticky; top: 0; z-index: 10; }
.docs-sidebar { grid-area: sidebar; padding: 24px 16px; border-right: 1px solid var(--border); overflow-y: auto; max-height: calc(100vh - 56px); position: sticky; top: 56px; }
.docs-content { grid-area: content; padding: 48px 64px; max-width: 800px; min-width: 0; }
.docs-on-this-page { grid-area: otp; padding: 32px 24px; position: sticky; top: 56px; max-height: calc(100vh - 56px); overflow-y: auto; }

@media (max-width: 1280px) {
  .docs-on-this-page { display: none; }
  .docs { grid-template-areas: 'header header' 'sidebar content'; grid-template-columns: 280px 1fr; }
}
@media (max-width: 1024px) {
  .docs-sidebar { display: none; }  /* moves into a drawer triggered from header */
  .docs { grid-template-areas: 'header' 'content'; grid-template-columns: 1fr; }
  .docs-content { padding: 32px 24px; }
}
```

## Palette

Light mode default for docs. Most readers prefer light during long reading sessions, but a dark toggle is mandatory.

```css
:root {
  --bg: #ffffff;
  --bg-subtle: #fafafa;
  --bg-code: #f6f8fa;
  --bg-code-block: #0d1117;  /* dark code blocks even in light mode is a common pattern */

  --text-primary: #1a1d23;
  --text-secondary: #4a4f59;
  --text-tertiary: #6b7280;
  --text-link: #0066cc;

  --border: #e5e7eb;
  --border-strong: #d1d5db;

  --code-text: #e6edf3;  /* on dark code block */

  /* Syntax highlighting on dark code blocks */
  --syn-keyword: #ff7b72;
  --syn-string: #a5d6ff;
  --syn-function: #d2a8ff;
  --syn-comment: #8b949e;
  --syn-number: #79c0ff;
  --syn-property: #79c0ff;
}

[data-theme="dark"] {
  --bg: #0d1117;
  --bg-subtle: #161b22;
  --bg-code: #161b22;
  --text-primary: #e6edf3;
  --text-secondary: #c9d1d9;
  --text-tertiary: #8b949e;
  --text-link: #58a6ff;
  --border: #30363d;
  --border-strong: #484f58;
}
```

## Typography

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

```css
:root { --font-sans: 'Inter', system-ui, sans-serif; --font-mono: 'JetBrains Mono', Consolas, monospace; }

/* Prose — the long-form reading column */
.prose { color: var(--text-primary); font-size: 16px; line-height: 1.7; }
.prose h1 { font-size: 32px; font-weight: 700; line-height: 1.2; margin: 0 0 16px; letter-spacing: -0.01em; }
.prose h2 { font-size: 24px; font-weight: 600; line-height: 1.3; margin: 48px 0 16px; padding-top: 16px; }
.prose h3 { font-size: 18px; font-weight: 600; line-height: 1.4; margin: 32px 0 12px; }
.prose h4 { font-size: 16px; font-weight: 600; margin: 24px 0 8px; }
.prose p { margin: 0 0 16px; }
.prose ul, .prose ol { margin: 0 0 16px; padding-left: 24px; }
.prose li { margin-bottom: 6px; }
.prose a { color: var(--text-link); text-decoration: underline; text-underline-offset: 2px; text-decoration-thickness: 1px; }
.prose a:hover { text-decoration-thickness: 2px; }
.prose strong { font-weight: 600; color: var(--text-primary); }
.prose hr { border: none; border-top: 1px solid var(--border); margin: 48px 0; }
```

16px line-height-1.7 for body — the "reading" type scale. Documentation prose isn't tight-density like dashboards.

## Anchor links on headings

Every h2 and h3 gets a hover-revealed anchor link. This is table-stakes for docs.

```css
.prose h2, .prose h3 { position: relative; }
.prose h2 .anchor, .prose h3 .anchor { position: absolute; left: -28px; opacity: 0; color: var(--text-tertiary); text-decoration: none; transition: opacity 0.15s; font-weight: 400; }
.prose h2:hover .anchor, .prose h3:hover .anchor { opacity: 1; }
```

```js
document.querySelectorAll('.prose h2, .prose h3').forEach(h => {
  if (!h.id) h.id = h.textContent.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const a = document.createElement('a');
  a.href = `#${h.id}`;
  a.className = 'anchor';
  a.textContent = '#';
  a.setAttribute('aria-label', `Link to ${h.textContent}`);
  h.prepend(a);
});
```

## Code blocks — the most important component

Inline code:

```css
.prose code:not(pre code) { font-family: var(--font-mono); font-size: 0.875em; background: var(--bg-code); border: 1px solid var(--border); padding: 1px 6px; border-radius: 4px; color: var(--text-primary); }
```

Block code:

```html
<div class="code-block">
  <div class="code-header">
    <span class="code-lang">javascript</span>
    <button class="code-copy" aria-label="Copy code">Copy</button>
  </div>
  <pre><code><!-- code from source, syntax-highlighted --></code></pre>
</div>
```

```css
.code-block { background: var(--bg-code-block); border-radius: 8px; margin: 24px 0; overflow: hidden; border: 1px solid var(--border-strong); }
.code-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 16px; border-bottom: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); }
.code-lang { font-family: var(--font-mono); font-size: 12px; color: var(--text-tertiary); text-transform: lowercase; }
.code-copy { background: transparent; border: 1px solid rgba(255,255,255,0.1); color: var(--code-text); font-size: 12px; padding: 4px 10px; border-radius: 4px; cursor: pointer; transition: all 0.15s; }
.code-copy:hover { background: rgba(255,255,255,0.05); }
.code-copy.copied { color: var(--success); border-color: var(--success); }
.code-block pre { margin: 0; padding: 16px; overflow-x: auto; }
.code-block code { font-family: var(--font-mono); font-size: 13px; line-height: 1.55; color: var(--code-text); background: transparent; border: none; padding: 0; }
```

Copy button JS:

```js
document.querySelectorAll('.code-copy').forEach(btn => {
  btn.addEventListener('click', async () => {
    const code = btn.closest('.code-block').querySelector('code').textContent;
    await navigator.clipboard.writeText(code);
    btn.textContent = 'Copied';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
});
```

For syntax highlighting, use **Prism.js** or **Shiki**. Shiki produces better output (uses TextMate grammars) but is heavier. Prism is lighter and good enough for most docs:

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
```

## Code tabs (multi-language examples)

When the same example exists in multiple languages, use tabs:

```html
<div class="code-tabs">
  <div class="code-tab-headers">
    <button class="code-tab active" data-tab="js">JavaScript</button>
    <button class="code-tab" data-tab="py">Python</button>
    <button class="code-tab" data-tab="curl">cURL</button>
  </div>
  <div class="code-tab-content active" data-tab="js"><!-- JS code block --></div>
  <div class="code-tab-content" data-tab="py"><!-- Python code block --></div>
  <div class="code-tab-content" data-tab="curl"><!-- cURL code block --></div>
</div>
```

## Sidebar navigation

```css
.sidebar-group { margin-bottom: 24px; }
.sidebar-group-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-tertiary); margin-bottom: 8px; padding: 0 12px; }
.sidebar-group ul { list-style: none; padding: 0; }
.sidebar-link { display: block; padding: 6px 12px; font-size: 14px; color: var(--text-secondary); border-radius: 6px; text-decoration: none; border-left: 2px solid transparent; }
.sidebar-link:hover { background: var(--bg-subtle); color: var(--text-primary); }
.sidebar-link.active { background: var(--bg-subtle); color: var(--text-link); border-left-color: var(--text-link); font-weight: 500; }
```

## On-this-page (right rail)

Generated from the page's h2/h3 structure:

```js
const otp = document.querySelector('.docs-on-this-page ul');
document.querySelectorAll('.prose h2, .prose h3').forEach(h => {
  const li = document.createElement('li');
  li.className = `otp-${h.tagName.toLowerCase()}`;
  li.innerHTML = `<a href="#${h.id}">${h.textContent.replace(/^#\s*/, '')}</a>`;
  otp.appendChild(li);
});
```

```css
.docs-on-this-page .otp-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-tertiary); margin-bottom: 12px; }
.docs-on-this-page ul { list-style: none; padding: 0; border-left: 1px solid var(--border); }
.docs-on-this-page li { padding-left: 12px; margin-left: -1px; }
.docs-on-this-page .otp-h3 { padding-left: 24px; }
.docs-on-this-page a { display: block; padding: 4px 0; font-size: 13px; color: var(--text-tertiary); text-decoration: none; }
.docs-on-this-page a:hover, .docs-on-this-page a.active { color: var(--text-link); }
```

Highlight the section currently in viewport:

```js
const sections = document.querySelectorAll('.prose h2, .prose h3');
const otpLinks = document.querySelectorAll('.docs-on-this-page a');
new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      otpLinks.forEach(l => l.classList.toggle('active', l.getAttribute('href') === `#${e.target.id}`));
    }
  });
}, { rootMargin: '-10% 0px -80% 0px' }).observe(s);
```

## Callouts (info / warning / danger / tip)

```html
<aside class="callout callout-warning">
  <div class="callout-icon"><!-- icon --></div>
  <div class="callout-body">
    <strong>Heads up</strong>
    <p><!-- content from source --></p>
  </div>
</aside>
```

```css
.callout { display: flex; gap: 12px; padding: 16px; border-radius: 8px; margin: 24px 0; border: 1px solid; }
.callout-info { background: rgba(88, 166, 255, 0.08); border-color: rgba(88, 166, 255, 0.3); }
.callout-warning { background: rgba(210, 153, 34, 0.08); border-color: rgba(210, 153, 34, 0.3); }
.callout-danger { background: rgba(248, 81, 73, 0.08); border-color: rgba(248, 81, 73, 0.3); }
.callout-tip { background: rgba(63, 185, 80, 0.08); border-color: rgba(63, 185, 80, 0.3); }
.callout-icon { flex-shrink: 0; width: 20px; height: 20px; margin-top: 2px; }
.callout-body strong { display: block; margin-bottom: 4px; }
.callout-body p { margin: 0; font-size: 14px; line-height: 1.6; }
```

## Tables in docs

Different from data-dense tables — bigger type, more padding, less density. These are reference tables (params, options, return values), not data tables.

```css
.prose table { width: 100%; border-collapse: collapse; font-size: 14px; margin: 24px 0; }
.prose th { text-align: left; font-weight: 600; padding: 8px 12px; border-bottom: 2px solid var(--border-strong); color: var(--text-primary); }
.prose td { padding: 12px; border-bottom: 1px solid var(--border); color: var(--text-secondary); vertical-align: top; }
.prose td code { white-space: nowrap; }
```

## Search

For real search you need a service (Algolia DocSearch is industry standard, free for OSS docs). For static-site cases, a client-side fuzzy index works:

```js
// Fuse.js is a lightweight option
import Fuse from 'https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.mjs';
const fuse = new Fuse(searchIndex, { keys: ['title', 'content'], threshold: 0.3, includeMatches: true });
```

The search UI is a modal triggered by ⌘K / Ctrl+K with results showing in real-time.

## Prev / Next page navigation

At the bottom of each page:

```html
<nav class="docs-footer">
  <a href="..." class="docs-prev">
    <span class="docs-nav-label">Previous</span>
    <span class="docs-nav-title"><!-- prev page title --></span>
  </a>
  <a href="..." class="docs-next">
    <span class="docs-nav-label">Next</span>
    <span class="docs-nav-title"><!-- next page title --></span>
  </a>
</nav>
```

```css
.docs-footer { display: flex; justify-content: space-between; gap: 16px; margin-top: 64px; padding-top: 32px; border-top: 1px solid var(--border); }
.docs-footer a { flex: 1; padding: 16px; border: 1px solid var(--border); border-radius: 8px; text-decoration: none; display: flex; flex-direction: column; gap: 4px; transition: border-color 0.15s; }
.docs-footer a:hover { border-color: var(--text-link); }
.docs-next { text-align: right; }
.docs-nav-label { font-size: 12px; color: var(--text-tertiary); }
.docs-nav-title { font-size: 16px; font-weight: 500; color: var(--text-primary); }
```

## "Was this page helpful?"

```html
<div class="feedback">
  <span>Was this page helpful?</span>
  <button class="feedback-btn">Yes</button>
  <button class="feedback-btn">No</button>
</div>
```

```css
.feedback { display: flex; gap: 12px; align-items: center; padding: 16px; background: var(--bg-subtle); border-radius: 8px; margin-top: 32px; font-size: 14px; }
.feedback-btn { padding: 4px 12px; border: 1px solid var(--border-strong); background: var(--bg); border-radius: 6px; cursor: pointer; font-size: 13px; }
```

## Theme toggle

```js
const toggle = document.querySelector('.theme-toggle');
const stored = localStorage.getItem('theme');
const initial = stored || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
document.documentElement.dataset.theme = initial;
toggle.addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('theme', next);
});
```

## Motion

Almost none. Docs that animate distract from reading.

- Theme toggle: 200ms transition on background and text colors
- Sidebar links: instant background change on hover (no transition)
- Code copy button: brief "Copied" state with success color
- Smooth scroll to anchor only (`html { scroll-behavior: smooth; }`)
- No reveal-on-scroll
- No parallax, no fades, no transforms

## Anti-patterns

- Hero with marketing-style headline and CTA — docs don't have heroes
- Carousels of "popular articles" — let the sidebar do its job
- Large illustrations in the prose column — cramps reading width
- Floating chatbot widgets covering the bottom-right — moves around as user scrolls and steals attention
- Auto-popups asking for email subscriptions — kills trust
- Heavy serifs for body — Inter / system-ui at 16px is the standard
- Custom cursor or canvas backgrounds — completely wrong for docs
- Removing scrollbars from the sidebar — breaks orientation in long TOCs