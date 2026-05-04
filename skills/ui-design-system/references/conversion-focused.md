# Conversion-Focused

For: e-commerce stores, SaaS marketing sites, pricing pages, lead-gen landing pages, B2B product pages. The job is to move visitors toward purchase or signup. The aesthetic must be **trustworthy, scannable, decisive** — not "pretty" at the expense of clarity.

## When this aesthetic fits

- The page exists to drive a transaction (buy, subscribe, sign up, request demo)
- Pricing is displayed
- The visitor is in evaluation mode, comparing options
- Success metric is conversion rate

## When it doesn't

- The actual product UI after signup → data-dense
- Documentation about the product → documentation
- Brand/portfolio sites where conversion isn't the goal → cinematic-editorial

## The core principle

**Clarity beats cleverness.** Every section answers a question the visitor is asking: What is it? Why should I care? What does it cost? Will it work for me? What do I do next?

The aesthetic supports clarity — it does not draw attention to itself.

## Two variants

Pick one based on source:

- **Variant A — SaaS / B2B / Software**: Clean, modern, conversion-optimized. Linear/Vercel/Stripe vibe. This is the default.
- **Variant B — Premium / Fashion / Lifestyle**: Larger imagery, more whitespace, less text density, restrained typography. Aēsop/Glossier/Apple vibe.

Most sources fit Variant A. Pick B only if the source is selling a physical premium product or experience.

## Palette — Variant A (SaaS default)

Light mode default — conversion sites convert better in light mode in most contexts. (Source data is industry-mixed; if the source is dark-mode-first, honor that.)

```css
:root {
  --bg: #ffffff;
  --bg-subtle: #fafbfc;
  --bg-muted: #f4f5f7;
  --bg-card: #ffffff;
  --bg-dark: #0a0b0d;  /* for dark sections / footer */

  --text-primary: #0a0b0d;
  --text-secondary: #4a4f59;
  --text-tertiary: #6b7280;
  --text-on-dark: #f4f5f7;

  --border: #e5e7eb;
  --border-strong: #d1d5db;

  /* Brand — pick one from source's existing brand if available */
  --brand: #5b6cff;
  --brand-hover: #4858e6;
  --brand-bg: #eef0ff;

  /* Trust signals */
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
}
```

If the source has an existing brand color, use it as `--brand`. The source's logo or hero illustration will tell you. Don't invent one.

## Palette — Variant B (Premium)

```css
:root {
  --bg: #fafaf7;       /* warm paper white */
  --bg-subtle: #f4f3ee;
  --bg-card: #ffffff;
  --text-primary: #1a1a1a;
  --text-secondary: #595959;
  --text-tertiary: #8a8a8a;
  --border: rgba(0, 0, 0, 0.08);
  --border-strong: rgba(0, 0, 0, 0.16);
  --brand: #1a1a1a;    /* black is the brand */
  --accent: #b8826e;   /* warm muted secondary, only if source supports */
}
```

## Typography

### Variant A

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

```css
:root { --font-sans: 'Inter', system-ui, sans-serif; }

.h1 { font-size: clamp(40px, 6vw, 72px); line-height: 1.05; letter-spacing: -0.02em; font-weight: 700; }
.h2 { font-size: clamp(32px, 4vw, 48px); line-height: 1.1; letter-spacing: -0.015em; font-weight: 600; }
.h3 { font-size: 24px; line-height: 1.25; font-weight: 600; }
.body-lg { font-size: 19px; line-height: 1.55; color: var(--text-secondary); }
.body { font-size: 17px; line-height: 1.6; color: var(--text-secondary); }
.eyebrow { font-size: 13px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--brand); }
```

### Variant B

```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400&family=Inter:wght@400;500&display=swap" rel="stylesheet">
```

```css
:root { --font-display: 'Cormorant Garamond', 'Didot', serif; --font-sans: 'Inter', sans-serif; }
.h1 { font-family: var(--font-display); font-size: clamp(48px, 7vw, 96px); line-height: 1.05; font-weight: 400; letter-spacing: -0.01em; }
.h2 { font-family: var(--font-display); font-size: clamp(32px, 4vw, 56px); line-height: 1.15; font-weight: 400; }
```

## Hero patterns

### Variant A — SaaS hero

Headline + subheadline + primary CTA + secondary CTA + visual (product screenshot, illustration, or animated mockup). Trust strip below (logos of customers).

```html
<section class="hero">
  <div class="hero-text">
    <div class="eyebrow"><!-- optional eyebrow from source --></div>
    <h1 class="h1"><!-- source headline, verbatim --></h1>
    <p class="body-lg hero-sub"><!-- source subheadline, verbatim --></p>
    <div class="cta-row">
      <a class="btn btn-primary" href="..."><!-- primary CTA from source --></a>
      <a class="btn btn-ghost" href="..."><!-- secondary CTA from source --></a>
    </div>
    <div class="hero-microcopy"><!-- e.g., "No credit card required" if source has it --></div>
  </div>
  <div class="hero-visual">
    <!-- product screenshot from source, or bespoke recreation -->
  </div>
</section>

<section class="trust-strip">
  <div class="trust-label"><!-- e.g., "Trusted by teams at" --></div>
  <div class="trust-logos">
    <!-- customer logos from source -->
  </div>
</section>
```

