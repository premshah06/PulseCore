# Decision Tree

How to classify a source site into one of the five aesthetics. Read this when classification is ambiguous from the surface read.

## The five categories

| Category | What the site is for | Example sources |
|---|---|---|
| **cinematic-editorial** | Showing who someone is and what they've made | Personal portfolio, designer site, writer's home, "look at my projects" page |
| **data-dense** | Helping someone do work with information | Internal dashboard, admin panel, monitoring tool, analytics view, log viewer, status page, ops console |
| **conversion-focused** | Getting someone to buy, sign up, or convert | E-commerce store, SaaS marketing site, pricing page, lead-gen landing page, B2B product page |
| **documentation** | Helping someone learn or look something up | API docs, library guide, technical handbook, knowledge base, tutorial site, changelog |
| **product-launch** | Announcing a new tool with intent to try | AI tool landing page, app launch page, "we built this thing — here's the demo" page |

## Classification questions

Ask these in order. Stop at the first definitive answer.

### Q1: Is the primary action "read about the person/team"?

If the homepage centers on a name, a story, or a body of work that belongs to a specific person or small team — that's **cinematic-editorial**.

Signals:
- First-person pronouns in headlines ("I build...", "We make...")
- Project showcase as the dominant content
- Personal background, education, employment history
- Single scrolling page or short multi-page (about / projects / contact)
- No pricing, no signup, no "get started"

### Q2: Is the primary action "operate on data"?

If the site is a tool people log into to view, filter, sort, monitor, or manipulate information — that's **data-dense**.

Signals:
- Tables, charts, metrics as primary content
- Filters, search, date pickers, sort controls
- Status indicators (green/yellow/red)
- Sidebar navigation between functional views
- "Logged in as..." patterns
- Information density is high — minimal whitespace
- Time-series data, real-time updates

### Q3: Is the primary action "buy" or "sign up"?

If the site exists to convert visitors into customers, leads, or subscribers — that's **conversion-focused**.

Signals:
- Pricing displayed prominently
- Multiple CTAs ("Buy", "Start Free Trial", "Get a Demo", "Add to Cart")
- Product cards with prices
- Testimonials, logos, social proof
- FAQ, money-back guarantee, return policy
- Comparison tables ("us vs them")
- Forms collecting contact info

### Q4: Is the primary action "look something up"?

If the site is reference material that people search and scan for specific answers — that's **documentation**.

Signals:
- Sidebar table of contents
- Code blocks throughout
- Anchor links on every heading
- "Was this page helpful?" patterns
- Search bar prominent in header
- Version selectors, language selectors
- Cross-linked between pages

### Q5: Is the primary action "try this new thing"?

If the site introduces a single product (often AI/software) with a "see it in action" or "join waitlist" intent — that's **product-launch**.

Signals:
- Single-page-ish, with possibly a few supporting pages
- Live demo or interactive preview embedded
- "How it works" walkthrough
- Use case examples
- One primary CTA repeated ("Try it", "Get early access", "Start building")
- Often dark mode, often AI-coded vibes that this skill is fighting against
- Usually launched recently — feels temporal

## Edge cases

### "It's a portfolio but with a blog/docs section"

Pick **cinematic-editorial** for the homepage and primary sections. If the blog or docs section is substantial, you can apply **documentation** specifically to those pages while the rest stays cinematic-editorial. Note the split in the README.

### "It's a SaaS product page with a dashboard preview"

The marketing/landing page is **conversion-focused**. The actual dashboard (if it's part of the redesign scope) is **data-dense**. Two different aesthetics, two different builds. Do not try to unify them — they serve different users in different mental modes.

### "It's an AI tool and the user wants it to look 'different from generic AI sites'"

Default to **product-launch**, then explicitly avoid the anti-patterns listed in `product-launch.md` (the "generic AI vibe" section is specifically called out there). If the user is allergic to anything that looks like a product launch, suggest **cinematic-editorial** instead and frame the AI tool as the maker's project.

### "It's an e-commerce store but very design-forward / fashion / luxury"

Still **conversion-focused** — the goal is purchase. But the conversion-focused reference includes a "luxury / fashion" variant with reduced density, larger imagery, and minimal pricing emphasis. Note the variant.

### "It's an internal tool but they want it to 'feel premium'"

Still **data-dense**. Premium-feeling data-dense exists — Linear, Vercel dashboard, Figma — and the data-dense reference covers it. Do not switch to conversion-focused; that aesthetic harms task efficiency.

### "It's a documentation site for a B2B SaaS"

**documentation** for the docs themselves. The product's marketing site is a separate thing.

### "It's a personal site that's also selling a course or book"

If the course/book is the dominant CTA → **conversion-focused** (the personal story becomes social proof for the product).
If the course/book is a side note in a portfolio of work → **cinematic-editorial** (with the course as one of the projects).

### "I genuinely can't tell"

Ask the user one question with the five options as buttons. Do not guess.

## Multi-page apps

If the source is a multi-page app where different pages serve different purposes (e.g., marketing pages + a dashboard + docs), apply different aesthetics to different routes. Build a small `routes.md` in the README listing which aesthetic applies to which path. Each aesthetic still has its own self-contained CSS — share only the absolute base reset (typography reset, box-sizing, etc.), not the design tokens.

## What "dominant" means

When a site spans categories, "dominant" means: which page does the user spend most time on, and which page drives the primary business outcome? A SaaS site with a flashy marketing page and a deep product is **dominant in product** — but if you're only redesigning the marketing page, you're working in **conversion-focused** even though the product itself would be **data-dense**.

Always confirm with the user which pages are in scope before classifying.