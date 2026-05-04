# Cinematic Editorial

For: portfolios, personal sites, designer/developer/writer homes, scroll narratives. The aesthetic is editorial-meets-engineering — long-form magazine feature crossed with a developer's terminal. Every scroll inch deliberate.

## When this aesthetic fits

- Single person or small studio showing work
- Single-page or short scroll narrative (3–7 sections)
- Content is qualitative — story, process, projects with descriptions
- The user wants their site to feel "designed," not generic

## When it doesn't

- Sites with deep navigation or multi-page IA → use a different aesthetic for the inner pages
- Heavy data tables or dashboards → data-dense
- Anything optimizing for purchase or signup → conversion-focused

## Palette

```css
:root {
  /* Surfaces */
  --bg: #0a0b0d;
  --bg-elevated: #121317;
  --bg-card: #16181d;

  /* Text */
  --text-primary: #f4ede4;
  --text-secondary: rgba(244, 237, 228, 0.65);
  --text-caption: rgba(244, 237, 228, 0.42);

  /* Borders */
  --border: rgba(244, 237, 228, 0.08);
  --border-strong: rgba(244, 237, 228, 0.16);

  /* Per-section accent — shifts as user scrolls */
  --accent-1: #6cd4ff;  /* cyan */
  --accent-2: #b48cff;  /* violet */
  --accent-3: #ffb068;  /* amber */
  --accent-4: #ff7a7a;  /* coral */
  --accent-5: #8be8a8;  /* green */
  --accent-6: #6cd4ff;
  --current-accent: var(--accent-1);
}
```

Every accent-colored element references `var(--current-accent)`. A single GSAP timeline mutates `--current-accent` on `:root` as each section enters viewport. The whole page recolors smoothly.

```js
document.querySelectorAll('[data-section]').forEach((s) => {
  ScrollTrigger.create({
    trigger: s,
    start: 'top 60%',
    end: 'bottom 40%',
    onEnter: () => gsap.to('html', { '--current-accent': s.dataset.accent, duration: 0.6 }),
    onEnterBack: () => gsap.to('html', { '--current-accent': s.dataset.accent, duration: 0.6 }),
  });
});
```

## Typography

```html
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,600;1,400;1,600&family=Inter+Tight:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

```css
:root {
  --font-display: 'Fraunces', Georgia, serif;
  --font-body: 'Inter Tight', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', Consolas, monospace;
}

.display-xl { font-family: var(--font-display); font-size: clamp(64px, 12vw, 160px); line-height: 0.95; letter-spacing: -0.03em; }
.display-lg { font-family: var(--font-display); font-size: clamp(48px, 8vw, 96px); line-height: 1.0; letter-spacing: -0.02em; }
.display-md { font-family: var(--font-display); font-size: clamp(32px, 5vw, 56px); line-height: 1.1; }

.body-lg { font-size: 19px; line-height: 1.55; color: var(--text-secondary); }
.body-md { font-size: 17px; line-height: 1.6; color: var(--text-secondary); }

.mono-eyebrow { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--current-accent); }
.mono-label { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.08em; color: var(--text-caption); }

/* Italic in headlines uses the live accent */
.display-xl em, .display-lg em, .display-md em {
  font-style: italic; color: var(--current-accent); font-weight: 500;
}
```

**One italic word per headline, max.** On the verb or noun that carries meaning.

## Section structure

Each section follows this skeleton. The eyebrow is generated chrome (allowed); the headline and body come from source content.

```html
<section data-section="3" data-accent="#ffb068" class="act">
  <div class="eyebrow mono-eyebrow">// 03 — THE WORK</div>
  <h2 class="display-lg" data-mask-group>
    <span data-mask><span><!-- source headline line 1 --></span></span>
    <span data-mask><span><!-- source headline line 2, with one <em> --></span></span>
  </h2>
  <div class="section-body">
    <!-- source content here, restyled, never reworded -->
  </div>
</section>
```

## Common section patterns

Pick the patterns that match the source's actual content. Don't force every pattern.

### Hero / Identity

Full viewport. Headline IS the hero. No card, no CTA, no gradient.

```html
<section data-section="1" data-accent="#6cd4ff" class="act act-hero">
  <div class="hero-mark" aria-hidden="true">P.S.</div>  <!-- monogram from source's actual initials -->
  <div class="mono-eyebrow">// 01 — IDENTITY</div>
  <h1 class="display-xl" data-mask-group>
    <!-- source's actual headline, broken into mask spans -->
  </h1>
  <p class="body-lg"><!-- source's positioning line --></p>
  <div class="scroll-hint" aria-hidden="true">
    <span class="mono-label">SCROLL</span>
    <div class="scroll-line"></div>
  </div>
