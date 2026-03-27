"""
CrewAI / LangChain Tools for GitHub MCP Server
================================================
Each tool wraps an MCP server capability and exposes it to CrewAI agents.

Tool Architecture:
    CrewAI Agent
        └── LangChain BaseTool
                └── MCPGitHubClient.call_tool()
                        └── GitHub REST API (via MCP or direct)

Why LangChain Tools?
- CrewAI agents understand LangChain tool schemas natively
- Tools provide structured input validation via Pydantic
- Tools encapsulate retry logic and error handling
- Tools make agent capabilities explicit and auditable
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Type
from pydantic import BaseModel, Field

# Handle LangChain import (works with crewai's bundled langchain too)
try:
    from langchain.tools import BaseTool
except ImportError:
    from langchain_core.tools import BaseTool

from mcp.github_mcp_client import mcp_client


# ─── Input Schemas ────────────────────────────────────────────────────────────

class RepoInput(BaseModel):
    """Input schema for repository-level tools."""
    owner: str = Field(..., description="GitHub repository owner/organization name")
    repo: str = Field(..., description="GitHub repository name")


class BranchInput(BaseModel):
    """Input schema for branch-aware tools."""
    owner: str = Field(..., description="GitHub repository owner/organization name")
    repo: str = Field(..., description="GitHub repository name")
    branch: str = Field(default="main", description="Branch name to analyze")


# ─── Tool 1: Repository Structure Tool ───────────────────────────────────────

class GitHubRepoStructureTool(BaseTool):
    """
    Fetches repository metadata and file tree structure.
    Used by: Repository Structure Agent
    MCP Tool: get_repository, get_file_tree, get_languages, get_contributors
    """
    name: str = "github_repo_structure"
    description: str = (
        "Analyzes GitHub repository structure. Fetches metadata (stars, forks, description), "
        "file tree, programming languages, and top contributors. "
        "Input: JSON with 'owner' and 'repo' keys."
    )
    args_schema: Type[BaseModel] = RepoInput

    def _run(self, owner: str, repo: str) -> str:
        """Execute repository structure analysis via MCP tools."""
        results = {}

        # MCP Tool Call 1: Repository metadata
        results["metadata"] = mcp_client.call_tool(
            "get_repository", {"owner": owner, "repo": repo}
        )

        # MCP Tool Call 2: File tree
        results["tree"] = mcp_client.call_tool(
            "get_file_tree", {"owner": owner, "repo": repo}
        )

        # MCP Tool Call 3: Language breakdown
        results["languages"] = mcp_client.call_tool(
            "get_languages", {"owner": owner, "repo": repo}
        )

        # MCP Tool Call 4: Contributors
        results["contributors"] = mcp_client.call_tool(
            "get_contributors", {"owner": owner, "repo": repo}
        )

        return json.dumps(results, indent=2, default=str)

    async def _arun(self, owner: str, repo: str) -> str:
        return self._run(owner, repo)


# ─── Tool 2: Issues Tool ──────────────────────────────────────────────────────

class GitHubIssuesTool(BaseTool):
    """
    Fetches and analyzes GitHub issues.
    Used by: Issue Analyzer Agent
    MCP Tool: list_issues
    """
    name: str = "github_issues_analyzer"
    description: str = (
        "Analyzes GitHub repository issues. Fetches open/closed issues, "
        "label distribution, and issue trends. "
        "Input: JSON with 'owner' and 'repo' keys."
    )
    args_schema: Type[BaseModel] = RepoInput

    def _run(self, owner: str, repo: str) -> str:
        """Execute issue analysis via MCP tools."""
        results = mcp_client.call_tool(
            "list_issues", {"owner": owner, "repo": repo}
        )
        return json.dumps(results, indent=2, default=str)

    async def _arun(self, owner: str, repo: str) -> str:
        return self._run(owner, repo)


# ─── Tool 3: Pull Requests Tool ───────────────────────────────────────────────

class GitHubPRTool(BaseTool):
    """
    Fetches and analyzes GitHub Pull Requests.
    Used by: PR Analyzer Agent
    MCP Tool: list_pull_requests
    """
    name: str = "github_pr_analyzer"
    description: str = (
        "Analyzes GitHub pull requests. Fetches open/merged PRs, "
        "review patterns, and contribution velocity. "
        "Input: JSON with 'owner' and 'repo' keys."
    )
    args_schema: Type[BaseModel] = RepoInput

    def _run(self, owner: str, repo: str) -> str:
        """Execute PR analysis via MCP tools."""
        results = mcp_client.call_tool(
            "list_pull_requests", {"owner": owner, "repo": repo}
        )
        return json.dumps(results, indent=2, default=str)

    async def _arun(self, owner: str, repo: str) -> str:
        return self._run(owner, repo)


# ─── Tool 4: Branches Tool ────────────────────────────────────────────────────

class GitHubBranchTool(BaseTool):
    """
    Fetches and analyzes GitHub branches and commit history.
    Used by: Branch Analyzer Agent
    MCP Tool: list_branches, get_commits
    """
    name: str = "github_branch_analyzer"
    description: str = (
        "Analyzes GitHub repository branches. Fetches all branches, "
        "recent commit history, and branching strategy patterns. "
        "Input: JSON with 'owner' and 'repo' keys."
    )
    args_schema: Type[BaseModel] = RepoInput

    def _run(self, owner: str, repo: str) -> str:
        """Execute branch analysis via MCP tools."""
        results = {}

        # MCP Tool Call 1: Branch list
        results["branches"] = mcp_client.call_tool(
            "list_branches", {"owner": owner, "repo": repo}
        )

        # MCP Tool Call 2: Recent commits on default branch
        results["recent_commits"] = mcp_client.call_tool(
            "get_commits", {"owner": owner, "repo": repo, "branch": "main"}
        )

        return json.dumps(results, indent=2, default=str)

    async def _arun(self, owner: str, repo: str) -> str:
        return self._run(owner, repo)


# ─── Tool Registry ────────────────────────────────────────────────────────────

ALL_TOOLS = [
    GitHubRepoStructureTool(),
    GitHubIssuesTool(),
    GitHubPRTool(),
    GitHubBranchTool(),
]

TOOL_MAP = {tool.name: tool for tool in ALL_TOOLS}
