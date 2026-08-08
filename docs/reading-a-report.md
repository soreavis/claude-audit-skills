# Reading a report

## The shape of a finding

Every finding is meant to carry three things:

1. **What is wrong**, in one sentence.
2. **Where**, as `path/to/file.ts:42`.
3. **Why it matters**, or what happens if you leave it.

A finding missing the line number is the one to distrust. The audits are written
to require it precisely so you can check them, and a claim you cannot open in an
editor is a claim nobody verified.

## Verdicts

`audit-security` and `audit-compliance` report a verdict per vector or dimension
rather than only listing failures. That distinction matters:

| Verdict | Meaning |
|---|---|
| Pass | Checked, nothing found |
| Fail | Checked, problem found, evidence given |
| Not applicable | The vector does not apply to this stack |
| Not checked | Skipped — out of scope, or a flag turned it off |

**Pass and Not checked are not the same thing.** A vector that was skipped
because of `--scope` or `--skip-deps` says nothing about your code. Read which
one you got before concluding you are clean.

`audit-all` reduces everything to SHIP / WARNINGS / DO-NOT-SHIP. Treat that as a
summary for a glance, not a decision. Read the findings underneath it.

## What to fix first

Not in report order. Order by what an attacker or a user actually reaches:

1. **Anything exposed to the internet and unauthenticated.** A public endpoint
   missing validation beats an internal script every time.
2. **Anything touching credentials or personal data.** These are the failures
   that are expensive after the fact rather than merely annoying.
3. **Anything blocking a user.** A keyboard trap or a form that fails on mobile
   is a user who leaves.
4. **Everything else.**

A single high-severity finding on a public route matters more than twenty
low-severity ones in a build script. The tools do not rank across audits, so
this part is yours.

## Using --fix

`--fix` applies changes after auditing. Before you use it:

- **Commit first.** Then the fixes are a reviewable diff instead of a mystery.
- **Read the diff.** A fix is a suggestion that was applied, not a proven-correct
  change. Some are mechanical and safe; some change behaviour.
- **Run your tests.** Nothing here runs them for you.

`--fix` is reasonable on formatting, missing attributes, and config. Be more
careful on auth and validation logic, where a plausible-looking fix can quietly
change who is allowed to do what.

## Limits worth knowing

**Results vary between runs.** These are instructions followed by a model, not a
fixed rule engine. The same audit on the same code can return a slightly
different set. If a finding matters, verify it directly rather than re-running
until it disappears.

**A clean report is not proof.** It means this pass found nothing, which is a
weaker statement than it looks. It is not a security certification, and no
compliance body will accept it.

**Some things cannot be checked by reading code.** Whether alt text describes the
image accurately, whether a permission model matches your intent, whether a
retention period matches your policy. Those need a person.

**Fixed findings can come back.** That is what `audit-diff` is for — run it
against your last report rather than trusting memory.
