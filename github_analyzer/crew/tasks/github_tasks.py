"""
CrewAI Tasks for GitHub Repository Analysis
============================================
Each task defines:
  - description: What the agent must do (injected with repo context)
  - expected_output: The exact format the agent must return
  - agent: Which agent executes this task
  - output_file: Where to save the Markdown output

Task Pipeline:
  Task 1 (Repo Structure) → Task 2 (Issues) → Task 3 (PRs) → Task 4 (Branches)
  
  Each task's output feeds context into subsequent tasks,
  allowing agents to reference each other's findings.
"""

from crewai import Task
from crewai import Agent


# ─── Task 1: Repository Structure Analysis ────────────────────────────────────

def create_repo_structure_task(agent: Agent, owner: str, repo: str) -> Task:
    """
    Task 1: Repository Structure Analysis
    
    The agent must use the github_repo_structure tool to fetch:
    - Repository metadata
    - File tree
    - Language breakdown
    - Contributors
    
    Then produce a structured Markdown section.
    """
    return Task(
        description=f"""
        Analyze the GitHub repository: {owner}/{repo}
        
        Use the github_repo_structure tool with owner="{owner}" and repo="{repo}".
        
        Your analysis MUST cover:
        1. **Repository Overview**: Name, description, stars, forks, watchers, license
        2. **Tech Stack**: Languages used and their percentage breakdown
        3. **Project Structure**: Key directories and files, inferred architecture pattern
        4. **Contributors**: Top contributors by commit count
        5. **Repository Health Indicators**: Open issues count, last updated date
        6. **Topics/Tags**: GitHub topics assigned to the repository
        
        Be specific and data-driven. Include actual numbers from the API response.
        """,
        expected_output="""
        A complete Markdown section with these headers:
        
        ## 🏗️ Repository Structure Analysis
        
        ### Overview
        (Table with: Name, Description, Stars, Forks, Watchers, License, Created, Updated)
        
        ### Tech Stack
        (Language breakdown with percentages, inferred frameworks)
        
        ### Project Architecture
        (Key directories and their purposes, file count, project type)
        
        ### Top Contributors
        (Table: Contributor, Commits, Profile URL)
        
        ### Repository Health Indicators
        (Stars trend interpretation, issue-to-PR ratio, maintenance frequency)
        
        ### Summary & Recommendations
        (3-5 bullet points with actionable insights)
        """,
        agent=agent,
        output_file="reports/generated/01_repo_structure.md",
    )


# ─── Task 2: Issue Analysis ────────────────────────────────────────────────────

def create_issue_analysis_task(agent: Agent, owner: str, repo: str) -> Task:
    """
    Task 2: Issue Health Analysis
    
    The agent must use the github_issues_analyzer tool to fetch:
    - Open and closed issue counts
    - Label distribution
    - Recent open/closed issues
    
    Then produce a health assessment with scoring.
    """
    return Task(
        description=f"""
        Perform a comprehensive issue analysis for repository: {owner}/{repo}
        
        Use the github_issues_analyzer tool with owner="{owner}" and repo="{repo}".
        
        Your analysis MUST cover:
        1. **Issue Volume**: Total open vs closed issues
        2. **Label Analysis**: What labels exist and their frequency
        3. **Issue Categories**: Bugs vs features vs enhancements vs docs
        4. **Issue Backlog Health**: Is the backlog growing or shrinking?
        5. **Recent Activity**: Most recently opened/closed issues
        6. **Issue Health Score**: Rate the project's issue management (1-10)
        
        Identify any red flags (too many bugs, stale issues, no triage labels).
        """,
        expected_output="""
        A complete Markdown section with these headers:
        
        ## 🐛 Issue Analysis Report
        
        ### Issue Volume Summary
        (Table: Open Issues, Closed Issues, Total, Resolution Rate %)
        
        ### Label Distribution
        (Table or list showing each label and count, grouped by category)
        
        ### Issue Health Assessment
        (Narrative analysis: is the team keeping up with issues?)
        
        ### Recent Issues Spotlight
        (Top 5 recent open issues with title and label)
        
        ### Issue Health Score
        (Score out of 10 with justification)
        
        ### Recommendations
        (3-5 specific, actionable recommendations for issue management)
        """,
        agent=agent,
        output_file="reports/generated/02_issue_analysis.md",
    )


# ─── Task 3: PR Analysis ────────────────────────────────────────────────────────

