from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ScoreSummary:
    overall: int = 0
    label: str = ""
    category_scores: Dict[str, int] = field(default_factory=dict)


@dataclass
class RepoFacts:
    name: str
    description: str
    owner_login: str = ""
    html_url: str = ""
    language: str = ""
    topics: List[str] = field(default_factory=list)
    homepage: str = ""
    updated_at: str = ""
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    license_name: str = ""
    default_branch: str = ""
    default_branch_head_sha: str = ""
    repo_size_kb: int = 0
    is_fork: bool = False
    languages: Dict[str, int] = field(default_factory=dict)
    root_entries: List[str] = field(default_factory=list)
    readme_present: bool = False
    readme_text: str = ""


@dataclass
class RepoCheckResult:
    repo_name: str
    findings: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    score: ScoreSummary = field(default_factory=ScoreSummary)


@dataclass
class RepoAudit:
    repo_name: str
    summary: str = ""
    what_it_does: str = ""
    key_technologies: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    showcase_value: str = ""
    recruiter_signal: str = ""


@dataclass
class PortfolioSummary:
    summary: str = ""
    strongest_repos: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    top_actions: List[str] = field(default_factory=list)


@dataclass
class PortfolioReport:
    github_username: str
    repo_count: int
    feedback_markdown: str
    analysis_label: str = ""
    cache_hit: bool = False
    cache_status: str = ""
    cache_saved_at: str = ""
    repo_facts: List[RepoFacts] = field(default_factory=list)
    repo_checks: List[RepoCheckResult] = field(default_factory=list)
    repo_audits: List[RepoAudit] = field(default_factory=list)
    portfolio_summary: PortfolioSummary = field(default_factory=PortfolioSummary)
    portfolio_score: ScoreSummary = field(default_factory=ScoreSummary)
