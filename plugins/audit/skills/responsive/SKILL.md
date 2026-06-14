---
name: audit-responsive
description: Responsive/mobile optimization audit. Checks padding, breakpoints, grid collapses, side-by-side stacking, sticky elements, touch targets, overflow, typography scaling, navigation, and footer across all viewports. Works on any web project (Next.js, React, Vue, static HTML, email templates). Use /audit:responsive for full audit or /audit:responsive --fix to auto-fix.
---

# Responsive / Mobile Optimization Audit

Comprehensive audit of responsive design across all viewport sizes. Detects layout issues that break on phones, tablets, and intermediate sizes.

## Arguments

- `/audit:responsive` — audit only, print results
- `/audit:responsive <path>` — scope to a directory (e.g., `src/components/`)
- `/audit:responsive --fix` — auto-fix issues after audit
- `/audit:responsive --report` — save report to `_local/reports/audit-responsive-<YYYY-MM-DD>.md`

## Phase 1: Detect Project Type & CSS Approach

Read project config to determine what responsive system is in use:

| Check | How | Records |
|-------|-----|---------|
| Framework | `package.json`: next, react, vue, angular, svelte, astro. `index.html` for static. | Framework |
| CSS approach | `package.json`: tailwindcss, styled-components, emotion. Glob for `*.module.css`, `*.scss`. | CSS system |
| Tailwind version | If Tailwind: check version in package.json. v3 uses `tailwind.config.js`, v4 uses `@theme` in CSS. | Tailwind version |
| Breakpoints | If Tailwind: use defaults (sm:640, md:768, lg:1024, xl:1280). If custom CSS: grep for `@media` queries and extract breakpoint values. | Breakpoint list |
| Viewport meta | Grep HTML files / layout files for `<meta name="viewport"`. | Present/missing |
| Email template | Check for `<table` layout patterns, `mso-` conditionals, inline styles only. | Is email? |

Print detected setup:
```
Project: [name]
Type: Next.js 15 + React 19 + Tailwind 4
Breakpoints: sm:640 md:768 lg:1024 xl:1280
Scope: [full project or specified path]
```

## Phase 2: Run Checks

### Check 1: Fixed Horizontal Padding (Critical)

The #1 mobile layout killer. On a 375px phone, `padding: 48px` on each side leaves only 279px for content.

**How to search:**
- Grep for inline `padding:` with values containing `48px`, `40px`, `36px`, or higher horizontal values
- Grep for Tailwind classes `px-12`, `px-10`, `px-8` WITHOUT responsive prefixes (no `sm:`, `md:`, `lg:` before them)
- Grep for `padding-left:` and `padding-right:` with fixed values > 24px

**Findings:**
- Severity: HIGH for any horizontal padding > 24px without responsive reduction
- Count total instances and list top 10 worst files
- Check if a shared padding utility exists (e.g., `section-px`, `@apply`, CSS class)

**Anti-hallucination:** Only report findings from actual grep results with file:line evidence. If grep returns 0 matches, report "no instances found."

### Check 2: Side-by-Side Layouts (Critical)

Flex/grid layouts that don't stack on mobile cause horizontal scroll.

**How to search:**
- Grep for inline `display: "flex"` or `display: flex` WITHOUT `flex-direction: column` or `flex-wrap` nearby
- Grep for inline `flex:` with fixed basis values like `"0 0 50%"`, `"0 0 40%"`, `"1 1 60%"`
- Grep for Tailwind `flex` class WITHOUT `flex-col` or `flex-wrap` on the same element
- Grep for inline `gridTemplateColumns:` with fixed multi-column values like `"1fr 1fr"`, `"repeat(2, 1fr)"`, etc.
- Check if responsive stacking exists: `flex-col lg:flex-row`, `flex-col md:flex-row`, `grid-cols-1 md:grid-cols-2`

**Findings:**
- Severity: HIGH for side-by-side layouts with no responsive stacking
- Severity: MEDIUM for layouts that stack but at the wrong breakpoint (e.g., stacks at `xl:` when content overflows at `md:`)

