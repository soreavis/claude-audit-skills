---
name: audit-seo
description: SEO, technical SEO, and GEO (Generative Engine Optimization) audit. Checks meta tags, structured data, crawlability, internal linking, URL structure, and AI-findability. Works on any web frontend.
user-invocable: true
argument-hint: "[--fix] [--scope=<path>] [--report] [--seo-only] [--geo-only] [--technical-only]"
---

# SEO + Technical SEO + GEO Audit

Comprehensive audit covering on-page SEO quality, technical crawlability, and AI/LLM findability (GEO). Works on any web project that renders HTML.

## Arguments

- `$ARGUMENTS` — optional flags:
  - `--fix` — auto-fix issues where possible (add meta tags, structured data, canonical URLs)
  - `--scope=<path>` — limit to specific directory or set of pages
  - `--report` — save report to `_local/reports/seo-audit-<YYYY-MM-DD>.md`
  - `--seo-only` — run only on-page SEO checks (Category 1)
  - `--geo-only` — run only GEO checks (Category 3)
  - `--technical-only` — run only technical SEO checks (Category 2)
  - No flags = run all three categories, report only

### Flag Precedence

Only ONE `--*-only` flag allowed. If multiple passed: `--technical-only` > `--seo-only` > `--geo-only`.

## Setup

### Detect Stack & Pages

| Check | How |
|-------|-----|
| Framework | `package.json`: `next`, `nuxt`, `gatsby`, `astro`, `remix`, `@angular/core`. Or static HTML. |
| Rendering | SSR/SSG (Next.js, Nuxt, Astro, Gatsby) vs SPA (CRA, Vite+React) vs Static HTML |
| Routing | File-based (`app/`, `pages/`) or config-based (react-router, vue-router) |
| i18n | Check for `next-intl`, `next-i18next`, `i18n` config, `hreflang`, `/[locale]/` routes |
| CMS | Check for `contentful`, `sanity`, `strapi`, `wordpress`, `prismic` in deps |

### Discover All Pages/Routes

**Next.js App Router:** Glob for `app/**/page.{tsx,jsx,ts,js}` — each is a route. Exclude `(groups)` from URL path. Check for `[slug]` dynamic routes.

**Next.js Pages Router:** Glob for `pages/**/*.{tsx,jsx,ts,js}` — exclude `_app`, `_document`, `_error`, `api/`.

**Nuxt/Astro/Gatsby:** Glob for `pages/**/*.{vue,astro,tsx}` or `src/pages/**/*`.

**Static HTML:** Glob for `**/*.html` (exclude `node_modules/`, `dist/`).

**SPA with react-router:** Grep for `<Route path=` or `createBrowserRouter` — extract route paths. Note: SPA SEO is inherently limited without SSR/SSG.

**If zero pages found:** Print "No pages/routes found. This audit requires a web frontend." and STOP.

Build a page inventory:
```
| Route | File | Type | Has metadata |
|-------|------|------|-------------|
| / | app/page.tsx | Static | Yes |
| /about | app/about/page.tsx | Static | Yes |
| /blog/[slug] | app/blog/[slug]/page.tsx | Dynamic | Check |
```

## Category 1: On-Page SEO

### Check 1.1: Meta Titles — Severity: HIGH

**How to check per page:**
- Next.js App Router: look for `metadata` export with `title` field, or `generateMetadata` function
- Next.js Pages Router: Grep for `<Head>` containing `<title>`
- Static HTML: check for `<title>` tag
- Check title content quality:
  - Exists = basic PASS
  - Length: 30-60 chars is optimal. Flag <30 (too short) or >60 (truncated in SERPs)
  - Unique: no two pages should share the same title. Cross-reference all pages.
  - Contains primary keyword hint: check if title relates to the page's route/content (heuristic — don't enforce specific keywords)

**Findings:**
- FAIL: page has no title
- WARN: title too short (<30) or too long (>60)
- WARN: duplicate title across pages
- PASS: title exists, good length, unique

### Check 1.2: Meta Descriptions — Severity: MEDIUM

**How to check:**
- Same approach as 1.1, look for `description` in metadata/meta tags
- Quality checks:
  - Exists = basic PASS
  - Length: 120-160 chars optimal. Flag <70 (too short) or >160 (truncated)
  - Unique per page
  - Not identical to title

