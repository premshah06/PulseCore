# Product Launch

For: AI tool landing pages, app launches, single-page product reveals, "we built this — try it" pages. The aesthetic must signal **technically credible AND not generic**. This is the category that suffers most from AI-coded sameness, so anti-patterns matter as much as patterns.

## When this aesthetic fits

- A single product is being introduced
- Demo or interactive preview is central to the page
- One primary CTA repeated throughout ("Try it", "Get early access", "Start building")
- Single-page-ish (3–7 sections), maybe 1–2 supporting pages
- The product is software/AI/developer-focused

## When it doesn't

- Selling a SaaS subscription with pricing tiers → conversion-focused
- The product is non-technical (a course, a book, a service) → conversion-focused
- The product is launched and the page is now a docs/marketing site → split appropriately

## The generic-AI tell — what to avoid

Every AI-coded landing page in 2024–2026 looks the same. Here is the visual checklist of what NOT to do:

- Purple → blue → pink gradient hero background
- "Glassmorphism" cards (backdrop-filter blur with white border-rgba)
- Floating gradient blobs/orbs in the corners
- Stars-in-a-dark-sky background with parallax
- The exact phrase "Powered by AI" in an eyebrow
- A 3D rotating sphere/torus made of dots
- Animated terminal typing out a tagline
- Headline in a generic geometric sans like Space Grotesk with `letter-spacing: -0.05em`
- Pricing cards with the same "Free / Pro / Enterprise" structure verbatim
- "Built with [logo soup of OpenAI / Anthropic / Vercel]" trust strip
- Vercel-style grid lines fading into a dark background
- The stock screenshot of a code editor with rainbow syntax highlighting
- Auto-cycling testimonials from people whose photos look like Unsplash
- Spline/Three.js scene that's a colorful abstract shape rotating slowly
- "Try it now" button with `bg-gradient-to-r from-indigo-500 to-purple-500`

If your draft includes any three of these, restart.

## What to do instead — three viable directions

Pick ONE based on the product's voice:

### Direction A — Technical / Editorial

Dark, restrained, code-forward. Looks like a technical engineer would build it for themselves. Closest to **cinematic-editorial** but tighter, less story-driven.

### Direction B — Bold / Confident

Light or off-white, oversized type, single saturated accent (not a gradient), big confident statements. Closer to a manifesto than a feature list.

### Direction C — Functional / Demo-First

The demo IS the hero. Minimal copy. The product proves itself by working in the page. Often used by developer tools where the value is immediately demonstrable.

## Direction A — Technical / Editorial

```css
:root {
  --bg: #0a0a0a;
  --bg-elevated: #141414;
  --bg-card: #1c1c1c;

  --text-primary: #fafafa;
  --text-secondary: rgba(250, 250, 250, 0.65);
  --text-tertiary: rgba(250, 250, 250, 0.45);

  --border: rgba(255, 255, 255, 0.08);
  --border-strong: rgba(255, 255, 255, 0.18);

  /* Single accent — pick from product brand if exists, else default */
  --accent: #00ff88;        /* electric green is a non-generic choice */
  /* alternatives that aren't generic: --accent: #ff5e3a (red-orange), #ffd23f (yellow), #00d4ff (cyan) */
}
```

Typography: serif display + sans body + mono accents.