**Anti-hallucination:** For each finding, verify by reading the actual element's full className + style props. A flex container with `flex-wrap` is acceptable.

### Check 3: Fixed Width Elements (High)

Elements with fixed pixel widths that exceed mobile viewport.

**How to search:**
- Grep for `width:` with values > 400px (inline styles)
- Grep for `w-[` with values > 400px (Tailwind arbitrary values)
- Grep for `maxWidth:` or `max-width:` with values > 400px that lack responsive alternatives
- Grep for `minWidth:` or `min-width:` with values > 300px

**Findings:**
- Severity: HIGH for fixed `width` > viewport (375px) without responsive override
- Severity: MEDIUM for `maxWidth` > 600px without responsive reduction
- Note: `maxWidth` with `margin: "0 auto"` is usually fine (content just gets narrower)

### Check 4: Grid Column Collapse (High)

Multi-column grids that don't reduce columns on mobile.

**How to search:**
- Grep for `grid-cols-2`, `grid-cols-3`, `grid-cols-4` WITHOUT responsive prefix
- Grep for inline `gridTemplateColumns:` with `repeat(N, 1fr)` where N > 1
- Grep for inline `gridTemplateColumns: "1fr 1fr"` etc.
- Check if `.responsive-grid` or equivalent CSS utility exists

**Findings:**
- Severity: HIGH for 3+ column grids with no mobile collapse
- Severity: MEDIUM for 2-column grids with no mobile collapse (may still fit on phones depending on content)

### Check 5: Navigation (Critical)

Mobile navigation is essential — desktop nav links don't fit on 375px.

**How to search:**
- Find the main navigation component (grep for `<nav`, `TopNav`, `Header`, `Navbar`)
- Check for: hamburger menu, mobile drawer, `hidden lg:flex` pattern on nav links
- Check for: `menuOpen` state, toggle function, body scroll lock
- Check for `position: fixed` or `position: sticky` on mobile menu — verify no ancestor has `overflow: hidden` or `backdrop-filter` (both break `position: fixed/sticky`)

**Findings:**
- Severity: CRITICAL for no mobile menu at all
- Severity: HIGH for mobile menu that doesn't close on route change
- Severity: HIGH for mobile menu inside an element with `backdrop-filter` (creates containing block, clips fixed positioning)
- Severity: MEDIUM for missing body scroll lock when menu is open

**Anti-hallucination:** Read the actual nav component file. Don't assume a hamburger exists — verify by finding the toggle button/icon.

### Check 6: Overflow Detection (High)

Elements that cause horizontal scroll on mobile.

**How to search:**
- Grep for negative margins: `margin-left:` or `margin-right:` with negative values, `marginLeft: -`, `marginRight: -`
- Check if negative margins have responsive guards (e.g., `lg:ml-[-200px]` only on desktop, zero on mobile)
- Grep for `overflow: hidden` on parent containers — these can break `position: sticky` for children
- Grep for fixed-width images: `width={1400}` or similar without `className="w-full"`
- Check for tables without horizontal scroll wrapper on mobile

**Findings:**
- Severity: HIGH for unguarded negative margins
- Severity: HIGH for `overflow: hidden` on containers with sticky children
- Severity: MEDIUM for wide tables without scroll wrapper

### Check 7: Typography Scaling (Medium)

Large font sizes that overwhelm mobile screens.

**How to search:**
- Grep for `fontSize:` with values > 32px (inline styles)
- Grep for `text-4xl`, `text-5xl`, `text-6xl` etc. without responsive prefix
- Check if `clamp()` is used for large headings
- Check for `letterSpacing` > 3px (causes overflow on narrow screens with long words)

**Findings:**
- Severity: MEDIUM for headings > 36px without responsive scaling
- Severity: LOW for body text > 18px without scaling (usually fine)

### Check 8: Touch Targets (Medium)

Interactive elements must be at least 44x44px on mobile for reliable tapping.

