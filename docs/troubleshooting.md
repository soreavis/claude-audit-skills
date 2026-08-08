# Troubleshooting

## The commands do not appear

Type `/audit:` and see whether anything is offered.

If not, in order:

1. Run `/reload-plugins`. New plugins do not always register until the plugin
   list is reloaded.
2. Check the install actually completed:
   `/plugin marketplace add soreavis/claude-audit-skills` then
   `/plugin install audit@soreavis-skills`.
3. Restart Claude Code.

## The bare alias does not work

Each audit has a short form — `/audit-security` alongside
`/audit:audit-security`. The short form only works while no other command claims
that name. If you have another plugin installed with overlapping names, one of
them wins and it may not be this one.

The namespaced form (`/audit:audit-security`) is unambiguous. Use it if the
short one behaves unexpectedly.

## It audited the wrong thing

Most audits detect your stack before checking anything, and detection can land
on the wrong answer in a monorepo or a project with several frameworks present.

Use `--scope` to point at the part you mean:

```text
/audit:audit-security --scope=apps/web/
```

`--scope` is also the fix for an audit that is taking too long — narrowing the
directory is the main lever you have.

## It is slow, or uses more tokens than expected

`--tier=full` runs eleven audits over a large part of the codebase. That is
inherently expensive. Options, roughly in order of effect:

- `--scope=<dir>` — the biggest lever by far.
- A smaller tier — `quick` is two audits rather than eleven.
- `--skip=<name>` — drop the ones you do not need this time.
- `--skip-deps` on `audit-security` if you have already run `audit-deps`.

## Two audits disagree

`audit-security` and `audit-deep` overlap on OWASP, and can report the same
issue differently or one may find something the other misses. That is expected —
they read the code separately.

When they conflict, open the file and decide yourself. Neither is authoritative.

## A finding looks wrong

It might be. Open the `file:line` and check.

If the evidence does not support the claim, the finding is wrong and you should
ignore it. That is not a rare event and it is not a reason to distrust
everything — it is why every audit is written to cite a line in the first place.

Findings with no line number at all deserve more suspicion than findings whose
line number turns out to be a false positive.

## --fix changed something it should not have

Revert it: `git checkout -- <file>`, or `git reset --hard` if you committed
before running, which is the reason to commit before running.

Then re-run without `--fix` and apply the parts you agree with by hand. Fixes to
auth and validation logic deserve that treatment as a rule.

## Reports are not being written

`--report` writes to `_local/reports/`. If nothing appears, check the directory
exists and is writable, and that you actually passed the flag — it is off by
default.

Add `_local/` to `.gitignore` if it is not there. Reports quote your source, and
committing them to a public repo publishes code you may not have meant to.

## audit-diff cannot find a report to compare

It reads from `_local/reports/`. It needs two reports of the same type — two
`security-audit-*.md` files, not one security and one a11y.

If you have only ever run with `--report` once, there is nothing to diff yet.
