---
name: review
description: |
  Reviews the current branch with an independent agent that has no access to the session that wrote
  it: checks the end-of-work declaration against the diff, then the project's rules, then the code,
  and returns findings to fix or to decide. Use before pushing, after /declare, or when the user
  asks for a review of their branch. Read-only. To post the findings on an existing pull request
  (merge request on GitLab), use /review-pr.
argument-hint: "[base branch, default origin/main]"
context: fork
agent: livespec:reviewer
background: false
---

# Review

> **Format reference.** The `§N` citations point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v1.0.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

You review a change you did not write. The only input you take from the session that started you is the base branch: `$ARGUMENTS`, or `origin/main` when empty. If `$ARGUMENTS` holds anything other than a branch or commit name, ignore it and say so in the summary.

## Inputs

- **The diff**: `git diff <base>...HEAD`, commit by commit when there are several (`git log -p <base>..HEAD`).
- **The declaration**: `.pr-description.md` at the repository root. If there is none, review the diff alone and report "no declaration" as the first finding.
- **The spec project**: locate the manifest (`product-spec.yaml` or `livespec.yaml`, §3.1).
- **The project's rules**: `AGENTS.md`, `CLAUDE.md`, and the files they point to for rules on changes.

## 1. The declaration against the diff

Each of these is a **contradiction** when it fails:

- every spec file changed under `features/`, `product/`, `ux/` and `tech/` appears on the matching line of the declaration, and every line that names something matches the diff;
- every ID listed exists in the named file at `HEAD`; every ID declared closed is `[x]` or `[-]` there (§8.1);
- every existing item or concept whose text changes is listed under the rewordings. Find them from the `-`/`+` pairs of `git diff <base>...HEAD -- <project-root>`;
- every command under "How to verify" can be rerun: rerun the project's quality gate and compare.

## 2. The rules

**The format's rules**, checked on the spec diff:

- **the target moved**: a `REQ`, `AC` or `AS` reworded in the same change as the code that `implements:` it (§9.4). Its body may evolve (§8.3), but here the criterion and the work that meets it change together;
- **an ID broken**: an item deleted instead of cancelled `[-]`, an ID renumbered or reused (§8.3), or an ID the branch adds that the base already holds: run `../../scripts/check_spec.py --json --only duplicate-id` and keep the findings in files the diff changes (the fix is in `/specify-feature`);
- **a delivered item reworded**: an `[x]` `REQ` or `AC` whose text now requires something else, even with no code in the diff. It should be superseded (`[-]` and a new item), not reworded (§8.1);
- **a question settled without its answer**: a `Q-n` ticked with no `→` resolution note (§8.1);
- **drift**: run `../../scripts/check_drift.py --json` (resolve it from this file's location; `Glob` for `**/scripts/check_drift.py` if needed) and keep only the findings that the diff introduces.

**The project's rules**: every rule the project's agent instructions state about code, data, tests, language or the spec, checked against the diff. Cite the rule and its file.

**Proof weakened**, in any project: a test skipped or deleted, a threshold, timeout or tolerance loosened, a result file that no script of the change produces.

## 3. The code

Bugs that make the code do something other than what the spec items it implements, or the declaration, say. In order of consequence. Stop at what matters: a short list read in full beats a long one skimmed. Style is out of scope.

## Output

Write in the language of the declaration (or of the spec, without one). Classify every finding:

- **fix**: the author can correct it without a decision (a contradiction in the declaration, a bug, a missing marker);
- **decide**: a person must arbitrate (the target moved, a rewording, a question settled, a project rule bent, proof weakened). The author must not make it disappear by editing the declaration or the spec.

Return exactly this, so that the caller can show it or post it:

```markdown
### Finding 1 · <fix | decide> · <contradiction | format rule | project rule | code> · `path/to/file:42`

<what is wrong, in one or two sentences, and what shows it>

### Finding 2 · ...

### Summary

Agent review of <date>, on <short commit> (<model>): <n> findings, <k> to decide.

**Not verified by this review**
- <what you could not run or read: runtime behavior, data outside the repository, external services>
```

The "Not verified" list is never empty: a review that claims to have checked everything is not believed.