```css
.hero { max-width: 1280px; margin: 0 auto; padding: 96px 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; }
.hero-sub { margin: 24px 0 32px; max-width: 560px; }
.cta-row { display: flex; gap: 12px; }
.hero-microcopy { margin-top: 16px; font-size: 13px; color: var(--text-tertiary); }
.trust-strip { padding: 48px 24px; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.trust-logos { display: flex; gap: 48px; align-items: center; justify-content: center; flex-wrap: wrap; opacity: 0.6; filter: grayscale(1); }
.trust-logos:hover { opacity: 0.9; filter: grayscale(0); transition: all 0.3s; }
@media (max-width: 1024px) { .hero { grid-template-columns: 1fr; padding: 64px 24px; } }
```

### Variant B — Premium hero

Full-bleed image + headline overlaid or below + minimal CTA.

```css
.hero-premium { min-height: 80vh; position: relative; }
.hero-premium img { width: 100%; height: 80vh; object-fit: cover; }
.hero-premium .h1 { position: absolute; left: 48px; bottom: 48px; max-width: 60%; color: #fff; mix-blend-mode: difference; }
```

## Buttons

```css
.btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; border-radius: 8px; font-size: 15px; font-weight: 500; cursor: pointer; border: 1px solid transparent; transition: all 0.15s; text-decoration: none; }
.btn-primary { background: var(--brand); color: white; }
.btn-primary:hover { background: var(--brand-hover); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(91, 108, 255, 0.25); }
.btn-secondary { background: var(--bg-card); color: var(--text-primary); border-color: var(--border-strong); }
.btn-secondary:hover { background: var(--bg-muted); }
.btn-ghost { background: transparent; color: var(--text-primary); }
.btn-ghost:hover { background: var(--bg-muted); }
.btn-lg { padding: 16px 28px; font-size: 17px; }
```

## Pricing tables

Most-conversion-critical component. Three columns is canonical (free / pro / enterprise) but match what the source has. The "recommended" tier gets visual emphasis.

```html
<section class="pricing">
  <h2 class="h2"><!-- pricing headline from source --></h2>
  <div class="pricing-grid">
    <article class="price-card">
      <div class="price-tier"><!-- tier name from source --></div>
      <div class="price-amount"><span class="price-num"><!-- price --></span><span class="price-period">/mo</span></div>
      <p class="price-desc"><!-- tier description from source --></p>
      <a class="btn btn-secondary"><!-- CTA from source --></a>
      <ul class="price-features">
        <li><svg class="check"></svg><!-- feature 1 --></li>
        <!-- features from source -->
      </ul>
    </article>

    <article class="price-card price-card-featured">
      <div class="price-badge">Most popular</div>
      <!-- ...same structure for the recommended tier -->
    </article>

    <article class="price-card">
      <!-- ...third tier -->
    </article>
  </div>
</section>
```

```css
.pricing-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; max-width: 1200px; margin: 48px auto 0; }
.price-card { padding: 32px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; display: flex; flex-direction: column; gap: 16px; position: relative; }
.price-card-featured { border: 2px solid var(--brand); transform: translateY(-8px); box-shadow: 0 12px 32px rgba(91, 108, 255, 0.15); }
.price-badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--brand); color: white; font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 999px; }
.price-amount { font-size: 48px; font-weight: 700; }
.price-period { font-size: 16px; font-weight: 400; color: var(--text-tertiary); }
.price-features { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }
.price-features li { display: flex; align-items: center; gap: 10px; font-size: 14px; color: var(--text-secondary); }
.check { width: 16px; height: 16px; color: var(--success); flex-shrink: 0; }

@media (max-width: 1024px) { .pricing-grid { grid-template-columns: 1fr; } .price-card-featured { transform: none; } }
```

## Feature sections

Three or four feature blocks, alternating layout (text-left/visual-right, then visual-left/text-right). Each block has eyebrow, headline, body, optional CTA, and a visual.

```css
.feature { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; padding: 96px 24px; max-width: 1280px; margin: 0 auto; align-items: center; }
.feature:nth-child(even) .feature-text { order: 2; }
.feature-visual { aspect-ratio: 4/3; background: var(--bg-muted); border-radius: 12px; overflow: hidden; }
@media (max-width: 1024px) { .feature { grid-template-columns: 1fr; } .feature:nth-child(even) .feature-text { order: 0; } }
```

## Testimonials

Use real testimonials from source verbatim. Pattern:

```html
<article class="testimonial">
  <div class="testimonial-quote"><!-- quote from source --></div>
  <div class="testimonial-attr">
    <img src="..." class="testimonial-avatar" />
    <div>
      <div class="testimonial-name"><!-- name from source --></div>
      <div class="testimonial-role"><!-- role @ company from source --></div>
    </div>
  </div>
</article>
```

```css
.testimonial { padding: 32px; background: var(--bg-subtle); border-radius: 12px; }
.testimonial-quote { font-size: 19px; line-height: 1.55; color: var(--text-primary); margin-bottom: 24px; }
.testimonial-quote::before { content: '"'; font-size: 48px; color: var(--brand); line-height: 0; vertical-align: -0.5em; margin-right: 4px; }
.testimonial-attr { display: flex; align-items: center; gap: 12px; }
.testimonial-avatar { width: 40px; height: 40px; border-radius: 50%; }
.testimonial-name { font-weight: 600; font-size: 14px; }
.testimonial-role { font-size: 13px; color: var(--text-tertiary); }
```

## FAQ

Use `<details>` for accordion behavior — accessibility-correct, no JS needed.

```css
.faq { max-width: 720px; margin: 0 auto; }
.faq details { border-bottom: 1px solid var(--border); padding: 20px 0; }
.faq summary { font-size: 17px; font-weight: 500; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; }
.faq summary::after { content: '+'; font-size: 24px; transition: transform 0.2s; }
.faq details[open] summary::after { content: '−'; }
.faq details[open] { padding-bottom: 24px; }
.faq details p { margin-top: 12px; color: var(--text-secondary); line-height: 1.6; }
```

## E-commerce specifics (product cards, cart, checkout)

For e-commerce sources specifically:

### Product card

```html
<article class="product-card">
  <a href="..."><img src="..." class="product-image" /></a>
  <div class="product-info">
    <h3 class="product-name"><!-- from source --></h3>
    <div class="product-price"><!-- from source --></div>
  </div>
  <button class="btn btn-secondary product-add"><!-- "Add to cart" or whatever source uses --></button>
</article>
```

```css
.product-card { display: flex; flex-direction: column; gap: 12px; }
.product-image { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 8px; transition: opacity 0.3s; }
.product-card:hover .product-image { opacity: 0.85; }
.product-name { font-size: 16px; font-weight: 500; }
.product-price { font-size: 14px; color: var(--text-secondary); }
```

Variant B uses larger product images (4:5 aspect), no border-radius, more whitespace below.

## Motion

Restrained. Conversion sites that animate too much feel cheap or push visitors toward decisions.

- Buttons: subtle hover lift (`translateY(-1px)`) and shadow
- Cards: subtle hover (border-color shift, optional 1–2px lift)
- Section reveals: simple fade-in-up via IntersectionObserver, single direction, ~400ms, light easing
- Numbers in stats: count-up if there are real metrics worth highlighting (otherwise skip)
- No parallax on hero
- No carousels for testimonials/products unless the source already has them and they're necessary

```js
new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('is-visible'); });
}, { threshold: 0.15 }).observe(el);
```

```css
.fade-up { opacity: 0; transform: translateY(20px); transition: opacity 0.5s ease, transform 0.5s ease; }
.fade-up.is-visible { opacity: 1; transform: translateY(0); }
```

## Trust signals

Conversion sites earn trust through visible signals. Honor whatever the source has:

- Customer logos (in the trust strip)
- Real testimonials with photos and full attribution
- Press mentions ("As seen in...")
- Security badges (SOC 2, GDPR) if source mentions them
- Specific numbers ("12,000+ teams", "$2B processed") — use only what source actually claims
- Money-back guarantee, free trial terms — use source's actual terms verbatim

Never invent these. If the source doesn't have them, leave them out.

## Anti-patterns

- Hero with stock photo of diverse people pointing at laptop screens
- Auto-playing video background on hero
- "Limited time!" countdown timers unless the source genuinely has a deadline
- Exclamation marks in CTAs unless source uses them
- Fake testimonials, fake logos, fake metrics
- Carousels for things the user needs to compare (pricing, features) — show them in parallel
- Overly aggressive popups (exit-intent, scroll-triggered) — these are conversion-killing in 2026
- Dark patterns: pre-checked checkboxes, hidden costs, "are you sure you want to leave?" guilt prompts
- Decorative gradient blobs floating behind every section
- Gradient text on every headline

## Mobile

- Hero stacks vertically; visual moves above or below text per source preference
- Pricing cards stack; the featured card loses its `translateY(-8px)` lift
- Feature sections stack with consistent text-then-visual order (don't alternate on mobile)
- Sticky CTA bar at bottom is acceptable on long pages
- Tap targets minimum 44×44px

## Accessibility

- Form labels are visible (placeholders are not labels)
- Pricing tables marked up as actual tables OR cards with clear headings — screen readers must hear "Pro plan, $29 per month, includes..."
- Color is never the only signal for state (success/error use icons + color)
- Focus states must be visible on all interactive elements
- Skip-to-content link at the top