</section>
```

```css
.act-hero { display: flex; flex-direction: column; justify-content: center; min-height: 100vh; padding: 0 clamp(24px, 5vw, 80px); position: relative; }
.hero-mark { position: absolute; right: 5vw; top: 30%; font-family: var(--font-display); font-size: clamp(200px, 40vw, 600px); opacity: 0.04; pointer-events: none; }
.scroll-line { width: 1px; height: 64px; background: linear-gradient(to bottom, var(--current-accent), transparent); animation: scrollHint 2s ease-in-out infinite; }
@keyframes scrollHint { 0%, 100% { transform: scaleY(1); transform-origin: top; } 50% { transform: scaleY(0.3); transform-origin: top; } }
```

### Pillars row (philosophy / approach / values)

Three or four columns, each with numbered eyebrow, title, short body. Pull all three from source.

```html
<div class="pillars">
  <article class="pillar">
    <div class="mono-label">01</div>
    <h3 class="display-md"><!-- pillar title from source --></h3>
    <p class="body-md"><!-- pillar body from source --></p>
  </article>
  <!-- repeat for each pillar in source -->
</div>
```

```css
.pillars { display: grid; grid-template-columns: repeat(3, 1fr); gap: 48px; max-width: 1280px; }
.pillar { padding: 32px; border-top: 1px solid var(--border); }
@media (max-width: 1100px) { .pillars { grid-template-columns: 1fr; } }
```

### IDE workspace (project showcase)

Single chrome-framed shell with traffic lights, sidebar file tree, top tabs, 2-column body (detail + preview). The one place a tab pattern is allowed in this aesthetic — switching tabs is the "I work in code" metaphor. Each project from source becomes one file/tab.

The right preview panel must NOT be a screenshot. Build a bespoke artifact per project type using the project's actual data:
- Data project → live SVG scatterplot with real metric labels
- Workflow project → vertical numbered flow diagram with stages from source
- CLI/backend project → terminal artifact with styled `$ command` line
- Scheduling project → CSS-grid allocation blocks
- ML/RAG project → pipeline panel with eval bars showing real metrics from source

```html
<div class="ide">
  <div class="ide-chrome">
    <div class="traffic-lights"><span></span><span></span><span></span></div>
    <div class="ide-path mono-label">~/portfolio/projects/</div>
  </div>
  <div class="ide-tabs"><!-- one button per project --></div>
  <div class="ide-body">
    <aside class="ide-sidebar"><!-- file tree --></aside>
    <div class="ide-panel">
      <div class="ide-pane active">
        <span class="pill"><!-- type label --></span>
        <h3 class="display-md"><!-- project name from source --></h3>
        <p><!-- description from source --></p>
        <div class="tech-tags"><!-- tags from source --></div>
      </div>
      <div class="ide-preview"><!-- bespoke artifact --></div>
    </div>
  </div>
  <div class="ide-statusbar">
    <span>● READY</span>
    <span>UTF-8 · LF · main</span>
  </div>
