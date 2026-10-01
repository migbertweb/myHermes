---
name: github
description: >-
  GitHub workflow umbrella: auth setup, PR lifecycle, code review, issue
  management, repo management, and release workflows. Absorbs the former
  github-auth, github-code-review, github-issues, github-pr-workflow, and
  github-repo-management skills.
version: 1.0.0
author: Hermes Agent (merged from 5 absorbed skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, git, auth, PR, code-review, issues, repo-management, releases, CLI, gh]
    supersedes:
      - github-auth
      - github-code-review
      - github-issues
      - github-pr-workflow
      - github-repo-management
---

# GitHub Umbrella

A consolidated GitHub workflow skill covering authentication, pull requests,
code review, issue tracking, repository management, and releases. This skill
replaces and extends the following now-archived narrow skills:

- **github-auth** — auth setup
- **github-code-review** — review workflow
- **github-issues** — issue management
- **github-pr-workflow** — PR lifecycle
- **github-repo-management** — clone/create/fork

Each former skill is now a labeled section below. See `references/` for the
complete original content of each absorbed skill.

---

## 1. Authentication (`github-auth`)

> **Legacy reference:** `references/github-auth-original.md`

### HTTPS Token Setup

```bash
# Create PAT at https://github.com/settings/tokens
# Store in git credential helper
gh auth login
```

### SSH Key Setup

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Add to ~/.ssh/id_ed25519.pub at https://github.com/settings/keys
```

### gh CLI Login

```bash
# Authenticate gh CLI
gh auth login

# Auth status check
gh auth status

# List tokens
gh auth token

# Logout
gh auth logout
```

### Environment Variable (for automation)

```bash
export GH_TOKEN=github_pat_...
# or set GITHUB_TOKEN
```

### Common auth pitfalls

- Token scope too narrow → `permissions` error — regenerate with `repo`, `workflow`
- SSH key format wrong → use `ed25519`, not RSA unless required
- `gh auth login` fails in TUI → use `--with-tokens < token.txt`

---

## 2. Pull Request Workflow (`github-pr-workflow`)

> **Legacy reference:** `references/github-pr-workflow-original.md`

### PR Lifecycle

#### Create a PR

```bash
# From current branch
git push -u origin feature-branch
gh pr create --title "Title" --body "Description" --base main
gh pr create -f  # auto-fill from commits
```

#### Review & Merge

```bash
# List PRs
gh pr list --state open
gh pr list --author @me

# View PR
gh pr view 42
gh pr view 42 --json title,body,reviews,additions,deletions

# Check review status
gh pr status

# Merge
gh pr merge 42 --squash  # or --merge, --rebase
gh pr merge 42 --auto    # auto-merge when CI passes

# Close without merge
gh pr close 42
```

### Branch Management

```bash
# Checkout PR locally
gh pr checkout 42

# Create branch from issue
gh issue develop 42 --branch-issue

# Delete remote branch after merge
git push origin --delete feature-branch
```

### CI / Checks

```bash
# View checks
gh pr checks 42

# Re-run failed checks
gh pr checks 42 --rerun-failed
```

---

## 3. Code Review (`github-code-review`)

> **Legacy reference:** `references/github-code-review-original.md`

### Review Process

1. **Fetch the PR diff:**
   ```bash
   gh pr diff 42
   gh pr view 42 --json files,additions,deletions
   ```

2. **Review inline:** Use `gh api` to post comments, or use `gh pr review`.

3. **Submit review:**
   ```bash
   # Approve
   gh pr review 42 --approve
   
   # Request changes
   gh pr review 42 --request-changes --body "Issues to fix"
   
   # Comment
   gh pr review 42 --comment --body "LGTM but consider..."
   ```

### CI Integration

- Check that required CI checks pass before approving
- Use `gh pr checks 42` to verify
- Block merge on failed required checks

### Review Checklist

- [ ] Code works as described in PR title/description
- [ ] No security issues (hardcoded secrets, SQL injection, XSS)
- [ ] Tests pass and new code has tests
- [ ] No dead code or unused imports
- [ ] Error handling is appropriate
- [ ] Logging / observability added
- [ ] Documentation updated if needed
- [ ] No regression in performance

### REST API Reviews

For advanced review workflows:

```bash
# Create a review with line-specific comments
gh api repos/:owner/:repo/pulls/42/reviews \
  --method POST \
  --field event=APPROVE \
  --field body="Looks good!" \
  --field comments='[{"path":"src/main.py","position":10,"body":"Nice fix!"}]'
