# Claude Audit Skills Companion

[![validate](https://github.com/soreavis/claude-audit-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/soreavis/claude-audit-skills/actions/workflows/validate.yml)
![License](https://img.shields.io/badge/license-MIT-blue)
![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-f97a5e)
![Skills](https://img.shields.io/badge/skills-13-blue)

A pre-ship audit suite for [Claude Code](https://claude.com/claude-code): 13 skills under one plugin. Run any audit on its own, or `/audit:audit-all` to orchestrate the whole suite into a single combined scorecard with a SHIP / WARNINGS / DO NOT SHIP verdict.

It installs as a Claude Code **plugin marketplace**. The whole suite installs as one plugin (`audit`); every audit is then an individually invocable, namespaced command (`/audit:audit-security`, `/audit:audit-a11y`, …). One install, no per-repo sprawl, no drift between siblings.

> [!IMPORTANT]
> **An independent project, built and maintained by Julian Soreavis.** Not affiliated with, endorsed by, or sponsored by Anthropic or any of the standards bodies whose catalogs it references (OWASP, W3C / WCAG, ISO, and others). Product names, trademarks, and standards are used here only to describe what each audit checks. Use at your own risk.

## The audits

| Command | Focus |
|---|---|
| `/audit:audit-all` | **Orchestrator** — runs the suite in sequence, merges into one scorecard with a SHIP / WARNINGS / DO NOT SHIP verdict |
| `/audit:audit-security` | Attack surface — 33 vectors (OWASP, auth, API, client-side, AI) |
| `/audit:audit-deep` | Code quality + security + injection surface (3 parallel agents) |
| `/audit:audit-deps` | Dependency health — licenses, outdated, unused, duplicates, bundle size, vulns |
| `/audit:audit-compliance` | Regulatory — GDPR, ISO 27001:2022, ISO 9001:2015 (+ HIPAA/SOC2/PCI), 7 dimensions |
| `/audit:audit-tech-stack` | Stack-convention conformance — 8 checks, adapts to your detected stack |
| `/audit:audit-forms` | Form hardening — 38-point spam/bot/security checklist |
| `/audit:audit-a11y` | Accessibility — WCAG 2.1 AA, 29 checks |
| `/audit:audit-seo` | SEO + technical SEO + GEO (generative-engine optimization) |
| `/audit:audit-deploy` | Pre-deploy production-readiness checklist |
| `/audit:audit-responsive` | Responsive / mobile optimization across viewports |
| `/audit:audit-hallucination` | LLM fabrication-risk audit — 46 vectors for prompts, AI-integration code, and generated content |
| `/audit:audit-diff` | Compare two audit reports — what improved, regressed, or is new |

Every audit is **report-only by default**; the ones that can remediate take an opt-in `--fix`. Every skill carries an anti-hallucination section requiring `file:line` evidence and forbidding invented identifiers. CI checks that the section is present; it does not verify that a given audit run obeyed it.

## Install

```text
# 1. Add this marketplace (Git-based; owner/repo shorthand):
/plugin marketplace add soreavis/claude-audit-skills

# 2. Install the suite:
/plugin install audit@soreavis-skills

# 3. Activate without restarting (if the install summary says to):
/reload-plugins
```

Then run any audit, e.g.:

```text
/audit:audit-security --fix
/audit:audit-all --tier=full --scope=src/ --report
/audit:audit-a11y
```

Each command also has a shorter bare alias — `/audit-security`, `/audit-all`, and so on — which works as long as no other command already claims that name.

### For a team or a repo

Add this to a project's `.claude/settings.json` and everyone who trusts the folder gets the marketplace and plugin:

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

## `/audit:audit-all` tiers

| Tier | Audits | When |
|---|---|---|
| `quick` | security, deploy | Fast sanity check / MVP |
| `standard` (default) | security, deploy, forms, a11y, responsive | Most public-facing web projects |
| `full` | hallucination, security, deep, deps, compliance, tech-stack, forms, a11y, seo, responsive, deploy | Pre-launch of a paid / regulated / customer-facing product |

```text
/audit:audit-all                                   # standard tier
/audit:audit-all --tier=full --skip=hallucination  # everything except the AI-risk pass
/audit:audit-all --tier=quick --include=a11y       # compose tier + include/skip
```

(`/audit:audit-diff` isn't part of a run-all — it compares two existing reports. Run `/audit:audit-all` twice across a fix sprint, then `/audit:audit-diff`.)

## Layout

```
claude-audit-skills/
├── .claude-plugin/
│   └── marketplace.json          # lists the `audit` plugin
├── build/
│   └── validate.py               # CI gate — manifests, YAML frontmatter, anti-hallucination guardrail
└── plugins/
    └── audit/
        ├── .claude-plugin/plugin.json
        └── skills/
            ├── audit-all/SKILL.md       → /audit:audit-all
            ├── audit-security/SKILL.md  → /audit:audit-security
            ├── audit-deep/SKILL.md      → /audit:audit-deep
            └── …                        (13 skills total)
```

## Requirements

- [Claude Code](https://claude.com/claude-code)
- Your target project checked out locally — the skills use `Grep` / `Glob` / `Read` against the codebase
- For `--report` / `--fix` reports: a `_local/` directory (skills create one if needed)

No external services. No API keys. Pure methodology + Claude Code execution.

## Documentation

Detailed guides in [`docs/`](docs/):

- [Getting started](docs/getting-started.md) — install, first audit, where reports go
- [The audits](docs/the-audits.md) — what each of the 13 checks, and which one you want
- [Reading a report](docs/reading-a-report.md) — verdicts, what to fix first, and the limits
- [Troubleshooting](docs/troubleshooting.md) — commands missing, wrong stack detected, slow runs

## Contributing

Bug reports, new audits, and extra checks are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Report security issues privately per [SECURITY.md](SECURITY.md).

## Acknowledgments

Vector and checklist catalogs assembled from OWASP, WCAG 2.1, web.dev, GDPR / ISO 27001:2022, and real shipping experience.

## Credits

- **Created by**: [Julian Soreavis](https://github.com/soreavis)

## License

MIT © 2026 Julian Soreavis — see [LICENSE](LICENSE).
