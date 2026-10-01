## Description:

Persistent file-based planning for multi-step AI-agent work, using local planning files, lifecycle hooks, and helper scripts to preserve selected project context across long tasks.

This skill is ready for commercial/non-commercial use.

## Publisher:

[othmanadi](https://clawhub.ai/user/othmanadi)

### License/Terms of Use:

MIT-0

## Use Case:

Developers and agent users use this skill to organize multi-step work by maintaining task_plan.md, findings.md, and progress.md, with helper scripts for plan resolution, completion checks, attestation, and optional gated continuation.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: Lifecycle hooks read selected project planning files and place bounded excerpts into the agent context.

Mitigation: Treat injected planning content as project data, keep untrusted external material in findings.md, and use attestation for important, autonomous, or gated plans.

Risk: Explicit session replay can expose same-project transcript snippets to the current model context.

Mitigation: Use metadata mode for counts-only recovery and run replay only after explicit approval; treat replayed excerpts as untrusted bounded data.

Risk: Unpinned install commands can resolve to a changed release.

Mitigation: Prefer a pinned or ClawHub-reviewed install route over unpinned npx commands.

## Reference(s):

- [ClawHub skill page](https://clawhub.ai/othmanadi/skills/planning-with-files)
- [Manus context engineering reference](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- [Attestation locking and fallback](https://github.com/OthmanAdi/planning-with-files/blob/master/docs/attestation-locking.md)
- [Performance notes](https://github.com/OthmanAdi/planning-with-files/blob/master/docs/perf-notes.md)

## Skill Output:

**Output Type(s):** [Markdown, Shell commands, Configuration, Guidance]

**Output Format:** [Markdown planning files with inline shell or PowerShell commands]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [Writes local planning files and may emit bounded hook context; no network upload path is disclosed.]

## Skill Version(s):

3.18.0 (source: server release and skill metadata)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
