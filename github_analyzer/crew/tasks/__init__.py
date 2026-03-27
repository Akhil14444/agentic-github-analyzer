"""CrewAI tasks package."""
from .github_tasks import (
    create_repo_structure_task,
    create_issue_analysis_task,
    create_pr_analysis_task,
    create_branch_analysis_task,
    create_all_tasks,
)

__all__ = [
    "create_repo_structure_task",
    "create_issue_analysis_task",
    "create_pr_analysis_task",
    "create_branch_analysis_task",
    "create_all_tasks",
]
