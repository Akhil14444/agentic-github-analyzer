"""
Django Views for GitHub Repository Analyzer
=============================================
Handles the web UI, form processing, CrewAI invocation,
and HTML report rendering.

View Flow:
    GET  /          → index view (form page)
    POST /analyze/  → analyze view (triggers CrewAI, redirects to report)
    GET  /report/<owner>/<repo>/  → report view (renders HTML from Markdown)
    GET  /api/status/<owner>/<repo>/  → status check (for loading UX)
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path so we can import crew/mcp modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.conf import settings
import markdown

logger = logging.getLogger(__name__)


# ─── Helper: Parse GitHub URL ────────────────────────────────────────────────

def parse_github_url(url_or_path: str) -> tuple[str, str]:
    """
    Parse a GitHub URL or 'owner/repo' string.
    
    Examples:
        "https://github.com/torvalds/linux" → ("torvalds", "linux")
        "torvalds/linux"                    → ("torvalds", "linux")
        "linux"                             → raises ValueError
    """
    url_or_path = url_or_path.strip().rstrip("/")
    
    if "github.com" in url_or_path:
        # Extract from URL: https://github.com/owner/repo
        parts = url_or_path.split("github.com/")[-1].split("/")
        if len(parts) >= 2:
            return parts[0], parts[1].split(".")[0]  # Remove .git if present
    elif "/" in url_or_path:
        parts = url_or_path.split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]
    
    raise ValueError(
        f"Invalid GitHub repository format: '{url_or_path}'. "
        "Use 'owner/repo' or 'https://github.com/owner/repo'"
    )


# ─── Helper: Markdown to HTML ────────────────────────────────────────────────

def markdown_to_html(md_text: str) -> str:
    """
    Convert Markdown text to HTML with syntax highlighting.
    Extensions:
        - tables: For data tables
        - fenced_code: For ``` code blocks
        - codehilite: Syntax highlighting
        - toc: Table of contents
        - nl2br: Newlines to <br>
    """
    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "codehilite",
            "toc",
            "nl2br",
            "attr_list",
        ],
        extension_configs={
            "codehilite": {
                "css_class": "highlight",
                "linenums": False,
            }
        }
    )
    return md.convert(md_text)


# ─── View 1: Index (Home Page) ────────────────────────────────────────────────

@require_http_methods(["GET"])
def index(request):
    """
    Renders the home page with the repository input form.
    
    Template: analyzer/index.html
    Context:
        - recent_reports: List of previously generated reports
        - example_repos: Suggested repos to analyze
    """
    # Find recent reports
    reports_dir = Path(settings.REPORTS_DIR)
    recent_reports = []
    
    if reports_dir.exists():
        report_files = sorted(
            reports_dir.glob("*_report.md"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:5]  # Show last 5 reports
        
        for f in report_files:
            name_parts = f.stem.replace("_report", "").split("_", 1)
            if len(name_parts) == 2:
                recent_reports.append({
                    "owner": name_parts[0],
                    "repo": name_parts[1],
                    "filename": f.name,
                    "modified": f.stat().st_mtime,
                })

    example_repos = [
        {"owner": "tiangolo", "repo": "fastapi", "desc": "FastAPI — Modern Python API Framework"},
        {"owner": "django", "repo": "django", "desc": "Django — The Web Framework"},
        {"owner": "pallets", "repo": "flask", "desc": "Flask — Lightweight WSGI Framework"},
        {"owner": "microsoft", "repo": "vscode", "desc": "VS Code — Code Editor"},
        {"owner": "facebook", "repo": "react", "desc": "React — UI Library"},
    ]

    return render(request, "analyzer/index.html", {
        "recent_reports": recent_reports,
        "example_repos": example_repos,
        "page_title": "GitHub Repository Analyzer",
    })


# ─── View 2: Analyze (Trigger CrewAI) ────────────────────────────────────────

@csrf_protect
@require_http_methods(["POST"])
def analyze(request):
    """
    Receives the repository form, validates input,
    triggers the CrewAI analysis pipeline, and redirects to the report.
    
    POST params:
        - repo_url: GitHub URL or owner/repo string
    """
    repo_input = request.POST.get("repo_url", "").strip()

    if not repo_input:
        return render(request, "analyzer/index.html", {
            "error": "Please enter a GitHub repository URL or owner/repo.",
            "page_title": "GitHub Repository Analyzer",
        })

    # Parse the repository identifier
    try:
        owner, repo = parse_github_url(repo_input)
    except ValueError as e:
        return render(request, "analyzer/index.html", {
            "error": str(e),
            "repo_input": repo_input,
            "page_title": "GitHub Repository Analyzer",
        })

    # Check if a recent report already exists (cache hit)
    reports_dir = Path(settings.REPORTS_DIR)
    report_path = reports_dir / f"{owner}_{repo}_report.md"
    
    force_refresh = request.POST.get("force_refresh", "false") == "true"
    
    if report_path.exists() and not force_refresh:
        logger.info(f"Cache hit for {owner}/{repo}, serving existing report")
        return redirect("report", owner=owner, repo=repo)

    # Render the loading page — analysis is triggered there via JS
    return render(request, "analyzer/loading.html", {
        "owner": owner,
        "repo": repo,
        "page_title": f"Analyzing {owner}/{repo}...",
    })


# ─── View 3: Run Analysis (AJAX endpoint) ────────────────────────────────────

@require_http_methods(["POST"])
def run_analysis(request, owner: str, repo: str):
    """
    AJAX endpoint that actually runs the CrewAI analysis.
    Called from the loading page via JavaScript.
    
    Returns JSON:
        - {"status": "complete", "redirect": "/report/owner/repo/"}
        - {"status": "error", "message": "..."}
    """
    try:
        # Import here to avoid Django startup issues with crewai
        from crew.crew_assembler import GitHubAnalyzerCrew

        logger.info(f"Starting CrewAI analysis for {owner}/{repo}")
        
        reports_dir = str(settings.REPORTS_DIR)
        crew = GitHubAnalyzerCrew(
            verbose=True,
            reports_dir=reports_dir,
        )
        
        result = crew.run(owner, repo)
        
        if result.get("success"):
            return JsonResponse({
                "status": "complete",
                "redirect": f"/report/{owner}/{repo}/",
                "metadata": result.get("metadata", {}),
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": result.get("error", "Analysis failed"),
            }, status=500)

    except Exception as e:
        logger.error(f"Analysis error for {owner}/{repo}: {e}", exc_info=True)
        return JsonResponse({
            "status": "error",
            "message": f"Analysis failed: {str(e)}",
        }, status=500)


# ─── View 4: Report (Render HTML from Markdown) ───────────────────────────────

@require_http_methods(["GET"])
def report(request, owner: str, repo: str):
    """
    Renders the final HTML report from the saved Markdown file.
    
    Template: analyzer/report.html
    Context:
        - html_content: Converted HTML from Markdown
        - owner, repo: Repository identifiers
        - metadata: Report metadata
        - section_reports: Individual section HTML
    """
    reports_dir = Path(settings.REPORTS_DIR)
    report_path = reports_dir / f"{owner}_{repo}_report.md"

    # Check if report exists
    if not report_path.exists():
        return render(request, "analyzer/error.html", {
            "error": f"No report found for {owner}/{repo}. Please analyze the repository first.",
            "owner": owner,
            "repo": repo,
            "page_title": "Report Not Found",
        })

    # Load and convert the Markdown report to HTML
    try:
        md_content = report_path.read_text(encoding="utf-8")
        html_content = markdown_to_html(md_content)
    except Exception as e:
        logger.error(f"Failed to render report for {owner}/{repo}: {e}")
        return render(request, "analyzer/error.html", {
            "error": f"Failed to render report: {str(e)}",
            "page_title": "Render Error",
        })

    # Load individual section reports
    section_files = {
        "structure": reports_dir / "01_repo_structure.md",
        "issues": reports_dir / "02_issue_analysis.md",
        "prs": reports_dir / "03_pr_analysis.md",
        "branches": reports_dir / "04_branch_analysis.md",
    }
    
    sections = {}
    for key, path in section_files.items():
        if path.exists():
            try:
                sections[key] = markdown_to_html(path.read_text(encoding="utf-8"))
            except Exception:
                sections[key] = "<p>Section unavailable.</p>"

    return render(request, "analyzer/report.html", {
        "html_content": html_content,
        "sections": sections,
        "owner": owner,
        "repo": repo,
        "repo_url": f"https://github.com/{owner}/{repo}",
        "report_path": str(report_path),
        "page_title": f"Analysis Report: {owner}/{repo}",
        "markdown_content": md_content,
    })


# ─── View 5: Download Report ─────────────────────────────────────────────────

@require_http_methods(["GET"])
def download_report(request, owner: str, repo: str):
    """Download the raw Markdown report."""
    reports_dir = Path(settings.REPORTS_DIR)
    report_path = reports_dir / f"{owner}_{repo}_report.md"

    if not report_path.exists():
        return HttpResponse("Report not found.", status=404)

    content = report_path.read_text(encoding="utf-8")
    response = HttpResponse(content, content_type="text/markdown")
    response["Content-Disposition"] = (
        f'attachment; filename="{owner}_{repo}_analysis_report.md"'
    )
    return response