```html
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

```css
:root {
  --font-display: 'Instrument Serif', Georgia, serif;
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

.h1 { font-family: var(--font-display); font-size: clamp(56px, 9vw, 128px); line-height: 0.95; letter-spacing: -0.02em; font-weight: 400; }
.h1 em { font-style: italic; color: var(--accent); }
```

Hero pattern:

```html
<section class="hero">
  <div class="mono-eyebrow">// <!-- product type from source --></div>
  <h1 class="h1"><!-- source headline, with one italic word --></h1>
  <p class="hero-sub"><!-- source subheadline, verbatim --></p>
  <div class="hero-actions">
    <a class="btn-primary" href="..."><!-- primary CTA from source --></a>
    <a class="btn-secondary" href="..."><!-- secondary CTA from source --></a>
  </div>
</section>
```

```css
.hero { padding: 120px 24px; max-width: 1200px; margin: 0 auto; }
.mono-eyebrow { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--accent); margin-bottom: 24px; }
.hero-sub { font-size: 20px; line-height: 1.5; color: var(--text-secondary); max-width: 640px; margin: 32px 0 40px; }
.hero-actions { display: flex; gap: 12px; }
.btn-primary { padding: 14px 28px; background: var(--accent); color: var(--bg); font-weight: 500; border-radius: 8px; font-family: var(--font-mono); font-size: 13px; letter-spacing: 0.06em; text-transform: uppercase; text-decoration: none; }
.btn-secondary { padding: 14px 28px; background: transparent; color: var(--text-primary); border: 1px solid var(--border-strong); border-radius: 8px; font-family: var(--font-mono); font-size: 13px; letter-spacing: 0.06em; text-transform: uppercase; text-decoration: none; }
.btn-secondary:hover { border-color: var(--accent); color: var(--accent); }
```

## Direction B — Bold / Confident

```css
:root {
  --bg: #f4f1ea;          /* warm off-white */
  --bg-card: #ffffff;
  --text-primary: #0a0a0a;
  --text-secondary: rgba(10, 10, 10, 0.7);
  --border: rgba(0, 0, 0, 0.1);
  --accent: #ff4500;      /* loud orange, no apology */
}
```

```html
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700;800&display=swap" rel="stylesheet">
```

```css
:root { --font-sans: 'Inter Tight', sans-serif; }
.h1 { font-family: var(--font-sans); font-size: clamp(64px, 11vw, 180px); line-height: 0.92; letter-spacing: -0.04em; font-weight: 800; }
```

The headline is the hero. No subheadline necessary unless the source has one. One CTA.

```css
.hero-bold { padding: 80px 24px 40px; max-width: 1400px; margin: 0 auto; }
.h1 { color: var(--text-primary); }
.h1-accent-line { color: var(--accent); }  /* one line of the headline pops in accent */
```

## Direction C — Functional / Demo-First

The hero IS the product running. Minimal text above and below.

```html
<section class="demo-hero">
  <div class="demo-context">
    <h1 class="demo-title"><!-- short product name from source --></h1>
    <p class="demo-tagline"><!-- one line from source --></p>
  </div>
  <div class="demo-stage">
    <!-- live interactive demo of the product, OR a video, OR an animated mockup -->
  </div>
  <div class="demo-cta">
    <a class="btn-primary" href="..."><!-- "Try it free" or whatever source uses --></a>
  </div>
</section>
```

The demo stage takes 60–70% of the viewport. Type is small (24–48px headline, not 128px). Reads like a tool, not a marketing page.

## Across all three directions

### What ALL the directions share

- **One** accent color, not a gradient
- Serif italic only on the verb in headlines (in directions A and B; C uses sans)
- No glassmorphism, no floating blobs, no gradient backgrounds
- The product is shown working, not described
- CTAs use mono uppercase OR sans medium-weight — never gradient text
- Footer is small, functional, not a marketing dump

### Demo / preview component

Every product launch needs ONE compelling demo on the page. Build it as one of:

1. **Live interactive demo** — best if technically feasible. The user can actually use the product on the page.
2. **Animated mockup** — looped video or CSS-animated UI showing the product working. Use real screenshots if the source has them, or recreate the UI.
3. **Code → output** — common for developer tools. Shows code on the left, the result on the right.

Whichever path, frame the demo in a chrome that hints at the product's medium:

```html
<div class="demo-frame">
  <div class="demo-chrome">
    <span class="demo-dot"></span>
    <span class="demo-dot"></span>
    <span class="demo-dot"></span>
  </div>
  <div class="demo-content">
    <!-- the demo -->
  </div>
</div>
```

```css
.demo-frame { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: 0 32px 64px -16px rgba(0,0,0,0.4); }
.demo-chrome { display: flex; gap: 6px; padding: 12px 16px; border-bottom: 1px solid var(--border); }
.demo-dot { width: 12px; height: 12px; border-radius: 50%; background: var(--border-strong); }
```

### Feature blocks

Three or four. Each block has: a small icon OR a number, a short title, two-to-three lines of body, optional code snippet or visual. **No screenshots of the product alongside features** — features describe capability, not show UI. Show UI in the demo section.

```html
<section class="features">
  <div class="features-header">
    <div class="mono-eyebrow">// CAPABILITIES</div>
    <h2><!-- source headline --></h2>
  </div>
  <div class="features-grid">
    <article class="feature">
      <div class="mono-label">01</div>
      <h3><!-- feature title from source --></h3>
      <p><!-- feature description from source --></p>
    </article>
    <!-- repeat -->
  </div>