**Findings:**
- FAIL: no description
- WARN: too short/long, duplicate, or identical to title

### Check 1.3: Heading Structure for SEO — Severity: MEDIUM

**How to check:**
- Per page: Grep for `<h1`, `<h2`, `<h3` etc.
- SEO rules (beyond a11y):
  - Exactly one `<h1>` per page — it should represent the page topic
  - `<h1>` should not be identical to `<title>` (wastes keyword opportunity)
  - `<h2>`s should cover subtopics/sections
  - No empty headings (`<h1></h1>` or `<h1>{""}</h1>`)

**Findings:**
- FAIL: no h1, or multiple h1s
- WARN: h1 identical to title tag, empty headings

### Check 1.4: Image SEO — Severity: MEDIUM

**How to check:**
- Grep for `<img`, `next/image`, `<Image` — for each:
  - Has `alt` attribute with descriptive text (not just `alt=""` which is a11y-decorative)
  - Has `width` and `height` attributes (prevents CLS)
  - Uses descriptive filename (not `IMG_0032.jpg` or `screenshot-2024.png`)
  - Has responsive sizing (`srcSet`, `sizes`, or Next.js automatic)

**Findings:**
- WARN: images with empty alt that appear to be content images (not decorative)
- WARN: images without dimensions (CLS risk, affects Core Web Vitals → ranking)
- LOW: images with non-descriptive filenames

### Check 1.5: Open Graph & Social Meta — Severity: MEDIUM

**How to check:**
- Per page: check for `og:title`, `og:description`, `og:image`, `og:url`, `og:type`
- Check for Twitter/X cards: `twitter:card`, `twitter:title`, `twitter:image`
- Next.js: check `openGraph` and `twitter` in metadata export

**Findings:**
- WARN: missing OG tags (links shared on social look plain)
- WARN: OG image missing or not sized correctly (1200x630 recommended)
- LOW: missing Twitter card meta

### Check 1.6: Canonical URLs — Severity: HIGH

**How to check:**
- Per page: check for `<link rel="canonical" href="...">` or `alternates.canonical` in Next.js metadata
- If dynamic routes exist, check that canonical resolves to the correct absolute URL (not relative)
- Check that canonical doesn't point to a different page (self-referencing is correct for most pages)

**Findings:**
- FAIL: no canonical URLs on any page (critical for avoiding duplicate content)
- WARN: missing canonical on specific pages
- WARN: canonical uses relative URL (should be absolute)

### Check 1.7: Internal Linking — Severity: MEDIUM

**How to check:**
- Grep for `<a href=`, `<Link href=` — collect all internal links (paths starting with `/` or relative)
- Build a link map: which pages link to which
- Find orphan pages: pages that no other page links to (unreachable via navigation)
- Find pages with very few inbound links (<2 internal links pointing to them)

**Findings:**
- WARN: orphan pages (no internal links pointing to them)
- LOW: pages with low internal link count

### Check 1.8: URL Structure — Severity: LOW

**How to check:**
- Review all route paths for SEO-friendly patterns:
  - Lowercase: flag uppercase characters in URLs
  - Hyphens: flag underscores (hyphens preferred for SEO)
  - Length: flag URLs with >5 path segments (too deep)
  - Descriptive: flag routes that are just IDs or hashes without context

**Findings:**
- WARN: uppercase in URLs
- WARN: underscores instead of hyphens
- LOW: deeply nested URLs

## Category 2: Technical SEO

### Check 2.1: robots.txt — Severity: HIGH

**How to check:**
- Check for `public/robots.txt`, `app/robots.ts` (Next.js), or equivalent
- If found, read its content:
  - Check for `Disallow: /` (blocks everything — intentional?)
  - Check for sitemap reference (`Sitemap: https://...`)
  - Check for unnecessary blocks (blocking CSS/JS can hurt rendering)

**Findings:**
- FAIL: no robots.txt
- WARN: robots.txt blocks all (`Disallow: /`) without apparent reason
- WARN: no sitemap reference in robots.txt

### Check 2.2: Sitemap — Severity: HIGH

**How to check:**
- Check for: `public/sitemap.xml`, `app/sitemap.ts` (Next.js dynamic), sitemap generation in build scripts
- If found:
  - Check it references all discovered pages
  - Check for `<lastmod>` dates
  - Check it's referenced in robots.txt

