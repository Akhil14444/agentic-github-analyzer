"""
Demo Report Generator
======================
Generates realistic mock analysis reports for UI testing
without requiring OpenAI API keys or GitHub tokens.

Usage:
    python demo_report.py django/django
    python demo_report.py tiangolo/fastapi
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "github_analyzer.settings")


DEMO_REPOS = {
    "django/django": {
        "stars": 76800, "forks": 30500, "language": "Python",
        "desc": "The Web framework for perfectionists with deadlines.",
        "topics": ["python", "django", "web-framework", "orm"],
        "languages": {"Python": 97.2, "HTML": 1.8, "JavaScript": 0.8, "Shell": 0.2},
        "open_issues": 186, "closed_issues": 28400,
        "open_prs": 25, "closed_prs": 41200,
        "branches": ["main", "stable/5.0.x", "stable/4.2.x", "stable/3.2.x"],
        "contributors": [
            ("felixxm", 1842), ("timgraham", 1654), ("carlton", 892),
            ("akfish", 745), ("claudep", 621)
        ],
    },
    "tiangolo/fastapi": {
        "stars": 72100, "forks": 6100, "language": "Python",
        "desc": "FastAPI framework, high performance, easy to learn, fast to code, ready for production.",
        "topics": ["python", "fastapi", "rest-api", "openapi", "asyncio"],
        "languages": {"Python": 99.1, "Shell": 0.5, "Dockerfile": 0.4},
        "open_issues": 412, "closed_issues": 2800,
        "open_prs": 38, "closed_prs": 1100,
        "branches": ["master", "dev"],
        "contributors": [
            ("tiangolo", 643), ("dependabot[bot]", 312), ("Kludex", 87),
            ("euri10", 64), ("hasansezertasan", 42)
        ],
    },
}


def generate_demo_structure_report(owner: str, repo: str, data: dict) -> str:
    langs = "\n".join([f"| {lang} | {pct}% | {'█' * int(pct/5)} |"
                       for lang, pct in data["languages"].items()])
    contribs = "\n".join([f"| [@{name}](https://github.com/{name}) | {commits:,} |"
                          for name, commits in data["contributors"]])
    topics = ", ".join([f"`{t}`" for t in data["topics"]])

    return f"""## 🏗️ Repository Structure Analysis

### Overview

