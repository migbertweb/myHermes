# github-code-review (original content — absorbed into `github` umbrella)

## Original SKILL.md content

(Full content from archived github-code-review skill. Covers: review checklist (7 items: correctness, security, tests, dead code, error handling, observability, documentation), CI integration, REST API review posting, gh pr review commands.)

## Key commands preserved in umbrella

- `gh pr diff 42` / `gh pr view 42 --json files,...`
- `gh pr review 42 --approve` / `--request-changes` / `--comment`
- `gh api repos/:owner/:repo/pulls/42/reviews` (REST API reviews with inline comments)