</section>
```

```css
.features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; max-width: 1200px; }
.feature { padding: 32px 0; border-top: 1px solid var(--border); }
.feature h3 { font-size: 22px; margin: 12px 0; }
@media (max-width: 1024px) { .features-grid { grid-template-columns: 1fr; } }
```

### "How it works"

If the source has a how-it-works section, present it as numbered steps with code or visual per step. Not a flowchart. Not a 3D animated diagram.

```html
<section class="how">
  <div class="mono-eyebrow">// HOW IT WORKS</div>
  <h2><!-- source headline --></h2>
  <ol class="how-steps">
    <li class="how-step">
      <span class="step-num">01</span>
      <div class="step-body">
        <h3><!-- step title from source --></h3>
        <p><!-- step description from source --></p>
        <pre class="step-code"><!-- code from source if applicable --></pre>
      </div>
    </li>
    <!-- repeat -->
  </ol>
</section>
```

### Use cases / examples

If the source has use cases or example outputs, show them as a **gallery of real outputs** (not stock-photo styled cards). Click on one to expand.

### Final CTA section

```html
<section class="final-cta">
  <h2 class="h1"><!-- source's final invitation, often a question --></h2>
  <a class="btn-primary btn-lg"><!-- primary CTA from source --></a>
  <div class="final-microcopy"><!-- e.g., "Free during beta" if source has it --></div>
</section>
```

## Motion

Restrained but present. The page should feel responsive, not animated.

- Hero text fades up once on load (~600ms, ease-out)
- Demo frame has a subtle entrance (scale from 0.98 to 1 over 800ms)
- Hover on CTAs: 150ms color/transform transition
- No scroll-triggered parallax
- No mouse-followed gradients
- No background shapes drifting
- The demo itself can animate freely — it's the demo's job

## Layout shell

Single page, scroll-driven. Top nav minimal:

```html
<header class="topnav">
  <a href="/" class="brand"><!-- product name from source --></a>
  <nav><!-- links from source if any: Docs / Pricing / Blog --></nav>
  <a class="btn-primary" href="..."><!-- primary CTA --></a>
</header>
```

```css
.topnav { display: flex; align-items: center; justify-content: space-between; padding: 16px 32px; max-width: 1400px; margin: 0 auto; position: sticky; top: 0; background: color-mix(in srgb, var(--bg) 85%, transparent); backdrop-filter: blur(12px); z-index: 50; }
```

(Backdrop-filter is OK here even though glassmorphism cards are banned — a sticky nav is a different use case and is not the visual identity of the page.)

## Footer

Functional, small. Don't bury the user in links.

```html
<footer class="footer">
  <div class="footer-brand"><!-- product name + one-line tagline from source --></div>
  <div class="footer-links">
    <!-- links from source -->
  </div>
  <div class="footer-meta">
    <span><!-- copyright from source --></span>
    <a href="..."><!-- privacy / terms from source --></a>
  </div>
</footer>
```

## Anti-patterns (the second list — even more specific)

- Headline followed by three feature cards followed by pricing followed by FAQ followed by CTA — that's the structural template every AI site uses; if the source content forces you into it, vary the visual rhythm so it doesn't read that way
- Calling the product "AI-powered" or "Intelligent" anywhere in copy you generate (chrome) — let the product speak
- Animated gradient on the headline text
- Spline embeds with no purpose
- Customer logo strip when the source has no real customers
- "Coming soon" countdowns
- Email capture as the entire hero CTA
- Discord/Slack join buttons in primary CTA position
- "Built by ex-OpenAI / ex-Google / Stanford alums" credibility plates that the source didn't actually write
- Particle effects of any kind
- Custom cursor (this isn't a portfolio)

## Mobile

- Hero reduces to ~60vh, no fixed positioning
- Demo frame becomes full-width, possibly with horizontal scroll for wide demos
- Feature grid stacks
- Sticky CTA at bottom is acceptable
- Top nav collapses to logo + primary CTA only (no hamburger needed for 3 links)

## Accessibility

- The demo must have a textual fallback for screen readers (an ARIA label describing what's shown, or a hidden transcript for video demos)
- Mono uppercase CTAs need adequate contrast — test at 4.5:1 minimum
- Auto-playing demo videos must be muted and pausable
- Reduced motion: skip the entrance fades, render demo as a static screenshot