---
name: audit-a11y
description: Accessibility audit against WCAG 2.1 AA. Checks semantic HTML, alt text, keyboard navigation, contrast, form labels, ARIA, focus management, and motion preferences. Works on any web frontend.
user-invocable: true
argument-hint: "[--fix] [--scope=<path>] [--report] [--level=A|AA|AAA]"
---

# Accessibility Audit (WCAG 2.1)

Audit the frontend for WCAG 2.1 compliance. Default level: AA. Checks HTML semantics, images, keyboard, contrast, forms, ARIA, focus, and motion.

## Arguments

- `$ARGUMENTS` — optional flags:
  - `--fix` — auto-fix issues where possible (add alt text placeholders, fix ARIA, add labels)
  - `--scope=<path>` — limit to specific directory or component
  - `--report` — save report to `_local/reports/a11y-audit-<YYYY-MM-DD>.md`
  - `--level=A|AA|AAA` — WCAG conformance level (default: AA)
  - No flags = audit only at AA level, report to conversation

## Setup

### Detect Frontend Stack

| Check | How |
|-------|-----|
| Framework | `package.json`: `react`, `next`, `vue`, `nuxt`, `@angular/core`, `svelte` |
| Rendering | SSR (Next.js, Nuxt) vs SPA (Create React App, Vite + React) vs Static |
| Component files | Glob for `**/*.{tsx,jsx,vue,svelte,html}` |
| CSS approach | Tailwind, CSS modules, styled-components, globals |

**If no frontend files found:** Print "No frontend components found. This audit is for web frontends only." and STOP.

### Determine Scope

If no `--scope`: scan all component/page files. Exclude `node_modules/`, test files, storybook files.

## Checks

Each check maps to a WCAG success criterion. Results: **PASS**, **FAIL**, **WARN**, **N/A**.

### Check 1: Semantic HTML Structure (WCAG 1.3.1, 2.4.1, 2.4.6)

**1a: Heading hierarchy**
- Grep for `<h1`, `<h2`, `<h3`, `<h4`, `<h5`, `<h6` across all page components
- Check: does each page have exactly one `<h1>`? Do headings follow sequential order (no skipping from h1 to h3)?
- PASS: proper heading hierarchy
- FAIL: skipped heading levels, multiple h1s per page, or no h1
- Severity: HIGH

**1b: Landmark regions**
- Grep for: `<main`, `<nav`, `<header`, `<footer`, `<aside`, `<section`, `role="main"`, `role="navigation"`, `role="banner"`, `role="contentinfo"`
- Check: does the page have at least `<main>` and `<nav>`?
- PASS: landmarks present
- FAIL: no landmarks — screen readers can't navigate by region
- Severity: MEDIUM

**1c: Lists for list content**
- Search for content patterns that should be lists but aren't: repeated `<div>` or `<span>` siblings with similar structure (navigation items, feature lists, pricing tiers)
- PASS: list content uses `<ul>`, `<ol>`, `<dl>`
- WARN: potential list content without list markup
- Severity: LOW
- Note: this check is heuristic — may have false positives. Only flag clear cases.

**1d: No div/span for interactive elements**
- Grep for: `<div.*onClick`, `<span.*onClick`, `<div.*role="button"` (should be `<button>`)
- Grep for: `<div.*href`, `<span.*href` patterns (should be `<a>`)
- PASS: interactive elements use proper HTML elements
- FAIL: divs/spans with click handlers instead of buttons/links
- Severity: HIGH
- Fix: replace `<div onClick>` with `<button onClick>`, `<span href>` with `<a href>`

### Check 2: Images & Media (WCAG 1.1.1, 1.4.5)

**2a: Alt text on images**
- Grep for: `<img` and check for `alt=` attribute
- Also grep for: `next/image` imports and check their `alt` prop
- Three valid states:
  - `alt="descriptive text"` = PASS (informative image)
  - `alt=""` = PASS (decorative image, intentionally empty)
  - No `alt` attribute at all = FAIL
- FAIL: images without any alt attribute
- Severity: HIGH

**2b: Decorative images properly hidden**
- For images with `alt=""`: check they also have `aria-hidden="true"` or are CSS background images
- PASS: decorative images properly marked
- WARN: `alt=""` without `aria-hidden` (technically valid but best practice)
- Severity: LOW

