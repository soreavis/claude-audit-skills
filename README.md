# claude-audit-skills

**A pre-ship audit suite for [Claude Code](https://claude.com/claude-code) — 13 skills under one plugin. Run any audit on its own, or `/audit:all` to orchestrate the whole suite into a single combined scorecard.**

[![validate](https://github.com/soreavis/claude-audit-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/soreavis/claude-audit-skills/actions/workflows/validate.yml)
![License](https://img.shields.io/badge/license-MIT-blue)
![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-f97a5e)
![Skills](https://img.shields.io/badge/skills-13-blue)

---

This is a Claude Code **plugin marketplace**. The whole suite installs as one plugin (`audit`); every audit is then an individually invocable, namespaced command (`/audit:security`, `/audit:a11y`, …). One install, no per-repo sprawl, no drift between siblings.

## The audits

| Command | Focus |
|---|---|
| `/audit:all` | **Orchestrator** — runs the suite in sequence, merges into one scorecard with a SHIP / WARNINGS / DO NOT SHIP verdict |
| `/audit:security` | Attack surface — 33 vectors (OWASP, auth, API, client-side, AI) |
| `/audit:deep` | Code quality + security + injection surface (3 parallel agents) |
| `/audit:deps` | Dependency health — licenses, outdated, unused, duplicates, bundle size, vulns |
| `/audit:compliance` | Regulatory — GDPR, ISO 27001:2022, ISO 9001:2015 (+ HIPAA/SOC2/PCI), 7 dimensions |
| `/audit:tech-stack` | Stack-convention conformance — 8 checks, adapts to your detected stack |
| `/audit:forms` | Form hardening — 38-point spam/bot/security checklist |
| `/audit:a11y` | Accessibility — WCAG 2.1 AA, 29 checks |
| `/audit:seo` | SEO + technical SEO + GEO (generative-engine optimization) |
| `/audit:deploy` | Pre-deploy production-readiness checklist |
| `/audit:responsive` | Responsive / mobile optimization across viewports |
| `/audit:hallucination` | LLM fabrication-risk audit — 46 vectors for prompts, AI-integration code, and generated content |
| `/audit:diff` | Compare two audit reports — what improved, regressed, or is new |

Every audit is **report-only by default**; the ones that can remediate take an opt-in `--fix`. All findings carry `file:line` evidence, and each skill enforces its own anti-hallucination rules (no invented identifiers, evidence-mandated findings).

## Install

```text
# 1. Add this marketplace (Git-based; owner/repo shorthand):
/plugin marketplace add soreavis/claude-audit-skills

# 2. Install the suite:
/plugin install audit@soreavis-skills

# 3. Activate without restarting:
/reload-plugins
```

Then run any audit, e.g.:

```text
/audit:security --fix
/audit:all --tier=full --scope=src/ --report
/audit:a11y
```

Team setup (project `.claude/settings.json`):

```json
{
  "extraKnownMarketplaces": {
    "soreavis-skills": {
      "source": { "source": "github", "repo": "soreavis/claude-audit-skills" }
    }
  },
  "enabledPlugins": {
    "audit@soreavis-skills": true
  }
}
```

## `/audit:all` tiers

| Tier | Audits | When |
|---|---|---|
| `quick` | security, deploy | Fast sanity check / MVP |
| `standard` (default) | security, deploy, forms, a11y, responsive | Most public-facing web projects |
| `full` | hallucination, security, deep, deps, compliance, tech-stack, forms, a11y, seo, responsive, deploy | Pre-launch of a paid / regulated / customer-facing product |

```text
/audit:all                                   # standard tier
/audit:all --tier=full --skip=hallucination  # everything except the AI-risk pass
/audit:all --tier=quick --include=a11y       # compose tier + include/skip
```

(`/audit:diff` isn't part of a run-all — it compares two existing reports. Run `/audit:all` twice across a fix sprint, then `/audit:diff`.)

## Layout

```
claude-audit-skills/
├── .claude-plugin/
│   └── marketplace.json          # lists the `audit` plugin
└── plugins/
    └── audit/
        ├── .claude-plugin/plugin.json
        └── skills/
            ├── all/SKILL.md       → /audit:all
            ├── security/SKILL.md  → /audit:security
            ├── deep/SKILL.md      → /audit:deep
            └── …                  (13 skills total)
```

## Requirements

- [Claude Code](https://claude.com/claude-code)
- Your target project checked out locally — the skills use `Grep` / `Glob` / `Read` against the codebase
- For `--report` / `--fix` reports: a `_local/` directory (skills create one if needed)

No external services. No API keys. Pure methodology + Claude Code execution.

## License

[MIT](./LICENSE) — copy it, ship it, improve it.

## Acknowledgments

Built with [Claude Code](https://claude.com/claude-code). Vector and checklist catalogs assembled from OWASP, WCAG 2.1, web.dev, GDPR / ISO 27001:2022, and real shipping experience.
