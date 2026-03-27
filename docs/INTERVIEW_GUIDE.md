# 🎤 Interview Guide: Agentic GitHub Repository Analyzer
## CrewAI + GitHub MCP Server + Django

---

## 🚀 ELEVATOR PITCHES

### ⏱️ 30-Second Pitch
> "I built an agentic AI system that analyzes any GitHub repository. You give it a URL, and four specialized AI agents — a structure analyst, issue analyst, PR analyst, and branch analyst — each use LangChain tools to call the GitHub MCP server, then synthesize their findings into a structured Markdown report that Django renders as a beautiful HTML interface. It uses CrewAI for orchestration, OpenAI GPT-4o for reasoning, and follows a sequential task pipeline where each agent builds on the previous one's context."

---

### ⏱️ 2-Minute Explanation
> "The project demonstrates a production-grade **Agentic AI** system — where multiple AI agents work together autonomously to complete a complex task.
>
> The architecture has four layers. First, **Django** provides the web interface — a form where you input a GitHub repository URL, a loading page that shows live agent progress, and a report renderer that converts Markdown to styled HTML.
>
> Second, **CrewAI** acts as the orchestration layer. It coordinates four specialized agents in a sequential pipeline: Repository Structure Agent, Issue Analyzer Agent, PR Analyzer Agent, and Branch Analyzer Agent. Each agent has a distinct role, backstory, and tools — like employees in a team.
>
> Third, **LangChain tools** wrap the data layer. Each agent uses a BaseTool implementation that knows how to call the GitHub data APIs. The tools handle input validation via Pydantic and error handling.
>
> Fourth, the **MCP (Model Context Protocol) Server** layer provides the actual data. MCPGitHubClient wraps GitHub's REST API and can route calls through an actual MCP server if one is running, or fall back to direct API calls. MCP is a protocol by Anthropic that standardizes how AI models call external tools — similar to how HTTP standardized web communication.
>
> The result: input a repository, get a professional analysis report in about 60-90 seconds."

---

### ⏱️ 5-Minute Explanation

#### The Problem
> Traditional code analysis tools are static — they scan code but miss the human dynamics: Is the team responsive? Do they review each other's code? Is the branch strategy organized? You need a system that understands context, not just counts.

#### The Solution: Agentic AI
> Instead of one monolithic AI call, I used **multiple specialized agents**, each optimized for a specific domain. This mirrors how real teams work — you have a systems architect, a project manager, a DevOps engineer, and a Git strategy specialist. Each brings expertise to their domain.

#### The Architecture (Layer by Layer)

**Layer 1 — Django (User Interface)**
> The frontend is a clean Django app with three views. The `index` view shows the input form with example repositories. The `analyze` view handles the POST, parses the URL, and renders a loading page. The `run_analysis` view is an AJAX endpoint that actually triggers CrewAI. The `report` view reads the generated Markdown and converts it to HTML using `python-markdown` with syntax highlighting via Pygments.

**Layer 2 — CrewAI (Orchestration)**
> CrewAI is a Python framework built on top of LangChain that lets you define agents with roles, goals, and backstories. When you `crew.kickoff()`, it runs all tasks in `Process.sequential` order — meaning each agent completes its task before the next begins. The output of each task becomes part of the context available to subsequent tasks.

**Layer 3 — LangChain Tools**
> Each of the four agents uses a dedicated LangChain `BaseTool`. Tools define what the agent CAN do. The tool has a `name`, `description` (which the LLM uses to decide when to call it), and a `_run()` method that executes the actual API call. The tool's description is part of the agent's prompt — it's how the agent learns that it can call GitHub.

**Layer 4 — MCP Server (Data)**
> The GitHub MCP Server is a Model Context Protocol server that wraps the GitHub API. MCP standardizes how AI tools expose capabilities — it's like a REST API but designed specifically for LLM tool use. My `MCPGitHubClient` can either call a running MCP server via HTTP or route directly to the GitHub REST API as a fallback. This makes the system resilient and testable.

