---
name: finalize
description: |
  Takes an implemented spec feature to production-ready: adds or updates tests, runs the project's
  CI/quality gate, delegates spec reconciliation to /sync, then commits the code and the spec together. Use when the
  user signals the work is finished ("done", "implementation done", "ready to finalize", "need tests",
  "run CI"); it chains /sync and offers /declare.
  Not for active implementation (/implement), debugging, or spec-only updates (/sync directly).
argument-hint: <feature-slug>
---

# Finalize Work

> **Format reference.** The `§N` citations point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v1.0.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

Complete the production-readiness workflow for a feature: **test → check → reconcile → commit**. Use this once the feature's behavior is implemented and you need it shippable.

## Step 1: Verify implementation status

`Read` `features/**/{slug}.md`. Confirm the acceptance criteria are implemented (their code exists and carries `implements:` markers, §9.4); they need not be tested yet. If some ACs are still genuinely unimplemented (`- [ ]` with no code), tell the user what is missing and ask whether to proceed anyway.

## Step 2: Add or update tests

Identify coverage gaps against the feature's acceptance criteria:

- Review each AC and check existing test files for related coverage.
- Add unit tests for new functions/components, integration tests for the feature's workflows, and E2E tests where the project uses them.
- Cover the edge-case, validation, and error-handling ACs, not just the happy path.
- Update existing tests affected by the change.

You MAY mirror the spec link in test names or comments (e.g. a test named after `log-completion#AC-2.3`), so the test reads as the executable form of that criterion. Summarize what test coverage you added.

## Step 3: Run the quality gate

Find and run the project's CI command:

- `package.json` scripts: `npm run ci`, `test:ci`, `lint && test`, `check`.
- A `Makefile`: `make ci`, `make test`, `make check`.
- Failing that, read `.github/workflows/` and run the equivalent steps locally.

Run the most comprehensive check. If it fails, fix the issues and re-run. Do not proceed to commit until it passes. Note anything you fixed.

## Step 4: Reconcile the spec

Delegate to `/sync` for this feature to reconcile the spec files with what was actually built:

- Confirm the right ACs are `[x]` (and any dropped one is `[-]` with a reason).
- Add or sharpen `## Tech` notes for decisions made during implementation.
- Record answered `Q` and lifted `LIM` as resolution notes (`→ `, §8.1).
- Promote any standing rule discovered during the work to a concept for the user to review.

Reconcile before committing, so the commit carries the spec as it now stands. If `/sync` is unavailable, do those edits directly on the local files (this is plain `Edit` on `features/` and concept files; there is no server to push to).

## Step 5: Commit

**Only after the gate passes and the spec is reconciled.**

1. Review what will be committed: implementation files, test files, the feature file as `/sync` left it, and any concept files the user approved. Leave out nothing `/sync` edited: an uncommitted spec edit stalls `/declare`.
2. Match the project's commit style (read recent `git log`).
3. Git safety:
   - Never update git config; never use `--no-verify` or skip hooks.
   - Stage specific files; avoid `git add -A`.
   - Create a new commit; do not amend unless the user asks.
   - If you are on the default branch, create a feature branch first.
4. **Commit attribution**: the commit MUST NOT mention Claude, Claude Code, or any AI agent as author, committer, or contributor. No `Co-Authored-By` AI trailer, no "Generated with" line. The human is the sole author of record (per `CLAUDE.md`).

## Step 6: Summary

Summarize conversationally: tests added for what, the gate passing, what `/sync` reconciled, and the commit hash. The diff is the record. There is no feature status to set and no batch to advance: sequencing the next piece of work is a git/issue-tracker concern, outside the spec (§1).

Then offer the hand-over: `/declare` writes the pull request description from the branch, and `/review` has an independent agent check it against the diff before the user pushes.

## Handling failures

- **Test failures**: fix the implementation or the tests, re-run; do not move to the gate until tests pass.
- **Gate failures**: address lint/type/other issues, re-run; do not commit until green.
- **Pre-commit hook failures**: fix what the hook raised, create a new commit (do not amend).
- **Reconciliation issues**: complete the file edits directly before committing, and report anything you could not reconcile.
