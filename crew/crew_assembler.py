"""
GitHub Analyzer Crew — Main Orchestration Layer
================================================
This module assembles the CrewAI crew and orchestrates the full
multi-agent analysis pipeline.

CrewAI Orchestration Flow:
    GitHubAnalyzerCrew.run(owner, repo)
        ├── Create Agents (4)
        │     ├── RepoStructureAgent
        │     ├── IssueAnalyzerAgent
        │     ├── PRAnalyzerAgent
        │     └── BranchAnalyzerAgent
        ├── Create Tasks (4) — sequential pipeline
        │     ├── Task 1: Repo Structure → 01_repo_structure.md
        │     ├── Task 2: Issue Analysis → 02_issue_analysis.md
        │     ├── Task 3: PR Analysis   → 03_pr_analysis.md
        │     └── Task 4: Branch Analysis → 04_branch_analysis.md
        ├── Assemble Crew (Process.sequential)
        └── Execute → Returns combined Markdown report

Why sequential process?
    Each agent's output can inform subsequent agents.
    The final report synthesizer (Task 4) has full context from Tasks 1-3.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Crew, Process
from dotenv import load_dotenv

from crew.agents.github_agents import create_all_agents
from crew.tasks.github_tasks import create_all_tasks

load_dotenv()
logger = logging.getLogger(__name__)


class GitHubAnalyzerCrew:
    """
    Orchestrates the multi-agent GitHub repository analysis.
    
    Usage:
        crew = GitHubAnalyzerCrew()
        result = crew.run("torvalds", "linux")
        print(result.final_report)
    
    Attributes:
        verbose: Enable detailed agent execution logs
        reports_dir: Directory to save individual Markdown reports
    """

    def __init__(
        self,
        verbose: bool = True,
        reports_dir: Optional[str] = None,
    ):
        self.verbose = verbose
        self.reports_dir = Path(reports_dir or "reports/generated")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run(self, owner: str, repo: str) -> dict:
        """
        Execute the full multi-agent analysis pipeline.
        
        Args:
            owner: GitHub username or organization
            repo: Repository name
            
        Returns:
            dict with keys:
                - final_report: Combined Markdown string
                - section_files: List of individual .md file paths
                - metadata: Run metadata (timing, agents used, etc.)
                - error: Error message if failed
        """
        start_time = datetime.now()
        logger.info(f"Starting analysis for {owner}/{repo}")

        try:
            # ── Step 1: Create all agents ──────────────────────────────────
            logger.info("Creating agents...")
            agents = create_all_agents()

            # ── Step 2: Create all tasks ───────────────────────────────────
            logger.info("Creating tasks...")
            tasks = create_all_tasks(agents, owner, repo)

            # ── Step 3: Assemble the Crew ──────────────────────────────────
            logger.info("Assembling crew...")
            crew = Crew(
                agents=list(agents.values()),
                tasks=tasks,
                process=Process.sequential,   # Tasks run in order
                verbose=self.verbose,
                # memory=True,                # Enable for cross-task memory (requires embeddings)
            )

            # ── Step 4: Kickoff the crew ───────────────────────────────────
            logger.info(f"Kicking off crew for {owner}/{repo}...")
            crew_output = crew.kickoff()

            # ── Step 5: Collect and assemble sections ──────────────────────
            section_files = [
                self.reports_dir / "01_repo_structure.md",
                self.reports_dir / "02_issue_analysis.md",
                self.reports_dir / "03_pr_analysis.md",
                self.reports_dir / "04_branch_analysis.md",
            ]

            final_report = self._assemble_final_report(
                owner, repo, section_files, str(crew_output)
            )

            # Save final combined report
            final_path = self.reports_dir / f"{owner}_{repo}_report.md"
            final_path.write_text(final_report, encoding="utf-8")

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Analysis complete in {elapsed:.1f}s")

            return {
                "success": True,
                "final_report": final_report,
                "final_report_path": str(final_path),
                "section_files": [str(f) for f in section_files if f.exists()],
                "metadata": {
                    "owner": owner,
                    "repo": repo,
                    "run_at": start_time.isoformat(),
                    "elapsed_seconds": elapsed,
                    "agents_used": list(agents.keys()),
                    "tasks_completed": len(tasks),
                },
            }

        except Exception as e:
            logger.error(f"Crew execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "final_report": self._error_report(owner, repo, str(e)),
                "metadata": {
                    "owner": owner,
                    "repo": repo,
                    "run_at": start_time.isoformat(),
                    "error": str(e),
                },
            }

    def _assemble_final_report(
        self,
        owner: str,
        repo: str,
        section_files: list,
        crew_output: str,
    ) -> str:
        """Combine individual section Markdown files into one final report."""
        
        header = f"""# 📊 GitHub Repository Analysis Report
## Repository: `{owner}/{repo}`
**Generated by:** Agentic GitHub Analyzer (CrewAI + GitHub MCP Server)  
**Generated at:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Powered by:** CrewAI Multi-Agent Framework + OpenAI GPT-4o  

---

"""
        
        toc = """## 📋 Table of Contents

1. [Repository Structure Analysis](#️-repository-structure-analysis)
2. [Issue Analysis Report](#-issue-analysis-report)
3. [Pull Request Analysis Report](#-pull-request-analysis-report)
4. [Branch Analysis Report](#-branch-analysis-report)

---

"""
        
        sections = []
        for section_file in section_files:
            path = Path(section_file)
            if path.exists():
                sections.append(path.read_text(encoding="utf-8"))
            else:
                # Fallback: use crew output
                sections.append(
                    f"## Section unavailable\n\nOutput: {crew_output[:500]}"
                )

        footer = f"""
---

## 📌 Analysis Summary

This report was generated using a **multi-agent AI system** powered by:
- **CrewAI** for agent orchestration
- **GitHub MCP Server** for API data retrieval  
- **LangChain** for tool wrapping
- **OpenAI GPT-4o** for analysis and synthesis

*For issues with this report, check the logs or re-run the analysis.*
"""
        
        return header + toc + "\n\n---\n\n".join(sections) + footer

    def _error_report(self, owner: str, repo: str, error: str) -> str:
        """Generate a minimal error report when analysis fails."""
        return f"""# ❌ Analysis Failed

## Repository: `{owner}/{repo}`
**Error:** {error}

**Possible causes:**
- Invalid repository owner or name
- Repository is private (requires GitHub token with repo scope)
- GitHub API rate limit exceeded
- OpenAI API key not set or invalid
- Network connectivity issue

**To fix:**
1. Check your `.env` file has valid `GITHUB_TOKEN` and `OPENAI_API_KEY`
2. Verify the repository exists at `https://github.com/{owner}/{repo}`
3. Check GitHub API rate limits at `https://api.github.com/rate_limit`
"""