| Property | Value |
|---|---|
| **Repository** | [{owner}/{repo}](https://github.com/{owner}/{repo}) |
| **Description** | {data['desc']} |
| **Stars** | ⭐ {data['stars']:,} |
| **Forks** | 🍴 {data['forks']:,} |
| **Primary Language** | {data['language']} |
| **License** | BSD-3-Clause |
| **Topics** | {topics} |

### Tech Stack

| Language | Percentage | Distribution |
|---|---|---|
{langs}

**Inferred Framework:** {data['language']} project using modern packaging (pyproject.toml detected). 
Likely uses pytest for testing, tox for CI matrix, and setuptools/flit for distribution.

### Project Architecture

The repository follows a **monorepo structure** with clear separation of concerns:

- **`{repo}/`** — Core library source code (~{random.randint(80, 200)} modules)
- **`tests/`** — Comprehensive test suite ({random.randint(800, 2500)} test files)
- **`docs/`** — Sphinx-based documentation with tutorials and API reference
- **`scripts/`** — Release automation and maintenance scripts
- **`.github/`** — CI/CD workflows (GitHub Actions), issue templates

**Architecture Pattern:** Domain-driven with clean module boundaries. 
Each subdirectory represents a distinct functional domain.

### Top Contributors

| Contributor | Commits | Profile |
|---|---|---|
{contribs}

### Repository Health Indicators

- 🟢 **Highly Active**: {data['stars']:,} stars places this in the top 1% of Python projects
- 🟢 **Strong Community**: {data['forks']:,} forks indicate significant adoption
- 🟡 **Issue Ratio**: {data['open_issues']}/{data['closed_issues']:,} open/closed suggests active maintenance
- 🟢 **Documentation**: Dedicated docs directory with API reference

### Summary & Recommendations

- ✅ **Mature codebase** with well-established module boundaries — safe for production adoption
- ✅ **Active maintenance** evidenced by recent commits and consistent release cadence
- ⚡ Consider adding `CODEOWNERS` file to route PR reviews to domain experts
- 📋 The `CONTRIBUTING.md` guidelines are comprehensive — new contributors are well-served
- 🔄 Dependency update automation (Dependabot) is configured and active
"""


def generate_demo_issues_report(owner: str, repo: str, data: dict) -> str:
    resolution_rate = round(data['closed_issues'] / max(data['closed_issues'] + data['open_issues'], 1) * 100, 1)
    
    label_data = [
        ("bug", random.randint(20, 80), "🔴"),
        ("enhancement", random.randint(30, 90), "✨"),
        ("documentation", random.randint(10, 40), "📚"),
        ("question", random.randint(15, 50), "❓"),
        ("good first issue", random.randint(10, 30), "🌱"),
        ("help wanted", random.randint(8, 25), "🙋"),
    ]
    labels_table = "\n".join([f"| {icon} `{name}` | {count} | {'█' * (count // 5)} |"
                               for name, count, icon in label_data])

    health_score = 8.2 if resolution_rate > 90 else (7.1 if resolution_rate > 70 else 5.5)

    return f"""## 🐛 Issue Analysis Report

### Issue Volume Summary

| Metric | Count |
|---|---|
| **Open Issues** | {data['open_issues']:,} |
| **Closed Issues** | {data['closed_issues']:,} |
| **Total Issues** | {data['open_issues'] + data['closed_issues']:,} |
| **Resolution Rate** | {resolution_rate}% |

### Label Distribution

| Label | Count | Frequency |
|---|---|---|
{labels_table}

### Issue Health Assessment

The repository demonstrates **strong issue management hygiene**. With a {resolution_rate}% 
resolution rate across {data['closed_issues']:,} closed issues, the maintainer team consistently 
addresses reported problems. 

The distribution between bug reports and enhancement requests ({data['open_issues']} open) 
is healthy — suggesting the software is stable while still growing in capability.

**Positive signals:**
- `good first issue` labels are actively used → welcoming to new contributors
- `help wanted` labels exist → community is invited to contribute
- Low ratio of stale issues (< 6 months old) → regular triage happening

**Concern areas:**
- Some issues dated 12+ months with no response → consider auto-close policy
- Enhancement requests accumulate faster than they're addressed → prioritization framework needed

### Recent Issues Spotlight

| # | Title | Labels | Age |
|---|---|---|---|
| #18341 | Fix migration optimizer edge case with ForeignKey | `bug` | 3 days |
| #18338 | Add async support for cache backend | `enhancement` | 5 days |
| #18330 | Update Python 3.13 compatibility matrix | `documentation` | 1 week |
| #18325 | QuerySet.explain() missing ANALYZE option | `bug` | 2 weeks |
| #18318 | GeoDjango: SpatiaLite 5.1 support | `enhancement` | 3 weeks |

### Issue Health Score

**Score: {health_score}/10** 🟢

**Justification:** High resolution rate ({resolution_rate}%), active label taxonomy, 
regular triage cadence, and welcoming new-contributor labels all indicate 
excellent issue management practices.

### Recommendations

1. **Implement auto-close bot** for issues with no activity after 180 days — reduces noise
2. **Add issue templates** for bug reports vs feature requests to improve signal quality
3. **Create a triage team** — rotate responsibility among core contributors monthly
4. **Milestone tracking** — link issues to release milestones for better roadmap visibility
5. **Issue metrics dashboard** — track mean-time-to-first-response as a team KPI
"""


def generate_demo_pr_report(owner: str, repo: str, data: dict) -> str:
    merge_rate = round(data['closed_prs'] / max(data['closed_prs'] + data['open_prs'], 1) * 100, 1)
    avg_comments = round(random.uniform(3.2, 8.7), 1)
    
    review_score = 8.8 if avg_comments > 5 else 7.2

    return f"""## 🔀 Pull Request Analysis Report

### PR Volume Summary

| Metric | Count |
|---|---|
| **Open PRs** | {data['open_prs']} |
| **Closed/Merged PRs** | {data['closed_prs']:,} |
| **Total PRs** | {data['closed_prs'] + data['open_prs']:,} |
| **Merge Rate** | {merge_rate}% |

### Code Review Metrics

| Metric | Value | Assessment |
|---|---|---|
| **Avg Comments / PR** | {avg_comments} | 🟢 Thorough |
| **Avg Review Time** | ~3.2 days | 🟢 Responsive |
| **Review Approval Required** | Yes (2 reviewers) | 🟢 Enforced |
| **CI Checks Required** | Yes (11 checks) | 🟢 Automated |

**Analysis:** An average of {avg_comments} comments per PR indicates reviewers engage 
substantively with code — not just rubber-stamping. This is a hallmark of mature 
engineering culture.

### Recent PR Activity

| PR | Title | Author | State |
|---|---|---|---|
| #18340 | Refactor ORM prefetch logic for clarity | @contributor1 | Open |
| #18336 | Add support for RETURNING clause in bulk_create() | @contributor2 | Open |
| #18329 | Fix: Template loader cache invalidation race | @contributor3 | Merged ✅ |
| #18322 | Docs: Clarify select_related() depth behavior | @contributor4 | Merged ✅ |
| #18315 | Add PostgreSQL JSONB indexing support | @contributor5 | Open |

### Contribution Patterns

The project follows a **distributed contribution model** where:
- Core team (5-10 people) handles ~40% of merged PRs
- Regular contributors (20-50 people) handle ~35%
- Community one-time contributors handle ~25%

This distribution is **healthy** — it shows the project is accessible to new 
contributors while maintaining a stable core team for consistency.

### Code Review Culture Score

**Score: {review_score}/10** 🟢

**Justification:**
- Required reviews before merge: ✅ enforced
- CI gates: ✅ 11 automated checks must pass
- Comment quality: ✅ substantive, educational reviews documented
- Merge velocity: ✅ responsive without being hasty
- Contributor diversity: ✅ welcoming contribution pipeline

### Recommendations

1. **PR size policy** — Encourage PRs under 400 lines changed; large PRs show lower review quality
2. **Review assignment rotation** — Distribute review load evenly to prevent bottlenecks
3. **Draft PR culture** — Encourage early WIP PRs for design feedback before implementation
4. **CHANGELOG automation** — Auto-generate changelog entries from merged PR titles
5. **PR metrics** — Track P50/P95 time-to-merge as engineering efficiency KPI
"""


def generate_demo_branch_report(owner: str, repo: str, data: dict) -> str:
    branches = data["branches"]
    branch_table = "\n".join([
        f"| `{b}` | {'Default' if i == 0 else 'Stable release' if 'stable' in b else 'Feature/fix'} | Active |"
        for i, b in enumerate(branches)
    ])

    git_score = 9.1 if len(branches) > 2 else 7.5

    return f"""## 🌿 Branch Analysis Report

### Branch Inventory

| Branch | Type | Status |
|---|---|---|
{branch_table}

**Total Branches:** {len(branches)}

### Identified Branching Strategy

**Strategy: GitHub Flow + Long-term Stable Branches** ✅

Evidence:
- `main` / `master` is the primary development branch
- `stable/X.Y.x` branches exist for long-term support (LTS) releases
- No `develop` branch → not using GitFlow
- Feature work happens on short-lived branches merged to `main`

This is a **mature, well-reasoned strategy** for an open-source library that must 
support multiple production versions simultaneously.

### Default Branch Analysis

| Property | Value |
|---|---|
| **Default Branch** | `{branches[0]}` |
| **Branch Protection** | ✅ Enabled |
| **Required Reviews** | 2 approvals |
| **Status Checks** | 11 required (CI matrix) |
| **Force Push** | ❌ Disabled |
| **Admin Bypass** | ❌ Disabled |

The default branch is **maximally protected** — reflecting production-grade 
quality standards appropriate for a widely-deployed framework.

### Recent Commit Analysis

| SHA | Author | Message | Date |
|---|---|---|---|
| `a1b2c3` | @felixxm | Fix: Improve migration state handling | Today |
| `d4e5f6` | @timgraham | Tests: Add coverage for async ORM paths | Yesterday |
| `g7h8i9` | @carlton | Docs: Update 5.1 release notes | 2 days ago |
| `j0k1l2` | @dependabot | Bump cryptography from 42.0.4 to 42.0.5 | 3 days ago |
| `m3n4o5` | @felixxm | Refactor: Simplify BaseDatabaseWrapper | 4 days ago |

### Commit Quality Assessment

| Metric | Assessment |
|---|---|
| **Message format** | 🟢 Consistent `Type: Description` pattern |
| **Commit size** | 🟢 Small, atomic commits preferred |
| **Frequency** | 🟢 5-15 commits/week on `main` |
| **Signed commits** | 🟡 Not enforced (optional) |

### Git Workflow Score

**Score: {git_score}/10** 🟢

**Justification:** Protected default branch, clear stable/LTS branch naming, 
atomic commits, and consistent message format all indicate professional-grade 
Git practices. Minor deduction for missing commit signing enforcement.

### Recommendations

1. **Require signed commits** on `main` for supply-chain security compliance
2. **Add `BRANCH_NAMING.md`** documenting the naming convention for contributors
3. **Auto-delete merged branches** — reduces stale branch accumulation
4. **Tag-based releases** — ensure every release is tagged for reproducibility (already done ✅)
5. **Branch age alerts** — notify when a branch hasn't been merged/updated in 30+ days
"""


def generate_full_report(owner: str, repo: str) -> str:
    key = f"{owner}/{repo}"
    data = DEMO_REPOS.get(key, DEMO_REPOS["tiangolo/fastapi"])

    structure = generate_demo_structure_report(owner, repo, data)
    issues    = generate_demo_issues_report(owner, repo, data)
    prs       = generate_demo_pr_report(owner, repo, data)
    branches  = generate_demo_branch_report(owner, repo, data)

    header = f"""# 📊 GitHub Repository Analysis Report
## Repository: `{owner}/{repo}`
**Generated by:** Agentic GitHub Analyzer (CrewAI + GitHub MCP Server)  
**Generated at:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Mode:** DEMO — Realistic mock data (no API keys required)

---

## 📋 Table of Contents

1. [Repository Structure Analysis](#️-repository-structure-analysis)
2. [Issue Analysis Report](#-issue-analysis-report)
3. [Pull Request Analysis Report](#-pull-request-analysis-report)
4. [Branch Analysis Report](#-branch-analysis-report)

---

"""

    footer = """
---

## 📌 Analysis Summary

This report was generated using a **multi-agent AI system** powered by:
- **CrewAI** for agent orchestration
- **GitHub MCP Server** for API data retrieval  
- **LangChain** for tool wrapping
- **OpenAI GPT-4o** for analysis and synthesis

*This is a DEMO report. Set OPENAI_API_KEY and GITHUB_TOKEN for live analysis.*
"""

    return header + structure + "\n\n---\n\n" + issues + "\n\n---\n\n" + prs + "\n\n---\n\n" + branches + footer


def save_demo_reports(owner: str, repo: str, reports_dir: str = "reports/generated"):
    """Save all demo report sections to disk."""
    path = Path(reports_dir)
    path.mkdir(parents=True, exist_ok=True)

    data = DEMO_REPOS.get(f"{owner}/{repo}", DEMO_REPOS["tiangolo/fastapi"])

    sections = {
        "01_repo_structure.md": generate_demo_structure_report(owner, repo, data),
        "02_issue_analysis.md": generate_demo_issues_report(owner, repo, data),
        "03_pr_analysis.md":    generate_demo_pr_report(owner, repo, data),
        "04_branch_analysis.md": generate_demo_branch_report(owner, repo, data),
        f"{owner}_{repo}_report.md": generate_full_report(owner, repo),
    }

    for filename, content in sections.items():
        filepath = path / filename
        filepath.write_text(content, encoding="utf-8")
        print(f"✅ Saved: {filepath}")

    print(f"\n📊 Demo report ready for {owner}/{repo}")
    print(f"   Open: http://localhost:8000/report/{owner}/{repo}/")
    return str(path / f"{owner}_{repo}_report.md")


if __name__ == "__main__":
    repo_arg = sys.argv[1] if len(sys.argv) > 1 else "django/django"
    
    if "/" not in repo_arg:
        print(f"Usage: python demo_report.py owner/repo")
        print(f"Example: python demo_report.py django/django")
        sys.exit(1)

    owner, repo = repo_arg.split("/", 1)
    save_demo_reports(owner, repo)
