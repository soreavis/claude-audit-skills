# Changelog

All notable changes to this plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this plugin adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `build/validate.py` — a single, locally-runnable validation gate covering manifest JSON validity, plugin-source resolution, and real YAML parsing of every skill's frontmatter (name + description required).
- **Anti-hallucination guardrail in CI.** The gate now fails any skill that ships without an anti-hallucination rules heading and evidence-grounding language, so the suite's core promise — every finding traces to real `file:line` evidence — can't silently drift as skills are added.

### Changed
- CI `validate.yml` now runs `build/validate.py` instead of duplicating manifest checks inline.
- README restructured for clarity and correct attribution (independence notice, `Created by`, `MIT © 2026` license line); documents the anti-hallucination CI gate. `CONTRIBUTING.md` documents `build/validate.py` and the mandatory anti-hallucination section for new audits.

## [0.1.0] - 2026-06-14

### Added
- Initial release as a Claude Code plugin marketplace bundling 13 audit skills under one `audit` plugin.
- Skills (all namespaced `/audit:<name>`):
  - `all` — orchestrator: runs the suite sequentially and merges into one combined scorecard (SHIP / WARNINGS / DO NOT SHIP), with `quick` / `standard` / `full` tiers and `--include`/`--skip`/`--scope`/`--fix`/`--report`.
  - `security` — 33-vector attack-surface audit.
  - `deep` — code quality + security + injection surface (3 parallel agents).
  - `deps` — dependency health (licenses, outdated, unused, duplicates, bundle size, vulnerabilities).
  - `compliance` — GDPR / ISO 27001:2022 / ISO 9001:2015 (+ optional HIPAA / SOC 2 / PCI), 7 dimensions.
  - `tech-stack` — stack-convention conformance, 8 checks.
  - `forms` — 38-point form-hardening audit.
  - `a11y` — WCAG 2.1 AA, 29 checks.
  - `seo` — SEO + technical SEO + GEO.
  - `deploy` — pre-deploy production-readiness checklist.
  - `responsive` — responsive / mobile optimization across viewports.
  - `hallucination` — 46-vector LLM fabrication-risk audit.
  - `diff` — compare two audit reports (fixed / new / regressed / deferred).
- Each skill is report-only by default; remediation skills take an opt-in `--fix`.
- In-skill command references updated from the previous standalone `/audit-<name>` form to the plugin-namespaced `/audit:<name>` form.
- `audit-all` reworked for the bundled model: resolves sibling skills from within the plugin (no separate install step), expanded to orchestrate the full bundled set.

### Notes
- This suite was previously distributed as separate per-skill repositories. It is now consolidated into one marketplace monorepo to eliminate cross-skill drift and simplify installation.