def create_pr_analysis_task(agent: Agent, owner: str, repo: str) -> Task:
    """
    Task 3: Pull Request Analysis
    
    The agent must use the github_pr_analyzer tool to fetch:
    - Open and closed PR counts
    - Average comment counts (review depth)
    - Recent PR activity
    
    Then assess code review culture and velocity.
    """
    return Task(
        description=f"""
        Analyze pull request patterns for repository: {owner}/{repo}
        
        Use the github_pr_analyzer tool with owner="{owner}" and repo="{repo}".
        
        Your analysis MUST cover:
        1. **PR Volume**: Open vs closed/merged PRs
        2. **Review Velocity**: Average comments per PR (indicates review depth)
        3. **PR Merge Rate**: What percentage of PRs get merged?
        4. **Contributor Diversity**: How many different authors submit PRs?
        5. **PR Size Patterns**: Evidence of large vs small atomic PRs
        6. **Code Review Culture Score**: Rate the team's review practices (1-10)
        
        Look for signs of healthy vs unhealthy code review culture.
        """,
        expected_output="""
        A complete Markdown section with these headers:
        
        ## 🔀 Pull Request Analysis Report
        
        ### PR Volume Summary
        (Table: Open PRs, Closed PRs, Merged PRs, Merge Rate %)
        
        ### Code Review Metrics
        (Avg comments/PR, review depth assessment)
        
        ### Recent PR Activity
        (Top 5 recent PRs with title, author, state)
        
        ### Contribution Patterns
        (Analysis of who is contributing and how frequently)
        
        ### Code Review Culture Score
        (Score out of 10 with detailed justification)
        
        ### Recommendations
        (3-5 recommendations for improving PR workflow)
        """,
        agent=agent,
        output_file="reports/generated/03_pr_analysis.md",
    )


# ─── Task 4: Branch Analysis ───────────────────────────────────────────────────

def create_branch_analysis_task(agent: Agent, owner: str, repo: str) -> Task:
    """
    Task 4: Branch Strategy Analysis
    
    The agent must use the github_branch_analyzer tool to fetch:
    - All branches
    - Recent commits
    
    Then identify branching strategy and commit patterns.
    """
    return Task(
        description=f"""
        Analyze the branching strategy and version control patterns for: {owner}/{repo}
        
        Use the github_branch_analyzer tool with owner="{owner}" and repo="{repo}".
        
        Your analysis MUST cover:
        1. **Branch Inventory**: All branches, their naming patterns
        2. **Branching Strategy**: GitFlow? GitHub Flow? Trunk-based? Custom?
        3. **Default Branch**: Is it main or master? Any protection rules?
        4. **Stale Branches**: Any branches that appear old or unused?
        5. **Commit Patterns**: Recent commits — frequency, authors, message quality
        6. **Release Strategy**: Evidence of release branches, hotfix branches, tags
        7. **Git Workflow Score**: Rate the team's Git practices (1-10)
        """,
        expected_output="""
        A complete Markdown section with these headers:
        
        ## 🌿 Branch Analysis Report
        
        ### Branch Inventory
        (Table: Branch Name, Type, Status)
        
        ### Identified Branching Strategy
        (Which strategy: GitFlow / GitHub Flow / Trunk-based, with evidence)
        
        ### Default Branch Analysis
        (Branch protection, status checks, required reviews)
        
        ### Recent Commit Analysis
        (Table: Commit, Author, Message, Date — last 10 commits)
        
        ### Commit Quality Assessment
        (Message quality, commit size patterns, frequency)
        
        ### Git Workflow Score
        (Score out of 10 with justification)
        
        ### Recommendations
        (3-5 recommendations for improving Git workflow)
        """,
        agent=agent,
        output_file="reports/generated/04_branch_analysis.md",
    )


# ─── Factory Function ─────────────────────────────────────────────────────────

def create_all_tasks(agents: dict, owner: str, repo: str) -> list:
    """
    Create all analysis tasks in order.
    Tasks are sequential: each builds on the previous agent's context.
    """
    return [
        create_repo_structure_task(agents["repo_structure"], owner, repo),
        create_issue_analysis_task(agents["issue_analyzer"], owner, repo),
        create_pr_analysis_task(agents["pr_analyzer"], owner, repo),
        create_branch_analysis_task(agents["branch_analyzer"], owner, repo),
    ]
