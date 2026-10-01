# github-issues (original content — absorbed into `github` umbrella)

## Original SKILL.md content

(Full content from archived github-issues skill. Covers: create/list/view/update/close issues, labels & milestones management, issue templates, REST API issue creation, issue-to-PR linking via "Closes #42" convention.)

## Key commands preserved in umbrella

- `gh issue create --title ... --body ... --label ... --assignee @me`
- `gh issue list --state open --label bug`
- `gh issue view 42 --json title,body,labels,assignees,comments`
- `gh issue edit 42 --add-label ... --remove-label ...`
- `gh issue close 42 --reason completed`
- `gh label list` / `gh label create bug --color FF0000`
- `gh milestone list` / `gh milestone create "v2.0"`
- `gh api repos/:owner/:repo/issues` (REST API)
