---
name: skill-creator
description: Crea, edita y optimiza skills de Hermes Agent.
version: 1.0.0
author: Anthropics
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [devops, skills, creator]
    related_skills: [validate-hermes-skill]
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:
- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run prompts with access to the skill
- Help the user evaluate the results both qualitatively and quantitatively
- Rewrite the skill based on feedback from the user's evaluation of the results
- Repeat until satisfied

## Creating a skill

### Capture Intent
Start by understanding the user's intent. Extract answers from conversation history or ask:
1. What should this skill enable the agent to do?
2. When should this skill trigger? (user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works?

### Write the SKILL.md
Fill in components:
- **name**: Skill identifier (lowercase, hyphens)
- **description**: When to trigger, what it does. Make descriptions "pushy" to avoid undertriggering.
- **compatibility**: Required tools, dependencies (optional)
- **body**: Instructions, procedures, patterns.

### Skill Writing Guide
- Keep SKILL.md under 500 lines.
- Reference files clearly with guidance on when to read them.
- Prefer imperative form in instructions.