**Findings:**
- FAIL: no sitemap
- WARN: sitemap exists but missing pages
- WARN: sitemap not referenced in robots.txt

### Check 2.3: Redirect Chains — Severity: MEDIUM

**How to check:**
- Search config files for redirects: `next.config.*` redirects/rewrites, `_redirects` (Netlify), `vercel.json` redirects
- Check for chains: redirect A → B → C (should be A → C directly)
- Check for redirect loops
- Check that old URLs redirect with 301 (permanent), not 302 (temporary) for SEO

**Findings:**
- WARN: redirect chains (flatten to single hop)
- FAIL: redirect loops
- WARN: 302 redirects that should be 301

### Check 2.4: noindex/nofollow Usage — Severity: HIGH

**How to check:**
- Grep for `noindex`, `nofollow` in meta robots tags, metadata exports, or HTTP headers
- Per page: is it intentional? Flag if applied to pages that should be indexed (main content pages)
- Check for `X-Robots-Tag` in headers config

**Findings:**
- WARN: `noindex` on content pages (might be accidental)
- PASS: `noindex` on utility pages (login, admin, thank-you) — intentional
- Note: "Cannot determine intent — verify noindex is intentional on flagged pages"

### Check 2.5: Duplicate Content — Severity: MEDIUM

**How to check:**
- Check if trailing slash and non-trailing-slash versions both resolve (Next.js `trailingSlash` config)
- Check if `www.` and non-`www.` are handled (need redirect one to the other)
- Check dynamic routes: do different parameters render the same content?
- Check for canonical tags (1.6) — canonical is the fix for duplicate content

**Findings:**
- WARN: trailing slash inconsistency without canonical
- WARN: potential duplicate content across similar routes without differentiation

### Check 2.6: Page Speed Signals — Severity: MEDIUM

**How to check (from code, not runtime):**
- Check for `next/image` usage vs raw `<img>` (image optimization)
- Check for code splitting / dynamic imports on route-level components
- Check for `<script>` tags without `async` or `defer`
- Check for render-blocking CSS (large CSS files in `<head>` without critical CSS extraction)
- Check for web font loading: `next/font`, `font-display: swap`, or `<link rel="preload">`
- Note: "Full Core Web Vitals measurement requires Lighthouse or PageSpeed Insights. This checks code-level optimization signals only."

**Findings:**
- WARN: render-blocking scripts without async/defer
- WARN: raw `<img>` instead of optimized image component
- LOW: no font preloading or `font-display: swap`

### Check 2.7: Mobile-Friendly — Severity: HIGH

**How to check:**
- Check for `<meta name="viewport" content="width=device-width, initial-scale=1">`
- Check CSS for responsive patterns: media queries, flexbox/grid that adapts
- Check for fixed-width containers that won't fit mobile (`width: 1200px` etc.)
- Check for `overflow-x: hidden` on body (sometimes hides horizontal scroll issues)

**Findings:**
- FAIL: no viewport meta tag
- WARN: fixed-width layout that doesn't adapt to mobile
- PASS: viewport + responsive patterns found

### Check 2.8: Internationalization (i18n) — Severity: MEDIUM

**N/A if project is single-language with no i18n config.**

**How to check:**
- Check for `hreflang` tags or `alternates.languages` in metadata
- Check that each language version has proper `lang` attribute on `<html>`
- Check for `x-default` hreflang
- Check that all language versions are in the sitemap

**Findings:**
- WARN: i18n configured but missing hreflang tags
- WARN: missing `x-default` hreflang
- WARN: language versions missing from sitemap

## Category 3: GEO (Generative Engine Optimization)

Checks for AI/LLM findability — how well AI search engines (Google AI Overview, Bing Chat, Perplexity, ChatGPT Browse) can extract and cite content from this site.

### Check 3.1: Structured Data / JSON-LD — Severity: HIGH

**How to check:**
- Grep for `application/ld+json`, `<script type="application/ld+json"`, `jsonLd` in source files
- Check for common schema types:
  - `Organization` — on homepage
  - `WebSite` — with `SearchAction` for sitelinks search box
  - `Article` / `BlogPosting` — on blog/content pages
  - `FAQPage` — on FAQ sections
  - `Product` — on product pages
  - `BreadcrumbList` — on any page with breadcrumbs
  - `LocalBusiness` — if applicable

