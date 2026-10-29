---
name: declare
description: |
  Writes the end-of-work declaration of the current branch: the pull request description (merge
  request on GitLab),
  stating what the change implements and changes in the spec, what was checked, what to watch and
  what is left, into `.pr-description.md`, then sets it on the request with `gh` or `glab` once
  the user confirms. Use when work on a branch is finished, before a pull
  request is opened or updated, or when the user says "done", "open the PR", "open the MR",
  "write the declaration". Not for committing (/finalize) or reviewing (/review, /review-pr).
argument-hint: "[base branch, default origin/main]"
---

# Declare

> **Format reference.** The `§N` citations point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v1.0.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

You state what this branch does, what you checked, what you left undone and what you are unsure about. The declaration is testimony: a reviewer, person or agent, checks it against the diff (`/review`, `/review-pr`). Write it so that a false claim is easy to catch, not so that the work looks finished.

Run this skill in the session that did the work: only that session knows what it ran and what it assumed. The declaration describes one change. It never goes into the spec files (§1): it lives in the pull request description.

## Step 1: Scope

Base = `$ARGUMENTS` or `origin/main`. Read `git log --oneline <base>..HEAD`, `git diff --stat <base>...HEAD` and `git status --short`. If there are uncommitted changes, say so and ask whether they belong to the change before going on.

Locate the spec project (`product-spec.yaml` or `livespec.yaml`, §3.1). Never assume a path.

## Step 2: Template

Use the project's pull request template when there is one: `.gitlab/merge_request_templates/Default.md`, `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md` or `docs/pull_request_template.md`. Otherwise use [`template.md`](template.md) next to this file. Write in the template's language. Keep every section; an empty one reads "none" (or the template's equivalent) rather than being dropped.

## Step 3: Specification

Read `git diff <base>...HEAD -- <project-root>`. Qualify every ID with its file slug (`log-completion#AC-2.3`, §8.3), written as a relative Markdown link to the file. Fill each line:

| Line | What goes there |
|---|---|
| Implemented by the code | The `REQ` and `AC` the code of the branch satisfies, from the `implements:` markers it adds or moves (§9.4), otherwise from the feature it works on. |
| Features changed | Items added, or whose checkbox goes to `[x]` or `[-]`, under `features/`; `UX-n` and `TECH-n` directions added or superseded. |
| Concepts changed | Files added or changed under `product/`, `ux/`, `tech/`, one line per layer. They are product decisions (§6): the reviewer reads them with the features that cite them. |
| Questions | `Q-n` ticked, with their `→` resolution note (§8.1), and those the branch brings evidence to while leaving them open. |
| Rewordings | Every existing item or concept whose text changes, whatever its checkbox. Find them from the `-`/`+` pairs of the spec diff. Bodies are mutable and git is their history (§8.3), so this line is the only place a reviewer sees them. Never leave one out: a criterion rewritten to fit the work is the first thing a reviewer looks for. |
| Choices the spec does not cover | Every choice the feature, its `## UX`/`## Tech` sections and the concepts did not settle: a threshold, a library, a format, a skipped case. |

## Step 4: Checks

Find and run the project's quality gate as `/finalize` does (`package.json` scripts, `Makefile`, CI workflow files). Under "How to verify", list only the commands you actually ran in this session, with their outcome. A test you did not run is not listed: put it under "Out of scope and follow-ups" if it should be run.

## Step 5: Project rules

Read the project's agent instructions (`AGENTS.md`, `CLAUDE.md`) and the files they point to for rules on changes. If this session did something they forbid, stop and tell the user instead of writing the declaration.

## Step 6: Prose

Short, one point per line:

- **Points of attention**: what you assumed without evidence, what you tested on one case only, what would break first. This is the section a reviewer reads. "None" there is a claim of full confidence: give the reason, or fill it.
- **Out of scope and follow-ups**: what is deliberately not done, and any spec change the work suggests but does not make.

## Step 7: Write

Check that `.pr-description.md` is git-ignored (`git check-ignore`). If it is not, propose the `.gitignore` line to the user. Fill the template into `.pr-description.md`. If the file exists, rewrite it in full rather than appending: one declaration per change, edited in place.

**Do not tick a checklist** if the template has one: it records what the person who opens the request did.

The file is the working copy of the declaration even when you publish it: `/review` reads it there.

## Step 8: Publish

Show the declaration. Then detect the host from `git remote -v`: GitHub uses `gh`, GitLab uses `glab`. A self-hosted GitLab may not say so in its URL: match the remote host against `glab auth status`. If the host is still unclear, ask the user. If the CLI is missing or not authenticated, say so and go to Step 9.

Find the request opened from the current branch (`gh pr view` / `glab mr view`), then propose the one action that fits and wait for the user's answer:

| Situation | Proposal |
|---|---|
| A request exists | Replace its description: `gh pr edit <id> --body-file .pr-description.md` / `glab mr update <id> --description "$(cat .pr-description.md)"`. |
| No request, the branch is pushed and its upstream is at `HEAD` | Open it as a draft against the base branch (without its remote prefix): `gh pr create --draft --base <base> --title "<title>" --body-file .pr-description.md` / `glab mr create --draft --target-branch <base> --title "<title>" --description "$(cat .pr-description.md)"`. Propose the title (default: the subject of the only commit). If `/review` has not run on this declaration, offer it first: an open request is visible to others. |
| No request, the branch is not pushed or is behind | Publish nothing. Go to Step 9. |

Publish nothing without the user's confirmation, and never push: pushing stays the user's act.

## Step 9: Hand over

If nothing was published, tell the user why, and how to do it: paste `.pr-description.md` into the request description, or use the command above once the branch is pushed.

Then point to the review: `/review` for an independent agent review before pushing, or `/review-pr` once the request exists.
