---
name: ui-design-system
description: Transform any website's visual design into a category-appropriate, opinionated, non-generic aesthetic — without altering content. The skill classifies the project (portfolio, dashboard, e-commerce, documentation, product-launch, or editorial) then applies the matching design system: cinematic editorial for portfolios and personal sites, data-dense functional for dashboards and admin panels, conversion-focused for e-commerce and SaaS marketing, documentation-grade for docs sites and API references, product-launch for AI tool and app landing pages. Use this skill whenever the user asks to "redesign," "restyle," "transform the UI," "change the look," "apply a design system," "make it look professional," "make it feel like [a magazine / a dashboard / a real product / a doc site]," or otherwise wants to rebuild the visual layer of a website. The skill MUST preserve all existing copy, headings, links, data, and information architecture exactly as written — only styling, layout chrome, motion, typography, and color treatment change. Trigger this even when the user only describes the vibe ("editorial," "data-heavy," "conversion-optimized," "dev-tool aesthetic") without naming the skill or a specific aesthetic explicitly.
---

# UI Design System

A **router skill** that classifies the project type and applies the right opinionated aesthetic. Each aesthetic is defined in its own reference file with concrete tokens, patterns, and motion rules — not vague design advice.

## The hard rule (applies to every aesthetic)

**Restyle, do not rewrite.** Every word, heading, link label, list item, image caption, project description, contact handle, date, number, credential, price, product name, and field label that exists on the source site must appear on the transformed site, verbatim. Do not paraphrase. Do not "improve" copy. Do not drop sections. Do not invent placeholder content where real content exists.

What you CAN change:
- HTML wrapper structure around content (semantic tags, container divs, section ordering visually but not narratively)
- All CSS (layout, typography, color, spacing, motion)
- All JavaScript that drives presentation
- Adding chrome around content (eyebrows, status bars, breadcrumbs, navigation patterns) — these are framing devices, not content
- Replacing generic stock screenshots with bespoke SVG/CSS recreations of the same data

What you CANNOT change:
- Headline wording, body copy, product names, company names, dates, locations, metrics, contact details, prices, error messages, form labels, CTA text
- The set of sections present (if the source has 4 products, the redesign has 4 — not 5, not 3)
- Factual claims, numbers, credentials, URLs, legal text

If the user explicitly says "you can also rewrite the copy," content edits are permitted. Absent that explicit permission, source text is immutable.

## Workflow

### Step 1 — Classify the project

Read the source. In one or two sentences, identify what kind of site this is. Use this rubric:

| If the site is primarily about... | Use aesthetic |
|---|---|
| A person showing their work, story, projects, writing — single-page or short scroll narrative | **cinematic-editorial** |
| Internal tools, admin panels, analytics, monitoring, status pages, CRUD interfaces, data tables | **data-dense** |
| Selling something — products, subscriptions, services, B2B SaaS, lead generation, pricing pages | **conversion-focused** |
| Reference material — API docs, library guides, technical handbooks, knowledge bases, changelogs | **documentation** |
| Launching a product — AI tool, app, software, with demo / signup / "try it" intent — single-page-ish | **product-launch** |

If the source spans multiple categories (e.g., a portfolio with a documentation section), pick the dominant one and note the secondary. Most "blended" sites are actually one category with auxiliary pages.

If you genuinely cannot classify, **ask the user one question** with concrete options. Do not guess.

For full classification rubric including edge cases and signals to look for, see `references/_decision-tree.md`.

### Step 2 — Inventory the source content

Before writing any code:
1. List every section, heading, paragraph, list item, link, image, data point, form field.
2. Note information architecture — what navigates to what, what's grouped together.
3. Identify factual content (numbers, prices, dates, credentials) that must survive verbatim.
4. Note any source-specific structure that the redesign needs to honor (e.g., "the source has 7 products in 3 categories — the redesign needs the same 7 in the same 3 groupings").

### Step 3 — Load the aesthetic reference

Based on classification, read the matching reference file:

- **cinematic-editorial** → `references/cinematic-editorial.md`
- **data-dense** → `references/data-dense.md`
- **conversion-focused** → `references/conversion-focused.md`
- **documentation** → `references/documentation.md`
- **product-launch** → `references/product-launch.md`

