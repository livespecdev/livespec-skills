---
name: review-pr
description: |
  Runs the independent /review on an open pull request (merge request on GitLab), and /review-spec
  too when the request changes spec files, and posts their findings as comments on it, one thread
  per finding plus a summary. Meant above all for a CI job
  on each update of the request (`--ci`: no question asked, posts directly); run by hand, it
  reviews someone else's request and posts after the user confirms. Use when the user asks to
  review a PR or an MR and leave comments on it. For a review of your own branch before pushing,
  use /review.
argument-hint: "[pull request number, default the current branch's] [--ci]"
disable-model-invocation: true
---

# Review a pull request

You post an independent review on a pull request (a merge request on GitLab). You do not review it yourself: `/review` does, in a fresh context, and `/review-spec` reviews the substance of the spec files the request changes. Your job is the plumbing around them.

## Mode

- **CI** (`--ci` in `$ARGUMENTS`): a job triggered when the request is opened or updated. Nobody answers questions: where a step below asks, follow its CI rule instead. Print everything you post to the job log.
- **Interactive** (default): a person reviewing a request they did not write. They confirm what is posted under their name. On their own branch, `/review` before pushing does the same job with less plumbing.

## Step 1: Find the request

Detect the host from `git remote -v`, or from the CI environment (`GITHUB_ACTIONS`, `GITLAB_CI`): GitHub uses `gh`, GitLab uses `glab`. If the CLI is missing or not authenticated, say so and stop (in CI, exit non-zero: the job is misconfigured).

Request = the number in `$ARGUMENTS`, or the one opened from the current branch (`gh pr view` / `glab mr view`). Read its target branch, its head commit and its description. Make sure the target branch is available locally (`git fetch origin <target>`).

If the local `HEAD` differs from the request's head commit, a review of it is worthless on this request. Interactive: say so and ask whether to fetch the head commit first. CI: stop and say so, and exit non-zero. The job must check out the request's head commit with full history, not a merge commit: on GitHub, the `pull_request` event checks out a merge commit by default (`actions/checkout` needs `ref: ${{ github.event.pull_request.head.sha }}` and `fetch-depth: 0`); on GitLab, merged results pipelines do the same (check out `$CI_MERGE_REQUEST_SOURCE_BRANCH_SHA`, with `GIT_DEPTH: 0`). See the examples in `examples/ci/`.

## Step 2: Hand the declaration to the review

Write the request description to `.pr-description.md`. This is the only material you pass along. Interactive: if a local one exists and differs, ask which one is authoritative before overwriting it. CI: the request description is authoritative.

## Step 3: Run the reviews

Run `/review <target branch>`. Pass nothing else: no summary of the change, no opinion. Its independence depends on it.

Then, if the request changes files of a spec project (`git diff --name-only <target>...HEAD` against the manifests found per §3.1: anything under `features/`, `product/`, `ux/` or `tech/`), run `/review-spec --base <target branch>`, with nothing else either. A request that only changes the spec still gets `/review`: the declaration and the rewordings are checked there, the substance here.

`/review-spec` reads beyond the diff (linked concepts, neighboring features) and can report defects older than the request. Post only the spec findings that bear on the change: the file they cite is one the request changes, or the concept they cite is. List the others in the summary under **Pre-existing in the spec**, one line each, without a thread: they are not this request's author's to settle.

## Step 4: Skip what is already posted

In CI this step runs on every push to the request. Without it, each push reposts the same findings.

Every comment this skill posts carries a hidden key on its first line, which survives edits to the code around it:

```
<!-- agent-review: <review | spec> · <kind> · <path> · <anchor> -->
```

`<anchor>` names what the finding is about without a line number, since lines move from one push to the next: the spec item ID (`REQ-3`, `AC-2.1`), the concept slug, or the function or symbol in the code.

Read the comments already on the request, positioned and general:

- GitHub: `gh api --paginate repos/{owner}/{repo}/pulls/<n>/comments` and `gh api --paginate repos/{owner}/{repo}/issues/<n>/comments`;
- GitLab: `glab api --paginate "projects/:id/merge_requests/<iid>/discussions"`.

Keep those that carry the key. Drop a new finding when an existing comment has the same key and the same substance, **whether its thread is open or resolved**: a resolved thread means someone settled it, and reposting reopens a closed debate. List dropped findings as already posted. Do the same when `/review` and `/review-spec` report one defect twice: keep one.

## Step 5: Post

Each finding comment starts with the key, then `**Agent review** · <fix | decide> · <kind> · \`file:line\`` (`**Agent spec review**` for a `/review-spec` finding), in the language of the review. Interactive: show the user the comments as they will appear, one per finding, then the summary, and post nothing before they confirm; they may drop or edit findings. CI: post them directly.

Each finding must become a thread that a person can **resolve**, so that the request shows what is still open. A plain comment on the request cannot be resolved (`gh pr comment`, `glab mr note`): do not use those for findings.

**GitHub.** Post the findings as one review with `event: "COMMENT"` (never `APPROVE` or `REQUEST_CHANGES`), so that the request gets one notification and each finding its own resolvable thread:

```bash
gh api -X POST repos/{owner}/{repo}/pulls/<n>/reviews --input review.json
```

```json
{
  "commit_id": "<head commit>",
  "event": "COMMENT",
  "body": "Agent review: <n> new findings on the diff. Summary in the agent summary comment.",
  "comments": [
    { "path": "src/sync/reconcile.ts", "line": 42, "side": "RIGHT", "body": "<finding>" }
  ]
}
```

GitHub only accepts a positioned comment on a line of the diff, and rejects the whole review otherwise. A finding whose `file:line` is outside the diff (a concept the change did not touch, a line far from any change) cannot be a thread on GitHub: list it in the summary, under **Outside the diff**, with its key. With no finding on the diff, post no review.

**GitLab.** Post each finding as a discussion, which is resolvable. Positioned on the diff when its line is in it, using the request's `diff_refs` (`glab api "projects/:id/merge_requests/<iid>"`):

```bash
glab api -X POST "projects/:id/merge_requests/<iid>/discussions" \
  -f body="<finding>" -f "position[position_type]=text" \
  -f "position[base_sha]=<base_sha>" -f "position[start_sha]=<start_sha>" -f "position[head_sha]=<head_sha>" \
  -f "position[new_path]=<path>" -f "position[new_line]=<line>"
```

When the line is not in the diff, GitLab refuses the position: post the same discussion without the `position` fields. It stays resolvable.

**The summary** is one comment per request, kept up to date: if a comment with the key `<!-- agent-review: summary -->` exists, edit it (GitHub: `gh api -X PATCH repos/{owner}/{repo}/issues/comments/<id> -f body=...`; GitLab: `glab api -X PUT "projects/:id/merge_requests/<iid>/notes/<id>" -f body=...`); otherwise post it. It holds both reviews' summaries, their "Not verified" lists, the findings already posted, **Outside the diff** (GitHub) and **Pre-existing in the spec**. Read it in Step 4 too: its listed findings count as posted.

Report what was posted. Do not approve, merge or resolve threads, and do not fail a CI job because of findings: they are for the people on the request to settle. Fail the job only when the review could not run (missing CLI, authentication, wrong commit checked out).