**How to search:**
- Grep for buttons and links with `padding` < 8px or `height` < 36px
- Check icon-only buttons: `width: 20px` or similar without adequate padding
- Check for `font-size: 11px` or `text-xs` on interactive elements (too small to read/tap)

**Findings:**
- Severity: MEDIUM for buttons/links < 44px touch area
- Severity: LOW for non-interactive small text

### Check 9: Responsive Images (Medium)

Images that don't scale or are oversized for mobile.

**How to search:**
- Grep for `<img` without `className="w-full"` or `max-width: 100%`
- If Next.js: check for `next/image` usage (preferred over `<img>`)
- Check for images with fixed `width` and `height` attributes but no responsive className
- Check for `aspect-ratio` usage on image containers (helps maintain proportions)

**Findings:**
- Severity: MEDIUM for images without responsive sizing
- Severity: HIGH for raw `<img>` in Next.js projects (should use `next/image`)

### Check 10: Footer Responsiveness (Medium)

Footers with multi-column grids, badge rows, or complex layouts.

**How to search:**
- Find footer component (grep for `<footer`, `Footer`)
- Check for: grid columns that don't collapse, `gap` values > 32px, fixed padding
- Check for: badge/icon rows that overflow horizontally without `flex-wrap`
- Check for: link rows that don't wrap

**Findings:**
- Severity: MEDIUM for footer grids that don't collapse on mobile
- Severity: LOW for large gaps that could be reduced

### Check 11: Sticky Elements (Medium)

Sticky elements that break on mobile due to parent overflow or incorrect `top` values.

**How to search:**
- Grep for `position: sticky` or `sticky` class
- For each sticky element, trace its parent chain — check for `overflow: hidden`, `overflow: auto`, or `backdrop-filter` on any ancestor
- Check `top` values: do they account for the mobile nav height?
- Check for sticky elements that should be disabled on mobile (e.g., TOC sidebars)

