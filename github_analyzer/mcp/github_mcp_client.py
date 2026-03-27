"""
MCP GitHub Client
==================
Wraps the GitHub MCP Server calls using the httpx client.
This module acts as the bridge between our agents and the GitHub API
via the Model Context Protocol (MCP) server.

MCP Protocol Flow:
  Agent → LangChain Tool → MCPGitHubClient → GitHub MCP Server → GitHub API

If no MCP server is running, falls back to direct GitHub REST API calls.
"""

import os
import json
import logging
import requests
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


# ─── GitHub REST API Direct Client (Fallback & Primary) ──────────────────────

class GitHubAPIClient:
    """
    Direct GitHub REST API client.
    Used when MCP server is not available, or as the backend for MCP calls.
    
    In production, the MCP server wraps these same endpoints.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a GET request to GitHub API."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"GitHub API error {e.response.status_code}: {e}")
            return {"error": str(e), "status_code": e.response.status_code}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"error": str(e)}

    # ── Repository ────────────────────────────────────────────────────────────

    def get_repository(self, owner: str, repo: str) -> Dict:
        """Fetch repository metadata."""
        return self._get(f"/repos/{owner}/{repo}")

    def get_repository_tree(self, owner: str, repo: str, branch: str = "main") -> Dict:
        """Fetch full file tree of the repository."""
        # Get the tree SHA first
        ref_data = self._get(f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
        if "error" in ref_data:
            # Try 'master' as fallback
            ref_data = self._get(f"/repos/{owner}/{repo}/git/ref/heads/master")
        
        if "error" in ref_data:
            return ref_data
        
        sha = ref_data.get("object", {}).get("sha", "")
        tree = self._get(f"/repos/{owner}/{repo}/git/trees/{sha}?recursive=1")
        return tree

    def get_languages(self, owner: str, repo: str) -> Dict:
        """Fetch language breakdown."""
        return self._get(f"/repos/{owner}/{repo}/languages")

    def get_contributors(self, owner: str, repo: str) -> List:
        """Fetch top contributors."""
        result = self._get(f"/repos/{owner}/{repo}/contributors", params={"per_page": 10})
        return result if isinstance(result, list) else []

    def get_topics(self, owner: str, repo: str) -> Dict:
        """Fetch repository topics."""
        response = requests.get(
            f"{self.BASE_URL}/repos/{owner}/{repo}/topics",
            headers={**self.session.headers, "Accept": "application/vnd.github.mercy-preview+json"},
            timeout=30
        )
        return response.json() if response.ok else {}

    # ── Issues ────────────────────────────────────────────────────────────────

    def get_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 20) -> List:
        """Fetch issues (excludes pull requests)."""
        result = self._get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page, "pulls": False}
        )
        if isinstance(result, list):
            # Filter out PRs (GitHub issues API returns PRs too)
            return [i for i in result if "pull_request" not in i]
        return []

    def get_issue_stats(self, owner: str, repo: str) -> Dict:
        """Get aggregate issue statistics."""
        open_issues = self.get_issues(owner, repo, state="open", per_page=100)
        closed_issues = self.get_issues(owner, repo, state="closed", per_page=100)
        
        # Label frequency analysis
        label_counts = {}
        for issue in open_issues:
            for label in issue.get("labels", []):
                name = label.get("name", "")
                label_counts[name] = label_counts.get(name, 0) + 1

        return {
            "open_count": len(open_issues),
            "closed_count": len(closed_issues),
            "label_distribution": label_counts,
            "recent_open": open_issues[:5],
            "recent_closed": closed_issues[:5],
        }

    # ── Pull Requests ─────────────────────────────────────────────────────────

    def get_pull_requests(self, owner: str, repo: str, state: str = "open", per_page: int = 20) -> List:
        """Fetch pull requests."""
        result = self._get(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": per_page, "sort": "updated"}
        )
        return result if isinstance(result, list) else []

    def get_pr_stats(self, owner: str, repo: str) -> Dict:
        """Get aggregate PR statistics."""
        open_prs = self.get_pull_requests(owner, repo, state="open", per_page=50)
        closed_prs = self.get_pull_requests(owner, repo, state="closed", per_page=50)

        return {
            "open_count": len(open_prs),
            "closed_count": len(closed_prs),
            "recent_open": open_prs[:5],
            "recent_closed": closed_prs[:5],
            "avg_comments": (
                sum(pr.get("comments", 0) for pr in open_prs) / max(len(open_prs), 1)
            ),
        }

    # ── Branches ──────────────────────────────────────────────────────────────

    def get_branches(self, owner: str, repo: str) -> List:
        """Fetch all branches."""
        result = self._get(f"/repos/{owner}/{repo}/branches", params={"per_page": 50})
        return result if isinstance(result, list) else []

    def get_branch_protection(self, owner: str, repo: str, branch: str) -> Dict:
        """Fetch branch protection rules."""
        return self._get(f"/repos/{owner}/{repo}/branches/{branch}/protection")

    def get_commits(self, owner: str, repo: str, branch: str = "main", per_page: int = 10) -> List:
        """Fetch recent commits."""
        result = self._get(
            f"/repos/{owner}/{repo}/commits",
            params={"sha": branch, "per_page": per_page}
        )
        return result if isinstance(result, list) else []


# ─── MCP Server Client (Protocol Layer) ──────────────────────────────────────

class MCPGitHubClient:
    """
    MCP (Model Context Protocol) GitHub Server Client.
    
    The MCP server exposes GitHub tools via a standardized protocol.
    Each 'tool call' maps to a GitHub API operation.
    
    MCP Tool Schema:
        {
            "tool": "get_repository",
            "arguments": {"owner": "...", "repo": "..."}
        }
    
    In production: Uses actual MCP server at GITHUB_MCP_SERVER_URL
    In development/demo: Delegates to GitHubAPIClient directly
    """

    MCP_TOOLS = {
        "get_repository": "Get repository metadata and statistics",
        "get_file_tree": "Get complete file/directory structure",
        "list_issues": "List repository issues with filters",
        "list_pull_requests": "List pull requests with filters",
        "list_branches": "List all repository branches",
        "get_languages": "Get language breakdown percentages",
        "get_contributors": "Get top contributor list",
        "get_commits": "Get recent commit history",
    }

    def __init__(self):
        self.mcp_url = os.getenv("GITHUB_MCP_SERVER_URL", "")
        self.github = GitHubAPIClient()
        self.use_mcp = bool(self.mcp_url)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """
        Dispatch an MCP tool call.
        Routes to MCP server if available, else direct GitHub API.
        
        Args:
            tool_name: MCP tool identifier (see MCP_TOOLS)
            arguments: Tool-specific arguments dict
            
        Returns:
            Structured response dict
        """
        if self.use_mcp:
            return self._call_mcp_server(tool_name, arguments)
        else:
            return self._call_direct(tool_name, arguments)

    def _call_mcp_server(self, tool_name: str, arguments: Dict) -> Dict:
        """Send request to actual MCP server via HTTP."""
        try:
            response = requests.post(
                f"{self.mcp_url}/tools/call",
                json={"tool": tool_name, "arguments": arguments},
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"MCP server call failed, falling back to direct API: {e}")
            return self._call_direct(tool_name, arguments)

    def _call_direct(self, tool_name: str, arguments: Dict) -> Dict:
        """
        Direct GitHub API routing — mirrors MCP server tool semantics.
        This is the fallback when MCP server is not running.
        """
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")

        dispatch = {
            "get_repository": lambda: self.github.get_repository(owner, repo),
            "get_file_tree": lambda: self.github.get_repository_tree(
                owner, repo, arguments.get("branch", "main")
            ),
            "list_issues": lambda: self.github.get_issue_stats(owner, repo),
            "list_pull_requests": lambda: self.github.get_pr_stats(owner, repo),
            "list_branches": lambda: {"branches": self.github.get_branches(owner, repo)},
            "get_languages": lambda: self.github.get_languages(owner, repo),
            "get_contributors": lambda: {"contributors": self.github.get_contributors(owner, repo)},
            "get_commits": lambda: {"commits": self.github.get_commits(
                owner, repo, arguments.get("branch", "main")
            )},
        }

        handler = dispatch.get(tool_name)
        if handler:
            return handler()
        else:
            return {"error": f"Unknown tool: {tool_name}"}


# ─── Singleton Instance ───────────────────────────────────────────────────────
mcp_client = MCPGitHubClient()
