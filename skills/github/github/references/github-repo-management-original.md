# github-repo-management (original content — absorbed into `github` umbrella)

## Original SKILL.md content

(Full content from archived github-repo-management skill. Covers: repo listing, cloning, forking, creating (from scratch, from template, under org, with --push --source), deleting, releases, remotes, search.)

## Key commands preserved in umbrella

- `gh repo list` / `gh repo list owner`
- `gh repo view owner/repo --json name,description,url,defaultBranch,...`
- `gh repo clone owner/repo`
- `gh repo fork owner/repo --clone`
- `gh repo create my-repo --public --clone`
- `gh repo create my-repo --template owner/template --public --clone`
- `gh repo delete owner/repo --confirm`
- `gh release list` / `gh release view v1.2.3` / `gh release create v1.2.3`
- `gh release upload v1.2.3 dist/*.deb` / `gh release download v1.2.3`
- `gh release delete v1.2.3 --yes`
- `gh repo sync owner/repo`
- `gh search repos "topic:llm language:python"`
