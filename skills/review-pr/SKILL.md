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

If the local `HEAD` differs from the request's head commit, a review of it is worthless on this request. Interactive: say so and ask whether to fetch the head commit first. CI: stop and say so; the job must check out the request's head commit, not a merge commit.

## Step 2: Hand the declaration to the review

Write the request description to `.pr-description.md`. This is the only material you pass along. Interactive: if a local one exists and differs, ask which one is authoritative before overwriting it. CI: the request description is authoritative.

## Step 3: Run the reviews

Run `/review <target branch>`. Pass nothing else: no summary of the change, no opinion. Its independence depends on it.

Then, if the request changes files of a spec project (`git diff --name-only <target>...HEAD` against the manifests found per §3.1: anything under `features/`, `product/`, `ux/` or `tech/`), run `/review-spec --base <target branch>`, with nothing else either. A request that only changes the spec still gets `/review`: the declaration and the rewordings are checked there, the substance here.

`/review-spec` reads beyond the diff (linked concepts, neighboring features) and can report defects older than the request. Post only the spec findings that bear on the change: the file they cite is one the request changes, or the concept they cite is. List the others in the summary under **Pre-existing in the spec**, one line each, without a thread: they are not this request's author's to settle.

## Step 4: Skip what is already posted

Read the request's existing comments (`gh pr view --comments` / `glab mr view --comments`). Drop a finding already posted by an earlier agent review on the same file and line with the same substance, and list it as already posted. Do the same when `/review` and `/review-spec` report one defect twice: keep one. In CI this step runs on every update of the request: without it, each push reposts the same findings.

## Step 5: Post

Each finding comment starts with `**Agent review** · <fix | decide> · <kind> · \`file:line\`` (`**Agent spec review**` for a `/review-spec` finding), in the language of the review. Interactive: show the user the comments as they will appear, one per finding, then one summary per review, and post nothing before they confirm; they may drop or edit findings. CI: post them directly.

Post each one as its own comment so that it becomes a thread resolved by a fix or an answer:

- GitHub: `gh pr comment <id> --body "<comment>"`;
- GitLab: `glab mr note <id> --message "<comment>"`.

Report what was posted. Do not approve, merge or resolve threads, and do not fail a CI job because of findings: they are for the people on the request to settle.