```

---

## 4. Issues (`github-issues`)

> **Legacy reference:** `references/github-issues-original.md`

### Core Operations

```bash
# Create
gh issue create --title "Bug: login fails with empty email" \
  --body "Steps to reproduce..." \
  --label bug,priority-high \
  --assignee @me

# List
gh issue list --state open \
  --label bug \
  --assignee @me \
  --limit 20

# View
gh issue view 42
gh issue view 42 --json title,body,labels,assignees,comments
gh issue view 42 --comments  # includes comment thread

# Update
gh issue edit 42 \
  --add-label "in-progress" \
  --remove-label "needs-triage"

# Close
gh issue close 42
gh issue close 42 --reason "completed"  # or "not_planned"
# --reason only works with `gh issue close` (not `gh issue reopen`)
```

### Labels & Milestones

```bash
gh label list
gh label create bug --color FF0000 --description "Bug reports"
gh label delete bug

gh milestone list
gh milestone create "v2.0" --due-date 2026-12-31
```

### Issue Templates

```markdown
---
name: Bug Report
about: Create a report to help us improve
labels: bug
---

**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
A clear description of what you expected to happen.

**Environment:**
 - OS: [e.g. Ubuntu 24.04]
 - Version [e.g. 1.2.3]
```

### REST API Issues

```bash
# List issues with custom filters
gh api repos/:owner/:repo/issues \
  --method GET \
  --field state=open \
  --field labels=bug \
  --field sort=updated \
  --field direction=desc

# Create issue with body from file
gh api repos/:owner/:repo/issues \
  --method POST \
  --field title="Issue from API" \
  --field body="$(cat issue_body.md)"
```

### Issue to PR Linking

```bash
# In PR body, reference issue
gh pr create --body "Closes #42"
# Or close via commit message
git commit -m "Fix login validation (closes #42)"
```

---

## 5. Repository Management (`github-repo-management`)

> **Legacy reference:** `references/github-repo-management-original.md`

### Clone, Create, Fork

```bash
# List repos for current user
gh repo list

# List repos for a specific owner
gh repo list owner

# View detailed repo info
gh repo view owner/repo --json name,description,url,defaultBranch,createdAt,updatedAt,pushedAt,language,repositoryTopics,diskUsage

# Clone using gh
gh repo clone owner/repo
gh repo clone owner/repo -- --depth 1  # shallow clone

# Clone via git (when repo URL is known and gh is unavailable)
git clone https://github.com/owner/repo.git
git clone git@github.com:owner/repo.git

# Fork a repo
gh repo fork owner/repo --clone  # fork and clone locally

# Create repo
gh repo create my-new-repo --public --clone
gh repo create my-new-repo --private --push --source .
gh repo create org/my-repo --public  # under org

# Create from template
gh repo create my-repo --template owner/template-repo --public --clone

# Delete repo
gh repo delete owner/repo --confirm
```

### Releases

```bash
# List releases
gh release list --limit 10

# View release
gh release view v1.2.3
gh release view v1.2.3 --json tagName,body,createdAt,assets

