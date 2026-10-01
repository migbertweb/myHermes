---
name: obsidian-knowledge-management
description: Manage and structure a professional knowledge base in Obsidian, focusing on high-signal research, categorized folders, and interconnected notes.
---

# Obsidian Knowledge Management

Guidelines for transforming raw research and session outputs into a durable, structured Obsidian vault.

## Structuring Knowledge
Avoid flat lists of notes. Use a hierarchical folder structure to separate areas of life and work.
- **Project-based**: Create a root folder for the main domain (e.g., `Work-Freelancer/`) and subfolders for specific platforms or clients (e.g., `Upwork/`).
- **Indexing**: Always include an `index.md` in new category folders to act as a map and table of contents for that domain.
- **Atomic Notes**: Break down large research dumps into focused files (e.g., `01-strategy.md`, `02-security.md`) rather than one giant file.

## Content Standards
- **Direct and Actionable**: Use tables for comparisons, bullet lists for checklists, and clear headers.
- **Source Tracking**: When extracting info from the web, keep the context of where the info came from.
- **Interconnectivity**: Link related notes using `[[WikiLinks]]` to allow the user to traverse the knowledge graph.

## Workflow: Research → Vault
1. **Discovery**: Perform comprehensive web searches and extractions.
2. **Synthesis**: Group findings by theme (e.g., "Tricks", "Security", "Strategies").
3. **Implementation**: 
   - Create the directory structure using `mkdir -p`.
   - Write the `index.md` first.
   - Populate supporting notes with structured markdown.
   - For technical projects (e.g., software, infrastructure), create an `assets/` subfolder to store interactive diagrams, screenshots, or generated assets. Embed these using HTML or markdown links.
4. **Verification**: Confirm file existence and content layout.

## Pitfalls
- **Over-clustering**: Don't create 10 folders for 10 notes. Use folders for broad categories and files for specific topics.
- **Generic Titles**: Avoid `notes1.md`. Use descriptive, numbered titles like `01-profile-optimization.md`.