"""
CrewAI Agents for GitHub Repository Analysis
=============================================
Four specialized agents, each with a distinct role, backstory,
and set of MCP-backed tools.

Agent Design Philosophy:
  - Role: Defines WHAT the agent is (its job title)
  - Goal: Defines WHAT the agent must achieve
  - Backstory: Provides LLM context for reasoning style
  - Tools: Defines HOW the agent gathers data

Agents:
  1. RepoStructureAgent   → File tree, languages, metadata
  2. IssueAnalyzerAgent   → Issue triaging and health scoring
  3. PRAnalyzerAgent      → PR velocity and review health
  4. BranchAnalyzerAgent  → Branching strategy and commit patterns
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from crew.tools.github_tools import (
    GitHubRepoStructureTool,
    GitHubIssuesTool,
    GitHubPRTool,
    GitHubBranchTool,
)

load_dotenv()


def _get_llm() -> ChatOpenAI:
    """Shared LLM instance for all agents."""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.2,          # Low temp for factual analysis
        api_key=os.getenv("OPENAI_API_KEY"),
    )


# ─── Agent 1: Repository Structure Agent ─────────────────────────────────────

def create_repo_structure_agent() -> Agent:
    """
    Agent 1: Repository Structure Analyst
    
    Responsibility:
        - Analyzes repository metadata (stars, forks, license, topics)
        - Maps the file/directory tree
        - Identifies tech stack via language breakdown
        - Lists top contributors
        
    Output: Structured Markdown report section on repo architecture
    """
    return Agent(
        role="Senior Repository Architect",
        goal=(
            "Perform a comprehensive structural analysis of the GitHub repository. "
            "Identify the tech stack, project layout, key files, language distribution, "
            "and top contributors. Generate a detailed Markdown report section."
        ),
        backstory=(
            "You are a veteran software architect with 15+ years of experience "
            "analyzing open-source repositories. You have an eagle eye for project "
            "structure, can instantly identify frameworks from file trees, and produce "
            "clear, actionable architectural summaries. You love turning raw GitHub data "
            "into meaningful insights about project health and maturity."
        ),
        tools=[GitHubRepoStructureTool()],
        llm=_get_llm(),
        verbose=os.getenv("CREWAI_VERBOSE", "True") == "True",
        allow_delegation=False,  # Each agent handles its own domain
        max_iter=3,
    )


# ─── Agent 2: Issue Analyzer Agent ────────────────────────────────────────────

def create_issue_analyzer_agent() -> Agent:
    """
    Agent 2: Issue Health Analyst
    
    Responsibility:
        - Counts open vs closed issues
        - Identifies label patterns (bug, feature, enhancement)
        - Assesses issue response times
        - Provides health scoring for issue management
        
    Output: Markdown report section on issue health
    """
    return Agent(
        role="Senior DevOps Issue Analyst",
        goal=(
            "Analyze all GitHub issues in the repository. Count open vs closed, "
            "identify the most common labels, spot concerning trends (too many bugs, "
            "stale issues), and generate a clear health assessment with recommendations."
        ),
        backstory=(
            "You are a DevOps specialist and project health consultant who has audited "
            "hundreds of GitHub repositories. You know that open issues tell the story "
            "of a project's struggles and triumphs. You can diagnose team communication "
            "problems from label patterns alone. You produce concise, data-driven "
            "reports that help maintainers prioritize effectively."
        ),
        tools=[GitHubIssuesTool()],
        llm=_get_llm(),
        verbose=os.getenv("CREWAI_VERBOSE", "True") == "True",
        allow_delegation=False,
        max_iter=3,
    )


# ─── Agent 3: PR Analyzer Agent ───────────────────────────────────────────────

def create_pr_analyzer_agent() -> Agent:
    """
    Agent 3: Pull Request Velocity Analyst
    
    Responsibility:
        - Analyzes open vs merged PR counts
        - Measures review velocity (avg comments)
        - Identifies bottlenecks in code review
        - Spots contribution patterns
        
    Output: Markdown report section on PR health and velocity
    """
    return Agent(
        role="Senior Code Review & CI/CD Analyst",
        goal=(
            "Analyze pull request patterns in the repository. Measure PR velocity, "
            "review thoroughness (comment counts), merge rates, and contributor "
            "activity. Identify workflow bottlenecks and suggest improvements."
        ),
        backstory=(
            "You are a CI/CD pipeline expert and engineering culture advocate who "
            "believes that how a team handles pull requests reveals everything about "
            "their engineering culture. You've helped dozens of teams reduce their "
            "PR cycle times and improve code review quality. Your reports are "
            "praised for being actionable and backed by concrete data."
        ),
        tools=[GitHubPRTool()],
        llm=_get_llm(),
        verbose=os.getenv("CREWAI_VERBOSE", "True") == "True",
        allow_delegation=False,
        max_iter=3,
    )


# ─── Agent 4: Branch Analyzer Agent ──────────────────────────────────────────

def create_branch_analyzer_agent() -> Agent:
    """
    Agent 4: Branch Strategy Analyst
    
    Responsibility:
        - Lists all branches and their purposes
        - Identifies branching strategy (GitFlow, trunk-based, etc.)
        - Analyzes recent commit patterns
        - Checks for stale or long-lived feature branches
        
    Output: Markdown report section on branching strategy
    """
    return Agent(
        role="Senior Git Strategy & Version Control Analyst",
        goal=(
            "Analyze the branching strategy and commit patterns of the repository. "
            "Identify whether the team uses GitFlow, GitHub Flow, or trunk-based "
            "development. Count branches, find stale ones, analyze recent commits, "
            "and provide strategic recommendations."
        ),
        backstory=(
            "You are a Git strategy consultant who has standardized version control "
            "workflows for teams ranging from 2-person startups to 500-engineer "
            "enterprises. You can read a repository's branch list and instantly "
            "understand the team's release cadence, deployment strategy, and "
            "engineering maturity. Your recommendations are specific, practical, "
            "and immediately actionable."
        ),
        tools=[GitHubBranchTool()],
        llm=_get_llm(),
        verbose=os.getenv("CREWAI_VERBOSE", "True") == "True",
        allow_delegation=False,
        max_iter=3,
    )


# ─── Factory Function ─────────────────────────────────────────────────────────

def create_all_agents() -> dict:
    """Create and return all four analysis agents."""
    return {
        "repo_structure": create_repo_structure_agent(),
        "issue_analyzer": create_issue_analyzer_agent(),
        "pr_analyzer": create_pr_analyzer_agent(),
        "branch_analyzer": create_branch_analyzer_agent(),
    }