# Create release
gh release create v1.2.3 --title "v1.2.3" \
  --notes "Release notes..." \
  --target main \
  dist/*.tar.gz

# Create prerelease
gh release create v2.0.0-beta1 --prerelease --title "v2.0.0-beta1" \
  --notes "Beta release"

# Upload assets to latest release
gh release upload v1.2.3 dist/*.deb

# Download release assets
gh release download v1.2.3 --pattern "*.tar.gz" --dir ./downloads

# Delete release
gh release delete v1.2.3 --yes
```

### Remotes

```bash
# Add upstream remote (for forks)
gh repo sync owner/repo  # sync fork with upstream
git remote add upstream https://github.com/upstream/repo.git

# Change remote URL
git remote set-url origin git@github.com:user/repo.git

# View remotes
git remote -v
```

### Search

```bash
# Search repos
gh search repos "topic:llm language:python" --limit 10
gh search repos "hermes" --owner owner

# Search code (needs token with access)
gh search code "def authenticate" --repo owner/repo
```

---

## Cross-cutting: Verification

After any auth change, verify:

```bash
gh auth status
gh repo list --limit 3
```

### Pitfall: `gh pr create --body` with shell-significant characters

The `--body` string is interpreted by the shell. Characters like backticks, parentheses, ampersands, pipes, and `$()` trigger command substitution or break parsing.

```bash
# BROKEN — body contains shell-significant chars
gh pr create --title "feat: big change" --body "Closes #42, refs $(git rev-parse HEAD)"

# WORKS — write body to a temp file first
cat > /tmp/body.md << 'EOF'
Closes #42

## Changes
- New feature with code-syntax in backticks
- Fixes (some edge-case in parens)
EOF
gh pr create --title "feat: big change" --body "$(cat /tmp/body.md)"
rm /tmp/body.md

# Also works — simple body with no special chars
gh pr create --title "feat: small fix" --body "Closes #42"
```

Even when the shell errors fire, the PR often still gets created — check the URL in stderr. If you see shell errors and the PR URL was emitted, the PR exists. Use `gh pr view` to verify.

### Multi-PR Delivery Workflow

When delivering multiple related improvements, organize them into sequential phases with independent branches and PRs to minimize merge conflicts:

1. **Plan phases** in a PLAN.md ordered by dependency (foundation > visuals > layout > features)
2. **One branch per phase**: `fix/<phase>`, `feat/<phase>`
3. **Build before every commit** (npm run build)
4. **Push branch > gh pr create > gh pr merge --squash --delete-branch**
5. **Switch back to main** and pull before starting the next phase
6. **Verify after merge**: `git log --oneline main` shows the chain

This avoids rebasing issues and keeps each PR focused. Do NOT report a phase as done until the PR is merged into main and verified locally.

### Sequential PR Rebasing (when branches share a base)

When multiple PRs were created from the same base commit (not chained), merging them requires rebasing each subsequent branch onto the updated `main`:

```bash
# 1. Merge PR #1
gh pr merge 1 --squash --delete-branch

# 2. Update local main
git checkout main && git pull origin main

# 3. Rebase PR #2's branch
git checkout feat/phase-2
git rebase main
# Resolve conflicts if any
git add <files>
git rebase --continue
git push --force-with-lease origin feat/phase-2

# 4. Merge PR #2 (now clean)
gh pr merge 2 --squash --delete-branch

# Repeat for PR #3, #4...
```

**Why rebase?** Each branch was created from the same point in time on main. When PR #1 merges, main advances, and the other branches lack those commits. `git rebase main` replays their commits on top of the new main tip. Conflicts mean the branches touched the same lines — resolve once during rebase, then the squash merge is trivial.

**If GitHub shows "merge conflicts" after rebase**, the PR page hasn't picked up the rebased commits yet. Force-push the branch:
```bash
git push --force-with-lease origin <branch-name>
```
Then retry `gh pr merge`.

**Rebase --continue with no editor**: When rebase prompts for a commit message during conflict resolution (e.g. after resolving and staging), `git rebase --continue --no-edit` may not be available on older git versions. Use:
```bash
git -c core.editor=true rebase --continue
```
This sets the editor to `true` (no-op) for that single command, skipping the editor prompt and using the default message.

**Force-push safety**: Always use `--force-with-lease` (not `--force`) when pushing a rebased branch. `--force-with-lease` checks that the remote branch hasn't been updated by someone else since you last fetched, preventing accidental overwrite of others' work.

### Dev → Main branch workflow

For projects with Docker/deploy auto-deploy on `main`:
- `main` — producción, deploy automático
- `dev` — desarrollo local, probar cambios antes de merge a producción
- Flujo: `git checkout dev` → desarrollar → test local → PR desde dev → merge a `main` → deploy
- Mantener `dev` sincronizada: `git checkout dev && git merge main && git push origin dev`
- Esto previene deploys rotos y da una superficie de testing local antes de producción.

### Pitfall: Never present aspirational results

Report only what is actually committed and merged into main. Describing planned work as if delivered erodes trust. If a change is on a branch but unmerged, say so. If its only in local uncommitted changes, say so. The user trusts real git history, not a narrative.
