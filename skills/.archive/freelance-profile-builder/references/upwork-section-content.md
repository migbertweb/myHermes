# Upwork Section Content — Portfolio, Work History, Skills

After a profile audit identifies gaps, generate ready-to-copy content for each section. The user wants to paste, not theory.

## Skills Section

Current skills on profile vs recommended additions. Order by priority:

| Priority | Skill | Rationale |
|----------|-------|-----------|
| 🔴 1 | React | User's primary frontend stack |
| 🔴 2 | JavaScript | Foundation of entire stack |
| 🔴 3 | Node.js | User's primary backend stack |
| 🔴 4 | CI/CD | High-demand keyword |
| 🔴 5 | REST API | Most commonly contracted skill |
| 🟡 6 | Git | Basic but often missing |
| 🟡 7 | API Development | Second keyword variant |
| 🟡 8 | IoT (Internet of Things) | User's niche differentiator |
| 🟡 9 | ESP32 | Most concrete niche skill |
| 🟢 10 | WebSocket | Real skill user has |
| 🟢 11 | GitHub Actions | DevOps keyword |
| 🟢 12 | Automation | High-demand keyword |
| 🟢 13 | SQLite | Used in projects |
| 🟢 14 | TypeScript | Quality signal |

**⚠️ Removal candidates:** PHP, Laravel, Kubernetes — if no longer the user's focus, these attract wrong-fit projects.

## Portfolio Section (Upwork fields)

Upwork portfolio entries require these exact fields with hard character limits (confirmed via screenshot, July 2026):

| Field | Required | Max Length |
|-------|----------|------------|
| **Project title** | ✅ Yes | 70 characters |
| **Your role** | ❌ Optional | 100 characters |
| **Project description** | ✅ Yes | 600 characters |
| **Skills and deliverables** | ✅ Yes | 5 skills (tag-style, not free text) |
| **Content upload** | ❌ Optional | Images, video, text, link, document, audio |

**Critical: honor these limits when drafting.** Upwork silently truncates at the boundary. Always pre-check character counts before delivering content — don't make the user discover truncation after pasting.

- **Title** — project name + brief descriptor
- **Your Role** — clear ownership level (Solo Developer, DevOps Engineer, etc.)
- **Description** — problem → solution → tech → outcome (3-5 sentences)
- **Skills** — comma-separated, match actual project stack
- **Deliverables** — concrete artifacts produced (bullet list)
- **Images/Video** — type of media to upload

### Template for each project

Always verify character counts before delivering. The template below shows approximate lengths:

```
Title: [Project Name] — [One-line descriptor]
       ← aim for 50-65 chars to leave margin (max 70)

Your Role: Solo Developer (full ownership — architecture, backend, frontend, deployment)
           ← aim for 60-85 chars (max 100)

Description:
[2-4 sentences. Start with what the project does. Mention tech. End with outcome or architecture quality.]
← aim for 400-550 chars (max 600)

Skills: [comma-separated, 4-5 skills max. Use exact Upwork skill tags, not free text]

Deliverables:
- [Concrete artifact 1]
- [Concrete artifact 2]
- [Concrete artifact 3]

Images/Video: [type of media — screenshot of X, diagram of Y, short video of Z]
```

### Example — WorkApp

```
Title: WorkApp — Full-Stack Project Management Platform

Your Role: Solo Developer (full ownership — architecture, backend, frontend, deployment)

Description:
Complete project management web application with Kanban boards, client management, budget tracking with line items, professional PDF invoice generation, activity logging, analytics dashboard, and drag-and-drop file uploads. Features JWT authentication with role-based access, responsive design optimized for 768px+ screens, and CSV export.

Skills: React, Node.js, Express.js, SQLite, JWT

Deliverables:
- Full-stack web application deployed and running
- 18 pull requests merged into production
- PDF invoice generation with corporate branding (jsPDF + autoTable)
- Clean modular architecture with separated concerns
- Responsive UI with Kanban, analytics charts, and client dashboard

Images/Video: Screenshot of Kanban board + screenshot of analytics dashboard
```

### Example — DeskMate IoT

```
Title: DeskMate — IoT Monitoring System with ESP32 + Real-Time Web Dashboard

Your Role: Solo Developer (firmware, backend API, frontend, integration)

Description:
IoT environmental monitoring system combining ESP32-C3 SuperMini with ST7789 display and WS2812B LED ring, paired with a real-time web dashboard via WebSocket. Custom firmware written in ESP-IDF with FreeRTOS for task management. Bi-directional communication enables instant updates between hardware sensor readings and browser interface.

Skills: ESP32, C, C++, FreeRTOS, WebSocket

Deliverables:
- Custom ESP32 firmware (ESP-IDF + FreeRTOS)
- Real-time web dashboard with live sensor graphs
- WS2812B LED ring as visual status indicators
- ST7789 display showing environmental data on-device
- Bi-directional WebSocket communication layer

Images/Video: Photo of ESP32 with display running + short video of LED ring responding to data + screenshot of web dashboard
```