**Findings:**
- Severity: HIGH for sticky elements inside `overflow: hidden` parent (sticky won't work)
- Severity: MEDIUM for incorrect `top` values (element hides behind nav)

### Check 12: TOC / Sidebar Handling (Medium)

Sidebars that consume too much horizontal space on phones.

**How to search:**
- Grep for sidebar patterns: `w-[220px]`, `w-[280px]`, fixed-width side panels
- Check if sidebars are hidden on mobile: `hidden sm:block`, `hidden md:block`
- Check if there's a mobile alternative (collapsible, horizontal pills, etc.)

**Findings:**
- Severity: HIGH for visible sidebar on mobile that's > 200px wide
- Severity: MEDIUM for sidebar without mobile alternative

### Check 13: Button & CTA Alignment (Low)

Buttons that look awkward left-aligned on mobile when content is centered.

**How to search:**
- Find CTA button groups (grep for `btn-filled`, `btn-primary`, `btn-cta`)
- Check if parent has `text-center sm:text-left` or `justify-center sm:justify-start`
- Check if button pairs stack vertically on phones: `flex-col sm:flex-row`

**Findings:**
- Severity: LOW for left-aligned buttons on mobile (functional but not ideal)
- Severity: MEDIUM for button pairs that overlap/cramp on mobile

### Check 14: Responsive Tailwind Prefix Usage (Meta)

**Skip if:** no Tailwind detected.

**How to search:**
- Count total responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`) across all component files
- Count total `style={{` inline occurrences
- If responsive prefix count is 0 or very low relative to inline styles, the project is not responsive

**Findings:**
- Severity: CRITICAL for zero responsive prefixes (site is desktop-only)
- Provides a quick health metric: "responsive prefix density"

### Check 15: Hub-and-Spoke / SVG / Complex Visual Layouts (Low)

Visual layouts with absolute positioning that break on small screens.

**How to search:**
- Grep for `position: absolute` or `position: "absolute"` with percentage-based `left`/`top` values
- Check for SVG `viewBox` elements with hardcoded dimensions
- Check for hub-and-spoke or radial layouts

**Findings:**
- Severity: MEDIUM for absolute-positioned layouts without mobile alternative
- Recommendation: hide on mobile, show simple grid/list alternative

## Phase 3: Scoring

Each check scores 0-10:

| Score | Meaning |
|-------|---------|
| 10 | No findings |
| 8-9 | Only LOW findings |
| 6-7 | Some MEDIUM findings, no HIGH |
| 4-5 | HIGH findings present |
| 2-3 | Multiple HIGH findings |
| 0-1 | CRITICAL — site is unusable on mobile |

**Overall grade** = weighted average (Critical checks 2x weight):

- A: 9.0+ (90%+) — fully responsive, polished
- B: 8.0+ (80%+) — responsive with minor issues
- C: 7.0+ (70%+) — partially responsive, usable
- D: 6.0+ (60%+) — major gaps
- F: below 6.0 — desktop-only or severely broken

## Phase 4: Report

```markdown
## Responsive Audit — [Project Name]
### Type: [detected] | Date: [YYYY-MM-DD] | Scope: [path]

| # | Check | Score | Severity | Key Issues |
|---|-------|-------|----------|------------|
| 1 | Fixed Padding | 8/10 | LOW | 3 files with >24px unguarded |
| 2 | Side-by-Side Layouts | 3/10 | HIGH | 12 flex layouts don't stack |
| ... | ... | ... | ... | ... |
| **Overall** | **6.2/10** | **D** | |

### Critical Viewport: 375px (iPhone SE)
- Usable content width with current padding: Xpx
- Horizontal overflow detected: Yes/No
- Navigation: Mobile menu present/missing

### Priority Actions
1. [CRITICAL] Add mobile hamburger menu — nav links overflow on phones
2. [HIGH] Add responsive stacking to 12 side-by-side layouts: flex-col lg:flex-row
3. [HIGH] Replace fixed 48px padding with responsive scale (16px mobile → 48px desktop)
...
```

### Breakpoint Impact Matrix

For each HIGH/CRITICAL finding, note which breakpoints are affected:

```
| Finding | <375px | 375-639px | 640-767px | 768-1023px | 1024px+ |
|---------|--------|-----------|-----------|------------|---------|
| Nav overflow | BROKEN | BROKEN | BROKEN | OK | OK |
| 3-col grid | BROKEN | BROKEN | CRAMPED | OK | OK |
```

## Phase 5: Fix (with --fix flag)

Apply fixes in this order:

1. **Navigation** — add mobile menu if missing (hamburger + slide-out panel)
2. **Padding** — convert fixed horizontal padding to responsive scale
3. **Side-by-side layouts** — add `flex-col lg:flex-row` stacking
4. **Grid collapses** — add responsive column counts
5. **Fixed widths** — add responsive width classes
6. **Overflow** — guard negative margins, add scroll wrappers for tables
7. **Sticky fixes** — remove `overflow: hidden` from sticky ancestors, adjust `top` values
8. **Sidebar handling** — hide on mobile with `hidden sm:block`
9. **Button alignment** — center on mobile with `text-center sm:text-left`
10. **Typography** — add `clamp()` or responsive font sizes for large headings
11. **Images** — add `w-full h-auto` classes
12. **Footer** — collapse grids, reduce gaps, wrap badges

### Fix Rules:
- Page must look identical on desktop after fixes (no visual changes at 1280px+)
- Mobile layout should be single-column, readable, no horizontal overflow
- Test at: 375px (iPhone SE), 390px (iPhone 14), 768px (iPad portrait), 1024px (iPad landscape)
- Run build after all fixes
- If CSS framework (Tailwind) exists, prefer framework classes over inline media queries

### Fix Patterns Reference (from real-world responsive refactor):

**Responsive padding:**
```
px-4 sm:px-6 md:px-8 lg:px-12
```
Or define a CSS utility:
```css
@utility section-px {
  padding-left: 1rem; padding-right: 1rem;
  @media (min-width: 640px) { padding-left: 1.5rem; padding-right: 1.5rem; }
  @media (min-width: 768px) { padding-left: 2rem; padding-right: 2rem; }
  @media (min-width: 1024px) { padding-left: 3rem; padding-right: 3rem; }
}
```

**Side-by-side stacking:**
```
flex flex-col lg:flex-row items-center gap-8 lg:gap-16
```

**Grid collapse:**
```
grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3
```

**Dynamic grid columns (CSS var):**
```css
.responsive-grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
@media (min-width: 768px) { .responsive-grid { grid-template-columns: repeat(var(--cols, 3), 1fr); } }
```
Usage: `className="responsive-grid" style={{ '--cols': n }}`

**Desktop-only features (negative margins, bleeds):**
```css
.hero-bleed { margin: 0; }
@media (min-width: 1024px) {
  .hero-bleed { margin-right: var(--bleed-r, 0); margin-top: var(--bleed-t, 0); }
}
```

**Mobile menu (essential pattern):**
- Hamburger button: `lg:hidden` (hidden on desktop)
- Desktop nav: `hidden lg:flex` (hidden on mobile)
- Menu panel: `position: fixed` — MUST be outside any `backdrop-filter` ancestor
- Body scroll lock: `document.body.classList.add("menu-open")` with cleanup on unmount
- Close on route change

**Inline style vs CSS class conflict:**
- Inline `display: "flex"` overrides `lg:hidden` — move display to className
- Inline `padding` shorthand overrides Tailwind `px-*` — split into paddingTop/paddingBottom
- Inline `margin` shorthand overrides Tailwind responsive margins

**Sticky element requirements:**
- No ancestor with `overflow: hidden`, `overflow: auto`, or `overflow: scroll`
- No ancestor with `backdrop-filter` (creates containing block)
- Correct `top` value accounting for sticky nav height

**Carousel/slider responsiveness:**
- Fixed card widths (e.g., 386px) overflow on 375px phones
- Use dynamic width: `containerWidth < 640 ? containerWidth - 32 : CARD_W_DESKTOP`
- Guard resize state updates: `setCardW(prev => prev === newW ? prev : newW)`

**Complex visual layouts (hub-and-spoke, SVG diagrams):**
- Hide on mobile: `hidden md:block`
- Show simple grid/list alternative: `md:hidden grid grid-cols-1 sm:grid-cols-2 gap-3`

**TOC/sidebar on mobile:**
- Hide sidebar: wrap in `<div className="hidden sm:block">`
- Parent layout: `sm:flex sm:gap-10` (flex only on tablet+)
- Content goes full-width on phones

**Footer badges on mobile:**
- Use `transform: scale(N)` to enlarge small badges (inline maxHeight can't be overridden by CSS)
- Add `margin` to compensate for scale (scale is visual only, doesn't affect layout flow)
- Stack vertically: target the flex container with `flex-direction: column` via CSS class

## Anti-Hallucination Rules

1. **Every finding must have a real file path and line number** confirmed by grep/read tool calls
2. **Do not invent component names** — discover them from the codebase
3. **Do not assume breakpoint values** — read them from config/CSS
4. **Do not report Tailwind findings in non-Tailwind projects**
5. **Do not report framework-specific findings for the wrong framework**
6. **If grep returns 0 matches, report "no instances found"** — do not fabricate findings
7. **Verify sticky element issues by reading the parent chain** — don't assume overflow exists
8. **Check both className AND style props** on the same element — inline styles override classes
9. **Score based only on concrete findings** with evidence, never on assumptions
10. **A `flex-wrap` container is NOT a side-by-side layout issue** — verify before flagging
11. **An element with `maxWidth` and `margin: auto` is NOT a fixed-width issue** — it contracts on narrow screens
12. **Dynamic inline styles (ternaries, state-dependent) are acceptable** — only flag static values
13. **Theme picker / color switcher hex values are data, not display colors** — don't flag them as token violations