</div>
```

(Full CSS for IDE workspace omitted for brevity — use border `var(--border)`, accent on active states `var(--current-accent)`, mono font for chrome, serif for project names, two-column 58/42 split, stack vertically below 1100px.)

### SVG journey path (timeline)

760px-tall SVG with Bezier curve drawn via `stroke-dashoffset` tied to scroll. Nodes are absolutely-positioned divs at curve waypoints.

```js
const path = document.querySelector('.journey-path path');
const length = path.getTotalLength();
path.style.strokeDasharray = length;
path.style.strokeDashoffset = length;
ScrollTrigger.create({
  trigger: '.journey', start: 'top 80%', end: 'bottom 20%', scrub: 1,
  onUpdate: (self) => { path.style.strokeDashoffset = length * (1 - self.progress); },
});
```

Mobile: hide SVG, render as vertical timeline list.

### Counters + merit grid (proof / receipts)

Counter-up tiles for numeric metrics, 2-col grid of "merit cards" for credentials/awards. All numbers from source.

```js
new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    const el = e.target, target = +el.dataset.target, start = performance.now();
    (function tick(now) {
      const t = Math.min((now - start) / 1200, 1);
      el.textContent = Math.floor((1 - Math.pow(1 - t, 3)) * target);
      if (t < 1) requestAnimationFrame(tick);
    })(start);
  });
}, { threshold: 0.5 }).observe(el);
```

### Magnetic CTA + contact channels (invitation)

Pill button that translates toward cursor on hover. Three channel cards (email/LinkedIn/GitHub or whatever the source has).

```js
btn.addEventListener('mousemove', (e) => {
  const r = btn.getBoundingClientRect();
  const x = e.clientX - r.left - r.width / 2;
  const y = e.clientY - r.top - r.height / 2;
  btn.style.transform = `translate(${x * 0.4}px, ${y * 0.4}px)`;
});
btn.addEventListener('mouseleave', () => { btn.style.transform = 'translate(0,0)'; btn.style.transition = 'transform .4s cubic-bezier(.34,1.56,.64,1)'; });
btn.addEventListener('mouseenter', () => { btn.style.transition = ''; });
```

## Motion essentials

### Lenis smooth scroll

```js
const lenis = new Lenis({ duration: 1.2, easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)) });
function raf(t) { lenis.raf(t); requestAnimationFrame(raf); }
requestAnimationFrame(raf);
gsap.registerPlugin(ScrollTrigger);
lenis.on('scroll', ScrollTrigger.update);
gsap.ticker.add((time) => lenis.raf(time * 1000));
gsap.ticker.lagSmoothing(0);
```

### Kinetic mask reveals

```css
[data-mask] { display: block; overflow: hidden; clip-path: inset(0 0 100% 0); transition: clip-path .9s cubic-bezier(.65,0,.35,1); }
[data-mask] > * { display: inline-block; transform: translateY(110%); transition: transform .9s cubic-bezier(.65,0,.35,1); }
[data-mask].is-revealed { clip-path: inset(0 0 0 0); }
[data-mask].is-revealed > * { transform: translateY(0); }
```

```js
new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.querySelectorAll('[data-mask]').forEach((m, i) => setTimeout(() => m.classList.add('is-revealed'), i * 120));
  });
}, { threshold: 0.3 }).observe(el);
```

The 120ms stagger is critical. Tighter feels mechanical, looser feels slow.

### Custom cursor (filled dot + lagging ring)

```js
let mx = 0, my = 0, rx = 0, ry = 0;
addEventListener('mousemove', (e) => { mx = e.clientX; my = e.clientY; dot.style.transform = `translate(${mx}px,${my}px) translate(-50%,-50%)`; });
(function loop() { rx += (mx - rx) * 0.15; ry += (my - ry) * 0.15; ring.style.transform = `translate(${rx}px,${ry}px) translate(-50%,-50%)`; requestAnimationFrame(loop); })();
```

`body { cursor: none }` to hide native. Fall back on `pointer: coarse`.

### Background canvas

Full-viewport `<canvas>` at `position: fixed; z-index: -1` with sparse drifting geometric primitives (hexagons, triangles, circles, plus signs). Cursor repels nearby shapes. Density: ~1 shape per 20,000px² of viewport. Skip entirely on reduced motion.

## Global chrome

- **Wordmark** (top-left, fixed, mix-blend-mode: difference): name in serif + mono caption like `↳ portfolio`. Name pulled from source.
- **Live clock** (top-right, fixed): local time in mono, updates every 30s.
- **Progress rail** (right edge, fixed): one dot per section. Active dot fills with `--current-accent`, shows label on hover.

## Reduced motion

```js
if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
  document.querySelectorAll('[data-mask]').forEach(el => { el.style.transform = 'none'; el.style.clipPath = 'none'; });
  document.querySelectorAll('[data-target]').forEach(el => el.textContent = el.dataset.target);
  document.querySelectorAll('.journey-path path').forEach(p => p.style.strokeDashoffset = '0');
  // skip Lenis, skip canvas, skip cursor
  return;
}
```

## Mobile (<1100px)

- IDE 2-col stacks vertically; sidebar collapses to horizontal pill row above panel
- SVG journey path hidden; render as vertical list of nodes
- Headline sizes step down via `clamp()` already in type scale
- Custom cursor falls back to native on `pointer: coarse`
- Pillars row → single column

## Anti-patterns

- Hero with centered card containing gradient + "Get Started" CTA
- Three-column "About / Services / Contact" footer
- Stock photography
- Light mode default (this aesthetic is dark-first)
- Carousels or accordions hiding content (the IDE tabs are the only exception)
- Multiple italic words per headline
- Animating body paragraphs (motion is for headlines, accent shifts, cursor, canvas, counters only)
- Touching source content