**2c: SVG accessibility**
- Grep for: `<svg` — check for `role="img"` + `aria-label` or `<title>` element inside
- For decorative SVGs: check for `aria-hidden="true"`
- PASS: SVGs have accessible names or are hidden
- WARN: SVGs without accessible treatment
- Severity: MEDIUM

**2d: No text in images**
- Check for images that might contain text (this is heuristic — look for images named `banner`, `hero`, `cta`, `promo` that might have baked-in text)
- WARN: potential text-in-image (cannot be read by screen readers, doesn't scale)
- Severity: LOW (advisory only — can't verify without viewing the image)

### Check 3: Keyboard Navigation (WCAG 2.1.1, 2.1.2, 2.4.3, 2.4.7)

**3a: Focus visible**
- Grep for CSS that removes focus: `outline: none`, `outline: 0`, `:focus { outline: none }`, `*:focus { outline: 0 }`
- Check if custom focus styles are provided as replacement (`:focus-visible` with visible ring/outline)
- PASS: default focus styles intact, or custom focus-visible styles provided
- FAIL: focus outline removed without replacement
- Severity: CRITICAL
- Fix: add `:focus-visible` styles with visible outline/ring

**3b: Tab order**
- Grep for: `tabIndex` or `tabindex` with positive values (`tabIndex={1}`, `tabindex="2"`)
- Positive tabindex overrides natural DOM order — almost always wrong
- `tabIndex={0}` (make focusable) and `tabIndex={-1}` (programmatic focus) are fine
- PASS: no positive tabindex values
- FAIL: positive tabindex values found
- Severity: HIGH

**3c: No keyboard traps**
- Search for modal/dialog components: Grep for `dialog`, `modal`, `Dialog`, `Modal`
- For each: check if they handle Escape key to close and trap focus within (not escape focus to background)
- Check for `onKeyDown` or `onKeyUp` handlers with `Escape` handling
- PASS: modals handle Escape and focus trapping
- WARN: modals found without keyboard handling
- Severity: HIGH

**3d: Skip to content link**
- Search for: `skip-to-content`, `skip-nav`, `skipLink`, `skip-to-main`, `#main-content`
- Check if a skip link exists as the first focusable element on the page
- PASS: skip link found
- WARN: no skip link — keyboard users must tab through all navigation
- Severity: MEDIUM

### Check 4: Color & Contrast (WCAG 1.4.3, 1.4.6, 1.4.11)

**4a: Text contrast**
- This check is LIMITED from code alone. What we CAN do:
  - Extract text color + background color pairs from CSS/Tailwind classes
  - For Tailwind: `text-*` paired with `bg-*` on same or parent element
  - For CSS: `color:` paired with `background-color:` or `background:`
  - Check known-bad combinations: light gray text on white, white text on light backgrounds
- PASS: no obviously low-contrast combinations found
- WARN: potential low-contrast combinations (list them with file:line)
- Severity: HIGH (AA requires 4.5:1 for normal text, 3:1 for large text)
- Note: "Full contrast audit requires a running page. Use browser DevTools or axe-core for precise measurement. This check catches obvious violations only."

**4b: Non-text contrast**
- Check UI components (buttons, inputs, icons) have sufficient contrast against background
- Grep for: border colors, icon colors that might be too light
- WARN: potential issues (advisory — needs visual verification)
- Severity: MEDIUM (AA level, 3:1 ratio)

**4c: Color not sole indicator**
- Search for patterns where color alone conveys meaning: error states using only red text, success using only green, required fields using only color
- Check for additional indicators: icons, text labels, underlines
- PASS: color used with additional indicators
- WARN: potential color-only indicators
- Severity: MEDIUM

### Check 5: Forms & Inputs (WCAG 1.3.1, 3.3.1, 3.3.2, 4.1.2)

**5a: Labels linked to inputs**
- Grep for `<input`, `<select`, `<textarea` — for each, check:
  - Has `id` and a corresponding `<label htmlFor="...">` or `<label for="...">`
  - Or is wrapped in a `<label>` element
  - Or has `aria-label` or `aria-labelledby`
- PASS: all inputs have associated labels
- FAIL: inputs without labels
- Severity: HIGH

**5b: Required fields indicated**
- Grep for `required` attribute or `aria-required="true"` on form inputs
- Check if required state is communicated visually AND programmatically (not just `*` in label without `required` attribute)
- PASS: required fields properly marked
- WARN: visual-only required indicators (asterisk without `required` attr)
- Severity: MEDIUM

**5c: Error identification**
- Check form validation: are error messages associated with their inputs via `aria-describedby` or `aria-errormessage`?
- Check: do errors have `role="alert"` or `aria-live` region?
- PASS: errors properly associated and announced
- FAIL: errors displayed but not programmatically linked to inputs
- Severity: HIGH (also covered by audit-forms C12, but this is more thorough)

**5d: Input purpose (autocomplete)**
- Check common form fields for `autocomplete` attribute:
  - Name fields → `autocomplete="name"` or `"given-name"` / `"family-name"`
  - Email → `autocomplete="email"`
  - Phone → `autocomplete="tel"`
  - Address → `autocomplete="street-address"`, etc.
- PASS: common fields have autocomplete
- WARN: missing autocomplete on standard fields
- Severity: LOW (AA level)

### Check 6: ARIA Usage (WCAG 4.1.2)

**6a: ARIA roles valid**
- Grep for `role="` — check that each role value is a valid WAI-ARIA role
- Common mistakes: `role="form"` (valid but often misused), `role="text"` (not valid)
- PASS: all roles are valid
- FAIL: invalid role values
- Severity: MEDIUM

**6b: ARIA states/properties valid**
- Grep for `aria-` attributes — check they're valid and properly valued
- Common mistakes: `aria-hidden="false"` on elements that should be visible (just remove it), `aria-label` on non-interactive elements
- PASS: valid usage
- WARN: questionable usage
- Severity: MEDIUM

**6c: No redundant ARIA**
- Check for ARIA that duplicates native HTML semantics:
  - `<button role="button">` — redundant
  - `<a href="..." role="link">` — redundant
  - `<nav role="navigation">` — redundant
  - `<input type="checkbox" role="checkbox">` — redundant
- PASS: no redundant ARIA
- WARN: redundant ARIA found (not harmful but indicates misunderstanding)
- Severity: LOW

**6d: ARIA labels on interactive elements**
- For icon-only buttons (buttons containing only `<svg>` or icon component, no text):
  - Check for `aria-label` on the button
- For links with non-descriptive text ("click here", "read more", "learn more"):
  - Check for `aria-label` with descriptive text
- PASS: interactive elements have accessible names
- FAIL: icon-only buttons without aria-label
- Severity: HIGH

### Check 7: Focus Management (WCAG 2.4.3, 3.2.1)

**7a: Focus on route change (SPA)**
- For SPAs/client-side routing: check if focus is managed on navigation
- React Router / Next.js: look for focus management after route transitions
- Check for: `focus()` calls after navigation, `aria-live` regions for route announcements, `next/navigation` usage
- PASS: focus management implemented
- WARN: no focus management on route changes — screen reader users lose context
- Severity: MEDIUM
- N/A: server-rendered pages (non-SPA)

**7b: Focus return from modals**
- Check modal/dialog implementations: when closed, does focus return to the trigger element?
- Look for: stored trigger reference, `focus()` call in close handler
- PASS: focus returned to trigger
- WARN: focus not explicitly managed on close
- Severity: MEDIUM

### Check 8: Motion & Animation (WCAG 2.3.1, 2.3.3)

**8a: Reduced motion support**
- Grep for: `prefers-reduced-motion` in CSS files, Tailwind `motion-reduce:` or `motion-safe:` classes, `matchMedia("(prefers-reduced-motion"` in JS
- PASS: reduced motion queries found
- WARN: animations/transitions exist but no `prefers-reduced-motion` support
- Severity: MEDIUM
- To check if animations exist: Grep for `animation:`, `transition:`, `@keyframes`, `animate-` (Tailwind), `framer-motion`, `react-spring`, `gsap`

**8b: No auto-playing content**
- Grep for: `autoPlay`, `autoplay` on `<video>` or `<audio>` elements
- Check for: auto-advancing carousels, auto-scrolling content
- PASS: no auto-playing media
- WARN: auto-playing content found (needs pause/stop control)
- Severity: MEDIUM

### Check 9: Language & Document (WCAG 3.1.1, 3.1.2)

**9a: Lang attribute on HTML**
- Check root HTML element for `lang` attribute
- Next.js: check `app/layout.tsx` for `<html lang="...">`
- Static HTML: check `index.html`
- PASS: `lang` attribute present with valid language code
- FAIL: no `lang` attribute
- Severity: HIGH (screen readers need this to use correct pronunciation)

**9b: Language changes in content**
- If content includes text in multiple languages, check for `lang` attribute on those sections
- PASS: multilingual content properly marked, or content is single-language
- N/A: single-language content
- Severity: LOW

## Report

```markdown
# Accessibility Audit — [Project Name]
**Date:** YYYY-MM-DD | **Level:** WCAG 2.1 [A/AA/AAA] | **Stack:** [detected]

## Score: X/Y checks passed — Grade [A-F]

| Category | Pass | Warn | Fail | N/A |
|----------|------|------|------|-----|
| Semantic HTML | X | X | X | X |
| Images & Media | X | X | X | X |
| Keyboard | X | X | X | X |
| Color & Contrast | X | X | X | X |
| Forms & Inputs | X | X | X | X |
| ARIA | X | X | X | X |
| Focus Management | X | X | X | X |
| Motion | X | X | X | X |
| Language | X | X | X | X |

## Critical Issues (must fix)
[FAIL items with WCAG criterion reference, file:line]

## Warnings
[WARN items]

## Recommendations
- Run axe-core browser extension for runtime contrast checking
- Test with screen reader (VoiceOver on Mac, NVDA on Windows)
- Test keyboard-only navigation through all workflows
```

**Grade:** A (90%+ pass), B (80%+), C (70%+), D (60%+), F (<60%). Based on applicable checks only (exclude N/A).

## Fix Phase (with --fix flag)

Fix in order of severity:

1. **CRITICAL:**
   - 3a: Add `:focus-visible` styles if focus outline removed
   - Add `lang` attribute to root HTML element

2. **HIGH:**
   - 1d: Replace `<div onClick>` with `<button>` (preserve styles)
   - 2a: Add `alt=""` placeholder to images missing alt (mark as TODO for descriptive text)
   - 3b: Remove positive tabindex values
   - 5a: Add `aria-label` to inputs missing labels (use placeholder text or field name as starting point)
   - 6d: Add `aria-label` to icon-only buttons (use icon name or action as label)
   - 9a: Add `lang="en"` (or detected language) to root HTML element

3. **MEDIUM:**
   - 1b: Add `<main>` wrapper if missing
   - 6a/6b: Fix invalid ARIA roles/attributes
   - 8a: Add `@media (prefers-reduced-motion: reduce)` disabling animations

4. **LOW:**
   - 6c: Remove redundant ARIA attributes
   - 5d: Add `autocomplete` to standard form fields

### Fix Rules:
- **Do NOT change visual appearance.** Accessibility fixes should be invisible to sighted users.
- **Do NOT invent alt text.** Add `alt=""` as placeholder and note "TODO: add descriptive alt text" in the report. Only a human who can see the image can write proper alt text.
- Run lint + build after fixes.

## Anti-Hallucination Rules

- **Contrast ratios cannot be precisely measured from code.** Do NOT claim "ratio is 3.2:1" unless you computed it from actual hex values. For color pairs found in code, say "potential low contrast — verify with browser DevTools."
- **Alt text quality cannot be assessed from code.** Check only that `alt` attribute EXISTS. Do NOT judge if the text is descriptive enough (e.g., `alt="image"` is technically present — flag it as WARN "generic alt text" but not FAIL).
- **Keyboard navigation cannot be fully verified from code.** Check for focus styles, tabindex, and escape handlers. Note: "Full keyboard audit requires manual testing."
- **Never fabricate WCAG criterion numbers.** Use only real WCAG 2.1 success criteria (e.g., 1.1.1, 2.4.7). If unsure of the criterion number, omit it rather than guessing.
- **File paths and line numbers must be real.** Every finding needs evidence from Grep/Glob/Read.
- **N/A checks reduce the total.** Grade calculation uses only applicable checks. A project with no forms scores N/A on Check 5, not FAIL.
- **This audit supplements, not replaces, automated tools.** Always recommend running axe-core, Lighthouse accessibility, or pa11y for runtime checks that code analysis cannot cover.
