# 🤖 Agentic GitHub Repository Analyzer

> **Multi-agent AI system** that analyzes any GitHub repository using **CrewAI**, **GitHub MCP Server**, **LangChain tools**, and a **Django web interface** — generating structured HTML reports from Markdown.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-green?logo=django)](https://djangoproject.com)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.28-orange)](https://github.com/joaomdmoura/crewAI)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-black?logo=openai)](https://openai.com)

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Agents & Tasks](#agents--tasks)
4. [MCP Server Integration](#mcp-server-integration)
5. [Setup & Installation](#setup--installation)
6. [Running the Project](#running-the-project)
7. [Demo Mode](#demo-mode)
8. [Workflow Explanation](#workflow-explanation)
9. [File-by-File Explanation](#file-by-file-explanation)
10. [Example Output](#example-output)
11. [Deployment](#deployment)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                │
│                    http://localhost:8000/                           │
└─────────────────────────┬───────────────────────────────────────────┘
                           │ HTTP POST /analyze/
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DJANGO LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  index view  │  │ analyze view │  │     report view          │  │
│  │  (form UI)   │  │(POST handler)│  │  (Markdown → HTML)       │  │
│  └──────────────┘  └──────┬───────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                             │ crew.run(owner, repo)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CREWAI ORCHESTRATION LAYER                       │
│                                                                     │
│  GitHubAnalyzerCrew (Process.sequential)                           │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Agent 1: Repo Structure  →  Task 1  →  01_repo_structure.md  │ │
│  │ Agent 2: Issue Analyzer  →  Task 2  →  02_issue_analysis.md  │ │
│  │ Agent 3: PR Analyzer     →  Task 3  →  03_pr_analysis.md     │ │
│  │ Agent 4: Branch Analyzer →  Task 4  →  04_branch_analysis.md │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────────┘
                           │ tool.call(arguments)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   LANGCHAIN TOOLS LAYER                             │
│  ┌─────────────────────┐  ┌─────────────────────────────────────┐  │
│  │ GitHubRepoStructure │  │  GitHubIssues / GitHubPR / Branch   │  │
│  │ Tool (BaseTool)     │  │  Tool (BaseTool implementations)    │  │
│  └────────┬────────────┘  └──────────────┬──────────────────────┘  │
└───────────┼───────────────────────────────┼────────────────────────┘
            │ mcp_client.call_tool()         │
            ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   MCP SERVER LAYER                                  │
│                                                                     │
│   MCPGitHubClient                                                  │
│   ├── [MCP Server Running] → POST http://localhost:3000/tools/call │
│   └── [Fallback]           → Direct GitHub REST API calls          │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  GitHub REST API v3
               https://api.github.com
```

---

## Project Structure

```
github_analyzer/
│
├── manage.py                        # Django CLI entry point
├── requirements.txt                 # All Python dependencies
├── .env.example                     # Environment variable template
├── demo_report.py                   # Demo mode (no API keys needed)
│
├── github_analyzer/                 # Django project settings
│   ├── settings.py                  # Configuration (DB, static, etc.)
│   ├── urls.py                      # Root URL router
│   └── wsgi.py                      # WSGI deployment entry point
│
├── analyzer/                        # Django app
│   ├── views.py                     # 5 views: index, analyze, run, report, download
│   └── urls.py                      # App URL patterns
│
├── django_app/
│   └── templates/analyzer/
│       ├── base.html                # Base template (dark theme, fonts, CSS vars)
│       ├── index.html               # Home page with input form
│       ├── loading.html             # Loading screen with live agent status
│       ├── report.html              # Report renderer (tabbed sections)
│       └── error.html               # Error page
│
├── mcp/
│   ├── __init__.py
│   └── github_mcp_client.py         # MCP + GitHub REST API client
│
├── crew/
│   ├── __init__.py
│   ├── crew_assembler.py            # Main CrewAI orchestration class
│   ├── agents/
│   │   ├── __init__.py
│   │   └── github_agents.py         # 4 specialized CrewAI agents
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── github_tasks.py          # 4 analysis tasks with prompts
│   └── tools/
│       ├── __init__.py
│       └── github_tools.py          # 4 LangChain BaseTool implementations
│
└── reports/
    └── generated/                   # Output: .md files per analysis
        ├── 01_repo_structure.md
        ├── 02_issue_analysis.md
        ├── 03_pr_analysis.md
        ├── 04_branch_analysis.md
        └── {owner}_{repo}_report.md # Combined final report
```

---

## Agents & Tasks

### Agent 1 — Repository Structure Agent
| Property | Value |
|---|---|
| **Role** | Senior Repository Architect |
| **Tool** | `GitHubRepoStructureTool` |
| **MCP Calls** | `get_repository`, `get_file_tree`, `get_languages`, `get_contributors` |
| **Output** | `01_repo_structure.md` |
| **Analyzes** | File tree, tech stack, language breakdown, contributor list, repo metadata |

### Agent 2 — Issue Analyzer Agent
| Property | Value |
|---|---|
| **Role** | Senior DevOps Issue Analyst |
| **Tool** | `GitHubIssuesTool` |
| **MCP Calls** | `list_issues` |
| **Output** | `02_issue_analysis.md` |
| **Analyzes** | Open/closed counts, label distribution, health score, resolution rate |

### Agent 3 — PR Analyzer Agent
| Property | Value |
|---|---|
| **Role** | Senior Code Review & CI/CD Analyst |
| **Tool** | `GitHubPRTool` |
| **MCP Calls** | `list_pull_requests` |
| **Output** | `03_pr_analysis.md` |
| **Analyzes** | PR velocity, review depth, merge rate, contribution patterns |

### Agent 4 — Branch Analyzer Agent
| Property | Value |
|---|---|
| **Role** | Senior Git Strategy Analyst |
| **Tool** | `GitHubBranchTool` |
| **MCP Calls** | `list_branches`, `get_commits` |
| **Output** | `04_branch_analysis.md` |
| **Analyzes** | Branching strategy, commit quality, default branch protection |

---

## MCP Server Integration

The **Model Context Protocol (MCP)** server provides a standardized way for AI agents to call external APIs as "tools."

### How it works:
```python
# Agent calls LangChain tool
tool.run({"owner": "django", "repo": "django"})

# Tool calls MCP client
mcp_client.call_tool("get_repository", {"owner": "django", "repo": "django"})

# MCP client routes:
# Option A: POST http://localhost:3000/tools/call (if MCP server running)
# Option B: GET https://api.github.com/repos/django/django (direct fallback)
```

### Running GitHub MCP Server (optional):
```bash
# Using the official GitHub MCP server
npx @modelcontextprotocol/server-github

# Or using Docker
docker run -p 3000:3000 -e GITHUB_TOKEN=$GITHUB_TOKEN ghcr.io/github/github-mcp-server
```

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- OpenAI API key
- GitHub Personal Access Token (for private repos or higher rate limits)

### Step 1: Clone and setup
```bash
git clone https://github.com/yourname/github-analyzer
cd github-analyzer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure environment
```bash
cp .env.example .env
# Edit .env with your keys:
# OPENAI_API_KEY=sk-...
# GITHUB_TOKEN=ghp_...
# DJANGO_SECRET_KEY=your-secret-key
```

### Step 3: Initialize Django
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### Step 4: Run
```bash
python manage.py runserver
# Open: http://localhost:8000
```

---

## Demo Mode

Test the full UI **without API keys** using pre-generated mock reports:

```bash
# Generate demo report for django/django
python demo_report.py django/django

# Generate demo report for fastapi
python demo_report.py tiangolo/fastapi

# Then start Django and view at:
# http://localhost:8000/report/django/django/
python manage.py runserver
```

---

## Workflow Explanation

### Full Request Flow (step by step):

1. **User** visits `http://localhost:8000/` → sees input form
2. **User** enters `django/django` and clicks "Analyze"
3. **Django** `analyze` view parses and validates the input
4. **Django** renders `loading.html` — the loading page
5. **loading.html** JavaScript calls `POST /run/django/django/` via AJAX
6. **Django** `run_analysis` view instantiates `GitHubAnalyzerCrew`
7. **CrewAI** creates 4 agents and 4 tasks
8. **CrewAI** kicks off `Process.sequential` — Task 1 runs first
9. **Agent 1** receives Task 1, calls `GitHubRepoStructureTool`
10. **Tool** calls `MCPGitHubClient.call_tool()` 4 times (metadata, tree, languages, contributors)
11. **MCPGitHubClient** routes to GitHub REST API (or MCP server if running)
12. **Agent 1** receives JSON data, uses LLM (GPT-4o) to write Markdown analysis
13. **Task 1** output saved to `01_repo_structure.md`
14. **Agents 2, 3, 4** run sequentially in the same pattern
15. **Crew** assembles all 4 sections into one final report
16. **Final report** saved to `django_django_report.md`
17. **AJAX** response returns `{"status": "complete", "redirect": "/report/django/django/"}`
18. **Browser** redirects to report page
19. **Django** `report` view reads Markdown file, converts to HTML via `python-markdown`
20. **report.html** renders the tabbed HTML interface

---

## File-by-File Explanation

| File | Purpose |
|---|---|
| `manage.py` | Django CLI — run server, migrate DB |
| `github_analyzer/settings.py` | Project config: apps, DB, static files, env vars |
| `github_analyzer/urls.py` | Root URL routing |
| `analyzer/views.py` | All 5 Django views |
| `analyzer/urls.py` | App-level URL patterns |
| `mcp/github_mcp_client.py` | GitHub API client + MCP protocol layer |
| `crew/crew_assembler.py` | Main orchestration: creates crew, runs pipeline |
| `crew/agents/github_agents.py` | 4 CrewAI Agent definitions |
| `crew/tasks/github_tasks.py` | 4 CrewAI Task definitions with prompts |
| `crew/tools/github_tools.py` | 4 LangChain BaseTool wrappers |
| `templates/analyzer/base.html` | Dark theme, fonts, global CSS |
| `templates/analyzer/index.html` | Repository input form |
| `templates/analyzer/loading.html` | Live agent status + AJAX trigger |
| `templates/analyzer/report.html` | Tabbed HTML report renderer |
| `demo_report.py` | Zero-dependency demo mode |

---

## Example Output

When you analyze `tiangolo/fastapi`, you get:

```markdown
# 📊 GitHub Repository Analysis Report
## Repository: `tiangolo/fastapi`

## 🏗️ Repository Structure Analysis
[Stars, forks, language breakdown, file tree analysis...]

## 🐛 Issue Analysis Report
[412 open issues, label distribution, health score: 7.8/10...]

## 🔀 Pull Request Analysis Report
[38 open PRs, avg 4.2 comments/PR, review culture score: 8.5/10...]

## 🌿 Branch Analysis Report
[2 branches (master, dev), GitHub Flow identified, commit quality...]
```

---

## Deployment

### Docker
```bash
docker build -t github-analyzer .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e GITHUB_TOKEN=ghp_... \
  github-analyzer
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn github_analyzer.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 300  # Long timeout for analysis runs
```

### Environment Variables
| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key for GPT-4o |
| `GITHUB_TOKEN` | Recommended | GitHub PAT for higher rate limits |
| `DJANGO_SECRET_KEY` | ✅ Yes (prod) | Django secret key |
| `DJANGO_DEBUG` | No | Set to `False` in production |
| `GITHUB_MCP_SERVER_URL` | No | URL of running MCP server |

---

## Tech Stack

| Component | Technology | Version |
|---|---|---|
| Web Framework | Django | 4.2 |
| Agent Orchestration | CrewAI | 0.28 |
| Tool Framework | LangChain | 0.1 |
| LLM | OpenAI GPT-4o | Latest |
| MCP Client | Custom + httpx | — |
| Markdown Rendering | python-markdown | 3.6 |
| Syntax Highlighting | Pygments | 2.17 |

---

*Built as a demonstration of Agentic AI architecture with multi-agent orchestration, MCP server integration, and production-ready Django deployment.*
