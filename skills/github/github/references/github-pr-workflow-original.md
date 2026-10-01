# github-pr-workflow (original content — absorbed into `github` umbrella)

## Original SKILL.md content

(Full content from archived github-pr-workflow skill. Covers: entire PR lifecycle — creating, viewing, listing, checking status, merging (squash/merge/rebase/auto), closing, branch management, CI checks.)

## Key commands preserved in umbrella

- `git push -u origin feature-branch`
- `gh pr create --title ... --body ... --base main`
- `gh pr list --state open`
- `gh pr view 42 --json title,body,reviews,additions,deletions`
- `gh pr status`
- `gh pr merge 42 --squash` / `--merge` / `--rebase` / `--auto`
- `gh pr close 42`
- `gh pr checkout 42`
- `gh pr checks 42` / `gh pr checks 42 --rerun-failed`