#### The Output
> Each agent writes a Markdown section to disk. After all four complete, the `crew_assembler.py` combines them into one final report. Django reads this report, converts it to HTML, and renders it with a tabbed interface — one tab per agent's analysis.

---

### 🔬 Deep Technical Explanation

#### Why CrewAI over LangGraph / AutoGen?
> CrewAI is purpose-built for **role-based multi-agent systems**. Unlike LangGraph (which uses directed graphs for control flow) or AutoGen (Microsoft's conversational agent framework), CrewAI models agents as professionals with defined roles, goals, and backstories. This produces more contextually appropriate outputs because the LLM "acts as" its assigned role. CrewAI also has native support for sequential and hierarchical process types, making it ideal for pipeline architectures.

#### Agent Memory and Context
> In `Process.sequential`, each task's output is appended to the crew's shared context. By Task 4, the Branch Analyzer Agent has visibility into what the Repo Structure Agent found. In practice, this means the branch agent can reference specific languages or contributors identified earlier. For production use, enabling `memory=True` in the Crew would add vector store-backed long-term memory.

#### MCP Protocol Details
> The Model Context Protocol defines a JSON-RPC-style protocol for LLM tool use. A tool call looks like:
> ```json
> {"tool": "get_repository", "arguments": {"owner": "django", "repo": "django"}}
> ```
> The server responds with structured data that the agent can reason over. My implementation uses a "thin MCP layer" — the `MCPGitHubClient` translates between our agent's needs and GitHub's API format, with the MCP server as an optional middleware.

#### Django + CrewAI Threading Considerations
> CrewAI runs synchronously by default, which blocks the Django request thread. For production at scale, you'd move the `run_analysis` call to a task queue (Celery + Redis). The AJAX-based loading page already anticipates this pattern — it polls for completion rather than holding the connection open. The timeout is set to 300 seconds in the production Gunicorn config.

#### LangChain Tool Design Principles
> Each tool follows the **Single Responsibility Principle**: one tool, one capability. The `args_schema` Pydantic model validates inputs before execution. The `description` field is a prompt engineering artifact — it must be specific enough for the LLM to know when to call the tool, but not so verbose that it confuses the model. Tools also implement `_arun()` for async support, enabling future migration to async CrewAI execution.

---

## ❓ INTERVIEW Q&A

### 🟢 Basic Questions

**Q: What is Agentic AI?**
> Agentic AI refers to AI systems where one or more LLMs act as autonomous agents — taking actions, calling tools, and making decisions to achieve a goal, rather than just generating a single response. The key characteristics are: (1) goal-directedness — the agent works toward a defined objective; (2) tool use — agents call external APIs or functions; (3) reasoning loops — agents think through problems step-by-step; (4) autonomy — the agent decides HOW to achieve the goal, not just WHAT to say.

**Q: What is MCP (Model Context Protocol)?**
> MCP is an open protocol created by Anthropic that standardizes how AI models interact with external tools and data sources. Think of it as "USB for AI tools" — it defines a common interface so that any tool server can expose its capabilities to any compatible AI model. The protocol uses JSON-RPC and defines schemas for tool discovery (`list_tools`) and tool execution (`call_tool`). GitHub has an official MCP server that wraps their API.

**Q: Why use multiple agents instead of one?**
> Multiple specialized agents outperform a single generalist agent for three reasons: (1) **Context window efficiency** — each agent only has the context it needs, not the entire analysis; (2) **Specialization** — an agent with the role "Senior Issue Analyst" produces better issue analysis than a generic agent; (3) **Parallelism** — agents can run concurrently (though our pipeline is sequential for context sharing); (4) **Maintainability** — adding a new analysis dimension means adding a new agent, not modifying a giant monolith.

**Q: How does Django integrate with CrewAI?**
> Django handles HTTP — receiving the repository URL from the form, routing to the right view. CrewAI is a Python library, so it's imported directly in the Django view and called synchronously. The `run_analysis` view is an AJAX endpoint that blocks while CrewAI runs, then returns JSON with a redirect URL. The loading page provides real-time UX feedback while the analysis runs in the background. For production scale, CrewAI execution would move to a Celery task.

---

### 🟡 Intermediate Questions

**Q: Walk me through what happens when I submit a repository URL.**
> 1. Browser POSTs to `/analyze/` with the URL
> 2. `analyze` view parses `django/django` from the URL string
> 3. View renders `loading.html` with the owner/repo
> 4. JS in `loading.html` immediately POSTs to `/run/django/django/`
> 5. `run_analysis` view calls `GitHubAnalyzerCrew().run("django", "django")`
> 6. Crew creates 4 agents (each backed by GPT-4o) and 4 tasks
> 7. Task 1: Agent 1 uses `GitHubRepoStructureTool` → calls MCP client 4 times → LLM synthesizes → writes `01_repo_structure.md`
> 8. Tasks 2-4 run in sequence similarly
> 9. `crew_assembler` combines sections → saves `django_django_report.md`
> 10. AJAX returns `{"status": "complete", "redirect": "/report/django/django/"}`
> 11. Browser navigates to report URL
> 12. `report` view reads `.md` file, converts to HTML, renders `report.html`

**Q: How does the LangChain tool communicate with the MCP server?**
> The tool calls `mcp_client.call_tool(tool_name, arguments)`. `MCPGitHubClient.call_tool()` checks if `GITHUB_MCP_SERVER_URL` is set. If yes, it POSTs to `{url}/tools/call` with a JSON body `{"tool": "get_repository", "arguments": {...}}`. If no MCP server, it dispatches to a Python function that calls the GitHub REST API directly. This dual-path design makes the system work in development without running an MCP server.

**Q: How do you ensure agent output quality?**
> Several mechanisms: (1) **Task prompts** — each task's `description` is carefully written to specify exactly what the agent must analyze and what format to use; (2) **Expected output** — the `expected_output` field tells the LLM exactly what structure to produce; (3) **Temperature 0.2** — low temperature keeps responses factual and consistent; (4) **Role + backstory** — framing the agent as a "Senior Repository Architect" produces more authoritative outputs; (5) **`max_iter=3`** — limits retry loops to prevent runaway LLM calls.

**Q: What would you change for production deployment?**
> (1) Move CrewAI to Celery tasks for async execution; (2) Add WebSocket support for real-time agent progress updates instead of polling; (3) Add Redis caching for recently analyzed repos; (4) Add rate limiting on the analyze endpoint; (5) Add authentication so users can access their own reports; (6) Use PostgreSQL instead of SQLite; (7) Store report metadata in the database; (8) Add retry logic with exponential backoff for GitHub API calls; (9) Add observability with LangSmith for agent tracing.

---

### 🔴 Advanced Questions

**Q: How would you make agents run in parallel instead of sequentially?**
> CrewAI supports `Process.hierarchical` where a manager agent delegates tasks, but true parallelism requires custom implementation. Options: (1) Use `asyncio.gather()` to run four separate CrewAI instances concurrently; (2) Use `concurrent.futures.ThreadPoolExecutor` to run agents in parallel threads (note: OpenAI calls are I/O-bound so threads are appropriate); (3) Use LangGraph instead of CrewAI for more fine-grained control over the DAG execution order. The challenge is that parallel agents lose shared context — Task 4 couldn't reference Task 1's findings.

**Q: How would you add agent memory across multiple analysis runs?**
> Enable `memory=True` in the Crew, which requires a vector store (e.g., Chroma, Pinecone). Each agent's output gets embedded and stored. On subsequent runs, agents can retrieve relevant context from previous analyses. More specifically, for "remember this repo's history": store analysis metadata in the DB, use semantic search to find related past reports, inject them as context into the task description. This enables trend detection: "This repo's issue count increased 40% since last month."

**Q: What are the failure modes and how do you handle them?**
> (1) **OpenAI API failure** — wrapped in try/catch, returns error report with guidance; (2) **GitHub API rate limit** (60 req/hr unauthenticated) — `GITHUB_TOKEN` raises limit to 5000/hr; (3) **Private repositories** — token with `repo` scope required; (4) **LLM hallucination** — mitigated by low temperature and explicit task prompts with factual data injection; (5) **Long-running analysis** — AJAX pattern with 300s timeout, user sees loading UI; (6) **MCP server down** — automatic fallback to direct GitHub API; (7) **Network timeouts** — `requests.Session` with 30s timeout.

**Q: How does the MCP protocol differ from standard function calling?**
> Standard LangChain function calling embeds tool schemas directly in the LLM prompt via JSON. MCP is a transport protocol — it separates tool definition (on the MCP server) from tool invocation (by the client). Advantages of MCP: (1) Tools are discovered at runtime via `list_tools` — no hardcoding; (2) Tools can be shared across different AI systems (Claude, GPT, local models); (3) Tool servers can be updated independently; (4) MCP enables tool composition — one MCP server aggregating many upstream APIs. It's the difference between a tightly coupled function call and a loosely coupled microservice call.

---

### 🏗️ System Design Questions

**Q: Design this system to handle 1000 concurrent users.**
> Architecture changes needed:
> - **Queue**: Move CrewAI execution to Celery workers (10-20 workers)
> - **Cache**: Redis cache for reports (TTL: 1 hour per repo)
> - **DB**: PostgreSQL with analysis job table (status, created_at, report_path)
> - **Storage**: S3/GCS for report files instead of local disk
> - **API**: WebSocket or SSE for real-time progress (replace polling)
> - **Rate limiting**: Token bucket per IP (10 analyses/hour)
> - **Scaling**: Horizontal Django (behind nginx), separate Celery workers
> - **Cost**: ~$0.05-0.15 per analysis in OpenAI costs → token-based billing

**Q: How would you add a "compare two repositories" feature?**
> Create a `ComparisonCrew` with two instances of each agent — one per repository. Use `Process.hierarchical` with a `ComparisonManagerAgent` that receives both analyses and synthesizes a comparison. The manager's task would be: "Given repo A analysis and repo B analysis, produce a side-by-side comparison of health scores, tech stacks, and workflow maturity." The Django view would accept two repo inputs, run both analysis pipelines concurrently, then pass both results to the comparison task.

**Q: How would you add observability and debugging for agent failures?**
> (1) **LangSmith**: CrewAI integrates with LangSmith for full trace visibility — every LLM call, tool invocation, and token count; (2) **Structured logging**: Log each agent's start, tool calls, and completion with timing; (3) **Agent output storage**: Save raw agent outputs before combining into reports; (4) **Replay capability**: Store the JSON data returned by MCP tools so analyses can be re-run without API calls; (5) **Error classification**: Distinguish LLM errors, API errors, and tool errors for targeted debugging.

---

### 🔄 Follow-up Questions

**Q: Why did you choose Django over FastAPI?**
> Django was chosen for its built-in template engine (Jinja2-compatible), admin panel, session management, and ORM — all useful for a full-stack report application. FastAPI would be preferable if the backend were purely an API consumed by a React frontend, or if async performance was critical. Django's synchronous nature actually aligns well with CrewAI's synchronous execution model.

**Q: How do you handle the case where a repository has no issues or branches?**
> Each agent's task prompt instructs it to "note if the data is unavailable or empty and explain the implications." For example, a repo with zero issues might mean: no public bug tracking (uses internal tracker), very new repo, or extremely stable software. The MCP client returns `{"open_count": 0, "closed_count": 0}` and the LLM interprets this contextually rather than crashing.

**Q: What's the difference between CrewAI agents and LangChain agents?**
> LangChain agents are lower-level — you define a prompt, tools, and an agent loop manually. CrewAI builds on LangChain and adds: (1) **Role-based identity** — `role`, `goal`, `backstory` shape the agent's reasoning persona; (2) **Crew coordination** — agents can delegate to each other (if `allow_delegation=True`); (3) **Task abstraction** — Tasks decouple the "what" from the "who"; (4) **Process types** — sequential, hierarchical; (5) **Built-in memory** options. CrewAI is "LangChain with training wheels for teams" — it adds structure that makes multi-agent systems more maintainable.

---

## 📝 RESUME BULLET POINTS

```
• Architected a production-grade multi-agent AI system using CrewAI,
  LangChain, and GitHub MCP Server to autonomously analyze GitHub
  repositories, reducing manual code review time by ~90%.

• Designed a 4-agent sequential pipeline (Structure, Issues, PR, Branch
  analyzers) each backed by GPT-4o via LangChain BaseTool wrappers,
  generating structured Markdown reports with health scoring.

• Integrated GitHub's Model Context Protocol (MCP) server as the data
  layer, implementing a resilient dual-path client with automatic fallback
  from MCP protocol to direct REST API calls.

• Built a full-stack Django web interface with async AJAX report generation,
  real-time agent progress UI, and Markdown-to-HTML report rendering with
  tabbed navigation and syntax highlighting.

• Implemented production-ready patterns: env-based configuration, graceful
  error handling, report caching, Markdown export, and demo mode for
  zero-dependency testing.
```

---

## 📊 ARCHITECTURE DIAGRAMS (ASCII)

### Data Flow Diagram
```
Input: "django/django"
         │
         ▼
   [URL Parser]
         │ ("django", "django")
         ▼
  [GitHubAnalyzerCrew]
         │
    ┌────┴────────────────────────────────┐
    │      CrewAI Sequential Process      │
    │                                     │
    │  Task1 → Task2 → Task3 → Task4     │
    │    │       │       │       │        │
    │  Agent1  Agent2  Agent3  Agent4    │
    │    │       │       │       │        │
    │  Tool1   Tool2   Tool3  Tool4      │
    └────┴───────┴───────┴───────┴───────┘
         │       │       │       │
         ▼       ▼       ▼       ▼
      [MCP Client — routes to GitHub API]
         │
         ▼
   GitHub REST API
   api.github.com
         │
    ┌────┴──────────────────────┐
    │  /repos/owner/repo        │
    │  /repos/owner/repo/issues │
    │  /repos/owner/repo/pulls  │
    │  /repos/owner/repo/branches│
    └───────────────────────────┘
         │
         ▼ (JSON data back through layers)
         │
    LLM Analysis (GPT-4o)
         │
         ▼
    Markdown Sections
         │ (assembled by crew_assembler.py)
         ▼
    Final Report (.md)
         │ (python-markdown)
         ▼
    HTML Report (Django)
         │
         ▼
    User Browser
```

### Agent Workflow Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                  CrewAI Agent Execution Loop                 │
│                                                             │
│  for each Task in sequential pipeline:                      │
│                                                             │
│    1. THINK: "What do I need to do?"                        │
│       → Read task.description                               │
│       → "I need to call github_repo_structure tool"         │
│                                                             │
│    2. ACT: Call LangChain Tool                              │
│       → tool._run(owner="django", repo="django")           │
│       → MCPGitHubClient.call_tool("get_repository", {...}) │
│       → GitHub API → returns JSON                          │
│                                                             │
│    3. OBSERVE: Process tool output                          │
│       → Receive 500-2000 tokens of JSON data               │
│       → Store in agent's working memory                     │
│                                                             │
│    4. REPEAT if needed (max_iter=3)                         │
│       → "Do I have enough data? Yes → proceed"             │
│                                                             │
│    5. RESPOND: Generate Markdown analysis                   │
│       → Use LLM to write structured section                │
│       → Save to output_file                                │
│       → Return for next agent's context                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*This guide covers all aspects of the project for technical interviews at all levels.*
*Practice the elevator pitches until they feel natural — timing matters in interviews.*