**Findings:**
- FAIL: no structured data at all (AI engines rely heavily on schema.org)
- WARN: structured data exists but missing key types for the site type
- PASS: comprehensive structured data with relevant types

### Check 3.2: FAQ Schema & Q&A Content — Severity: MEDIUM

**How to check:**
- Grep for FAQ-like patterns: `FAQ`, `frequently asked`, accordion components, `<details>/<summary>`, expandable sections
- If FAQ content exists: check if it has `FAQPage` JSON-LD markup
- Check for `HowTo` schema on tutorial/guide content

**Findings:**
- WARN: FAQ content exists without FAQPage schema (AI engines extract FAQ schema directly)
- WARN: how-to content without HowTo schema
- N/A: no FAQ or how-to content found

### Check 3.3: Clear Entity Definitions — Severity: MEDIUM

**How to check:**
- Check homepage and about page for clear first-paragraph entity definition (who/what is this company/product/person?)
- Pattern: look for a prominent text block near the top of the main page that answers "What is [brand]?"
- Check for `Organization` or `Person` schema with complete properties: `name`, `description`, `url`, `logo`, `sameAs` (social links)

**Findings:**
- WARN: no clear entity definition on homepage (AI can't summarize what this site is about)
- WARN: Organization schema missing `description` or `sameAs`
- Note: this check is heuristic. "Verify that the homepage's first visible paragraph clearly explains what this site/product/company is."

### Check 3.4: Content Structure for AI Extraction — Severity: MEDIUM

**How to check:**
- Check content pages for:
  - Clear section headings (h2/h3) that serve as topic labels
  - Concise first paragraph per section (AI extracts leading sentences)
  - Lists (`<ul>`, `<ol>`) for enumerations (AI prefers structured lists over prose)
  - Tables for comparison data (AI extracts tables well)
  - Definition patterns (`<dl>`, or "X is Y" sentences)

**Findings:**
- WARN: long prose paragraphs without section headings (hard for AI to chunk)
- LOW: comparison content in prose instead of tables
- LOW: enumerations in prose instead of lists
- Note: "Content structure recommendations are heuristic — assess based on actual content type."

### Check 3.5: Citation-Worthy Signals — Severity: LOW

**How to check:**
- Check for author attribution: `author` in metadata, bylines on blog posts, author pages
- Check for publication dates: `datePublished`, `dateModified` in metadata/schema
- Check for source attribution: `<cite>`, `<blockquote>`, references/bibliography sections
- Check for expertise signals: credentials, "about the author" sections

**Findings:**
- WARN: blog/article content without author attribution (reduces citation trust)
- WARN: content without publication dates (AI deprioritizes undated content)
- LOW: no author pages for blog contributors

### Check 3.6: AI Crawl Access — Severity: HIGH

**How to check:**
- Read `robots.txt` for AI-specific crawlers:
  - `GPTBot` (OpenAI/ChatGPT)
  - `Google-Extended` (Google Gemini/Bard — deprecated but may still exist)
  - `anthropic-ai` (Claude)
  - `CCBot` (Common Crawl, used by many AI training sets)
  - `Bytespider` (TikTok/ByteDance AI)
  - `PerplexityBot`
- Check if they're blocked (`Disallow`) or allowed
- Note: blocking AI crawlers is a valid business choice — just verify it's intentional

**Findings:**
- WARN: AI crawlers explicitly blocked (verify intentional — reduces AI search visibility)
- PASS: AI crawlers not blocked (default allow)
- PASS: AI crawlers explicitly allowed
- Note: "If blocking AI crawlers is intentional (e.g., content licensing concerns), this is not a bug — just document the decision."

### Check 3.7: Content Freshness Signals — Severity: LOW

**How to check:**
- Check for `<lastmod>` in sitemap
- Check for `dateModified` in structured data
- Check blog/content pages for visible "last updated" dates
- Check for `<meta http-equiv="last-modified">` or `Last-Modified` HTTP header config

**Findings:**
- WARN: no freshness signals (AI engines may deprioritize stale-looking content)
- PASS: lastmod in sitemap and/or dateModified in schema

### Check 3.8: SPA/JavaScript Rendering — Severity: HIGH

**How to check:**
- If project is SPA (client-side rendering only, no SSR/SSG):
  - WARN: "Client-only rendering means AI crawlers may see empty HTML. Critical content is invisible to search engines without JavaScript execution."
  - Check for `prerender.io`, `rendertron`, or similar pre-rendering solutions
- If SSR/SSG: PASS (content is in initial HTML)
- Check for critical content behind `useEffect` or dynamic loading that wouldn't be in SSR output

**Findings:**
- FAIL: SPA without pre-rendering (content invisible to crawlers)
- WARN: important content loaded only via client-side fetch (may not be in SSR HTML)
- PASS: SSR/SSG with content in initial render

## Report

```markdown
# SEO + GEO Audit — [Project Name]
**Date:** YYYY-MM-DD | **Stack:** [detected] | **Pages:** [count] | **Rendering:** [SSR/SSG/SPA]

## Score: X/Y checks passed — Grade [A-F]

| Category | Pass | Warn | Fail | N/A |
|----------|------|------|------|-----|
| On-Page SEO (8 checks) | X | X | X | X |
| Technical SEO (8 checks) | X | X | X | X |
| GEO (8 checks) | X | X | X | X |

## Per-Page Summary (top issues)
| Page | Title | Description | Canonical | Schema | OG | Issues |
|------|-------|-------------|-----------|--------|-----|--------|
| / | OK (45 chars) | OK (140 chars) | Missing | Organization | OK | 1 |
| /about | Too long (72) | Missing | OK | None | Missing | 3 |
| /blog/[slug] | Dynamic | Dynamic | OK | Article | OK | 0 |

## Critical Issues
[FAIL items with page, check, and file:line]

## Warnings
[WARN items grouped by category]

## GEO Recommendations
[Top 5 actions to improve AI findability]

## Quick Wins
[Changes with highest SEO impact for lowest effort]
```

**Grade:** A (90%+ pass), B (80%+), C (70%+), D (60%+), F (<60%). Based on applicable checks only.

## Fix Phase (with --fix flag)

Fix in order of impact:

1. **Critical (must fix):**
   - Add canonical URLs to all pages
   - Add viewport meta tag if missing
   - Create robots.txt if missing
   - Create basic sitemap if missing
   - Add JSON-LD Organization schema to homepage layout

2. **High priority:**
   - Add meta titles/descriptions to pages missing them
   - Add OG tags to pages missing them
   - Add `FAQPage` schema to FAQ sections
   - Fix noindex on pages that should be indexed

3. **Medium:**
   - Add `BreadcrumbList` schema
   - Add `Article` schema to blog posts
   - Add author attribution to blog posts
   - Fix heading structure

4. **Low:**
   - Add `dateModified` to schema
   - Add `lastmod` to sitemap entries
   - Fix URL structure issues

### Fix Rules:
- **Do NOT invent content.** When adding meta descriptions, use the page's first paragraph as a starting point and note "TODO: write custom description." Do NOT fabricate marketing copy.
- **Structured data must be valid.** Use schema.org types correctly. Only add properties you have real values for — do NOT fill with placeholder data.
- **Test with Google Rich Results Test** after adding structured data (recommend, don't run).
- Run build after fixes to verify.

## Anti-Hallucination Rules

- **Page routes must be real.** Discover them via Glob/Grep. Do NOT assume routes like `/about`, `/contact`, `/blog` exist.
- **Meta tag content must be read, not assumed.** Read the actual file to check what the title/description says. Do NOT assume from the route name.
- **Do NOT fabricate structured data quality judgments.** If JSON-LD exists, report what types are present. Do NOT judge if the content is "good enough" without reading it.
- **Duplicate content detection is heuristic.** Report trailing slash config and canonical presence. Do NOT claim "these pages have duplicate content" without evidence of identical rendering.
- **GEO checks are advisory.** AI search algorithms are opaque and change frequently. Frame GEO findings as "best practices that improve AI findability" not "required for ranking."
- **SPA SEO limitations are real.** If the project is a client-rendered SPA, the content IS invisible to most crawlers. This is a factual statement, not speculation.
- **Do NOT fabricate search volume or ranking predictions.** Never say "this keyword gets X searches" or "this will rank for Y." That requires external tools (Ahrefs, SEMrush) not available here.
- **robots.txt blocking AI crawlers may be intentional.** Report it, don't judge it. Some sites block AI crawlers for valid legal/business reasons.
- **Content quality is subjective.** Check 3.4 (content structure) is heuristic. Flag clear structural issues (long paragraphs without headings) but do NOT judge writing quality.
