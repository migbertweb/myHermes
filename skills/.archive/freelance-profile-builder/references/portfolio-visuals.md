# Portfolio Visual Assets for Upwork

Visual content (screenshots, diagrams, infographics) significantly increases conversion on Upwork portfolio entries. This reference covers generating professional images using available tools.

## Image Types & When to Use

| Type | Best For | Tool |
|------|----------|------|
| **Architecture Diagram** | System structure, infrastructure, cloud/DevOps | `architecture-diagram` skill (dark HTML/SVG) |
| **Infographic** | Project overview, tech stack + features showcase | `baoyu-infographic` skill (image generation) |
| **Screenshot** | Live UI, dashboard, real data | Browser screenshot + cropping |
| **Pipeline/Flow Diagram** | CI/CD, workflows, processes | `architecture-diagram` or custom SVG |

## Workflow: Per-Project Visuals

### Option A — Infographic (Baoyu, requires `image_gen` toolset)

Best for project cards that need to combine tech stack, features, and visual impact in one image.

1. **Enable image_gen toolset** (one-time):
   ```bash
   hermes tools enable image_gen
   # Then /reset to activate
   ```
   Requires a FAL_KEY in `~/.hermes/.env` (get one at https://fal.ai/dashboard).

2. **Follow Baoyu infographic workflow**:
   - Create `analysis.md` (content type, complexity, audience)
   - Create `structured-content.md` (sections with verbatim data)
   - Create `prompts/infographic.md` (layout × style, aspect ratio, content)
   - Run `image_generate` with the prompt → download result
   
   Recommended layout × style combos for tech portfolios:
   - **bento-grid + corporate-memphis**: Clean modular overview, vibrant flat design
   - **dashboard + technical-schematic**: Blueprint-style, engineering/DevOps feel
   - **structural-breakdown + cyberpunk-neon**: Futuristic, impactful for cloud/infra
   
   Aspect: `landscape` (16:9) fits Upwork's content area best.

### Option B — Architecture Diagram (no API key needed)

Best for DevOps/infrastructure projects where you need to show system topology.

1. Generate a dark-themed HTML/SVG diagram using `architecture-diagram` skill
2. Open the HTML file in a browser (works offline, no dependencies)
3. Take a screenshot with the browser's built-in tools or `browser_vision`
4. Save/export as PNG

The skill's template provides a complete dark grid-backed design system with component types (frontend, backend, database, security, cloud), arrows, boundaries, and info cards.

### Option C — Live Screenshots

For web apps, IoT dashboards, or any running UI:
1. Start the app locally (or use the deployed URL)
2. Navigate to the relevant page/state
3. Capture screenshot via `browser_vision` or OS screenshot tool
4. Crop and optimize (aim for <500 KB per image)

## Upwork Upload Requirements

- **Content area** in the portfolio form accepts: images, video, text, links, documents, audio
- **Image format**: PNG or JPG preferred
- **Suggested size**: 1200×675px (16:9) or close to it
- Each project entry can have multiple images — show different aspects (UI, architecture, hardware)

## Per-Project Strategy

| Project Type | Recommended Visuals |
|-------------|-------------------|
| **Web App** (SaaS, dashboard) | Screenshot of live UI + infographic with tech stack + feature badges |
| **IoT/Hardware** (ESP32, embedded) | Photo of device + screenshot of web dashboard + architecture diagram |
| **DevOps/Infrastructure** (K8s, CI/CD) | Architecture diagram (full stack) + CI/CD pipeline flow diagram |
| **API/Backend** | API schema/endpoint diagram + performance metrics infographic |

## Naming Convention

Save generated images with descriptive names for easy reference:
```
{project-slug}-{type}-{description}.png
# Examples:
workapp-dashboard-kanban.png
deskmate-hardware-led-ring.png
devops-infrastructure-architecture.png
devops-cicd-pipeline.png
```