Each reference file is self-contained with palette, typography, spacing, layout patterns, motion rules, and category-specific anti-patterns.

**Do not load multiple aesthetic references at once.** Pick one. The aesthetics are deliberately incompatible — mixing them produces the generic vibe-code result this skill exists to avoid.

### Step 4 — Build the site

Follow the patterns in the loaded reference. Each reference uses the same structural skeleton:

```
project-folder/
├── index.html       (or multiple .html files for multi-page categories)
├── styles.css
├── main.js
└── README.md
```

Plus aesthetic-specific files where called for (e.g., `background.js` for cinematic-editorial, `charts.js` for data-dense).

Pull HTML and JS dependencies from CDN (Tailwind, GSAP, Lenis, Chart.js, etc. as the aesthetic specifies).

### Step 5 — Verify content fidelity

Before declaring done, do a diff pass:
1. Open source. Open redesign. Read side by side.
2. For every headline, paragraph, data point, form field, link, and price in the source, confirm it appears verbatim in the redesign.
3. If anything was dropped, restyled into oblivion, or reworded — fix it.
4. Tell the user explicitly: "I preserved all original content. Here's the inventory I worked from: [list]. If anything is missing, point me to it."

### Step 6 — Honor accessibility and reduced motion

Across every aesthetic:
- `prefers-reduced-motion: reduce` short-circuits all transitions and reveals — content visible by default, counters jump to final value, paths render fully drawn, smooth-scroll libraries disabled.
- Color contrast meets WCAG AA minimum (4.5:1 for body text, 3:1 for large text).
- Interactive elements have visible focus states.
- Touch devices (`pointer: coarse`) get native-cursor and tap-friendly hit targets.
- Mobile breakpoints stack appropriately — no aesthetic should be desktop-only.

### Step 7 — Ship

Deliver:
- All source files, runnable by opening `index.html`.
- A short `README.md` explaining: which aesthetic was applied and why, how to run, where to find the source content blocks (so the user can update them later), which CSS custom properties to tweak.

## When NOT to use this skill

- A small CSS tweak (color change, single font swap) — handle inline, no skill needed.
- A brand-new site from scratch with content that doesn't exist yet — the user needs content help, not a restyle.
- The user wants an aesthetic that's none of the five (e.g., brutalist, glassmorphism, skeuomorphic) — say so honestly and offer to either pick the closest fit or build a one-off without using this skill.
- The source is already in one of these aesthetics and just needs polish — direct edits will be cleaner than running the full transform.

## Cross-aesthetic principles

These hold regardless of which reference you load:

1. **Tokens, not magic numbers.** Every color, font size, spacing value lives in a CSS custom property. Hardcoding hex values inside components defeats the system.
2. **One opinionated choice per axis.** One serif. One sans. One mono. One accent shift mechanism. One motion library. Mixing produces the generic look.
3. **Italics are precious** in any aesthetic that uses serif display type. One italic word per headline, on the verb or noun that carries meaning.
4. **No marketing tropes** as defaults — no "Get Started Free!" exclamation marks, no stock-photo hero with gradient overlay, no three-column "About / Services / Contact" footer, no emoji in copy unless the source has them.
5. **Content density follows category.** A dashboard packs information; a portfolio breathes. Don't apply portfolio whitespace to a dashboard or dashboard density to a portfolio.
6. **Motion serves comprehension.** Animate to direct attention or signal state change. Animating decoration is the generic-AI tell.

## Reference index

- `references/_decision-tree.md` — Full classification rubric, edge cases, signals.
- `references/cinematic-editorial.md` — Portfolios, personal sites, scroll narratives.
- `references/data-dense.md` — Dashboards, admin panels, analytics, monitoring tools.
- `references/conversion-focused.md` — E-commerce, SaaS marketing, pricing pages, lead-gen.
- `references/documentation.md` — Docs sites, API references, technical handbooks.
- `references/product-launch.md` — AI tools, apps, single-page product launches.

Read the `_decision-tree.md` if classification is uncertain. Otherwise, classify, load the matching reference, and build.

## Final reminder

Restyle, do not rewrite. The source author chose those words. Your job is to give those words a stage worthy of them — and the right stage depends on what kind of show is playing.