### Example — DevOps Infrastructure (Traefik + K3s + CI/CD)

```
Title: DevOps Infrastructure — K3s Cluster, Traefik, CI/CD & Docker

Your Role: Solo DevOps Engineer (Terraform, Kubernetes, Docker, CI/CD, monitoring, security)

Description:
End-to-end DevOps stack: Traefik reverse proxy (Docker Compose) with automatic Let's Encrypt SSL, Cloudflare DNS challenge, security middlewares, rate limiting and Prometheus metrics — routing multiple apps behind a single entry point. K3s Kubernetes cluster on Hetzner Cloud via Terraform (IaC) with Traefik Ingress, cert-manager, NFS storage, MariaDB/Redis, Prometheus/Grafana monitoring, and ArgoCD for GitOps. CI/CD pipelines with GitHub Actions for automated builds, testing, and zero-downtime deployments. Secret management with SOPS + KSOPS.

Skills: Docker, Kubernetes, Terraform, GitHub Actions, CI/CD

Deliverables:
- Production Traefik reverse proxy with automatic SSL (Docker Compose)
- K3s Kubernetes cluster provisioned via Terraform on Hetzner Cloud
- Prometheus + Grafana monitoring stack
- CI/CD pipeline configs (GitHub Actions) with automated Docker builds
- Secret management with Mozilla SOPS + KSOPS
- ArgoCD configuration for GitOps workflows

Images/Video: Architecture diagram of K3s cluster + Traefik dashboard screenshot + Grafana metrics dashboard
```

## Employment History Section

Upwork allows adding employment history outside Upwork. Use this pattern:

### Job entry format

**Title:** [Role]
**Company:** [Company name or Self-employed]
**Dates:** [Start] – [End/Present]
**Description:** [1-3 sentences. Focus on deliverables, not responsibilities. Include stack keywords.]

### Example entries

```
Title: Full Stack Developer — Freelance
Company: Self-employed (Freelance)
Dates: 2024 – Present
Description: End-to-end development of web applications, IoT systems, and automation. Built project management platforms with Kanban and analytics, IoT environmental dashboards with ESP32 + real-time WebSocket, and DevOps pipelines with Docker + GitHub Actions. Stack: React, Node.js, Python, Docker, Linux.

Title: Junior Developer Analyst
Company: TODoca, C.A.
Dates: Jan 2018 – May 2020
Description: Led migration from physical server to VPS Linux infrastructure, improving system reliability by ~40%. Provided technical support, bug fixing, and ensured high availability of production platform.

Title: Project Analyst
Company: CVG Alcasa
Dates: May 2012 – Nov 2018
Description: Requirements gathering, process definition, and corporate project execution. Technical feasibility analysis and resource allocation planning. Schedule tracking and integrated project management support.
```

## Bio — Single-Paragraph Version

Some users prefer a single compact paragraph instead of the 4-paragraph structure. Ready-to-paste:

**English:**
> Full Stack Developer with 5+ years of experience building scalable web applications, IoT systems, and automated workflows. I help startups and businesses turn complex requirements into reliable software — from real-time dashboards and REST APIs to embedded device integration with ESP32. I've delivered end-to-end solutions including custom IoT controllers, full-stack management platforms with Kanban and analytics, and DevOps pipelines that streamline deployment. My workflow: daily updates via Slack or Telegram, Git version control, CI/CD via GitHub Actions, Docker containers, and clear documentation. Have a project in mind? Let's talk.

**Spanish (LATAM clients):**
> Desarrollador Full Stack con 5+ años de experiencia creando aplicaciones web escalables, sistemas IoT y flujos de automatización. Ayudo a startups y empresas a convertir requerimientos complejos en software confiable — desde dashboards en tiempo real y APIs hasta integración de dispositivos embebidos con ESP32. He entregado soluciones completas incluyendo controladores IoT personalizados, plataformas de gestión con Kanban y analytics, y pipelines DevOps que optimizan despliegues. Mi flujo de trabajo incluye: comunicación diaria vía Slack/Telegram, Git, CI/CD con GitHub Actions, Docker y documentación clara. ¿Tienes un proyecto en mente? Hablemos.
