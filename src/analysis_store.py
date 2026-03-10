import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256

from src.config import ANALYSIS_CACHE_DB_PATH, ANALYSIS_CACHE_VERSION
from src.schemas import (
    PortfolioReport,
    PortfolioSummary,
    RepoAudit,
    RepoCheckResult,
    RepoFacts,
    ScoreSummary,
)


def _connect(db_path=None):
    target_path = db_path or ANALYSIS_CACHE_DB_PATH
    connection = sqlite3.connect(target_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_analysis_store(db_path=None):
    with _connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_cache (
                analysis_key TEXT PRIMARY KEY,
                github_username TEXT NOT NULL,
                freshness_signature TEXT NOT NULL,
                analysis_version TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _hash_payload(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def build_analysis_key(github_username, selected_repo_names, max_repos, skip_forks):
    payload = {
        "analysis_version": ANALYSIS_CACHE_VERSION,
        "github_username": (github_username or "").strip().lower(),
        "selected_repo_names": list(selected_repo_names or []),
        "max_repos": max_repos,
        "skip_forks": bool(skip_forks),
    }
    return _hash_payload(payload)


def build_freshness_signature(repo_facts):
    payload = [
        {
            "name": repo.name,
            "owner_login": repo.owner_login,
            "updated_at": repo.updated_at,
            "default_branch": repo.default_branch,
            "default_branch_head_sha": repo.default_branch_head_sha,
        }
        for repo in repo_facts
    ]
    return _hash_payload(payload)


def _score_from_payload(payload):
    return ScoreSummary(
        overall=payload.get("overall", 0),
        label=payload.get("label", ""),
        category_scores=dict(payload.get("category_scores", {})),
    )


def _repo_facts_from_payload(payload):
    return RepoFacts(
        name=payload["name"],
        description=payload.get("description", ""),
        owner_login=payload.get("owner_login", ""),
        html_url=payload.get("html_url", ""),
        language=payload.get("language", ""),
        topics=list(payload.get("topics", [])),
        homepage=payload.get("homepage", ""),
        updated_at=payload.get("updated_at", ""),
        stargazers_count=payload.get("stargazers_count", 0),
        forks_count=payload.get("forks_count", 0),
        open_issues_count=payload.get("open_issues_count", 0),
        license_name=payload.get("license_name", ""),
        default_branch=payload.get("default_branch", ""),
        default_branch_head_sha=payload.get("default_branch_head_sha", ""),
        repo_size_kb=payload.get("repo_size_kb", 0),
        is_fork=bool(payload.get("is_fork", False)),
        languages=dict(payload.get("languages", {})),
        root_entries=list(payload.get("root_entries", [])),
        readme_present=bool(payload.get("readme_present", False)),
        readme_text=payload.get("readme_text", ""),
    )


def _repo_check_from_payload(payload):
    return RepoCheckResult(
        repo_name=payload["repo_name"],
        findings=list(payload.get("findings", [])),
        strengths=list(payload.get("strengths", [])),
        score=_score_from_payload(payload.get("score", {})),
    )


def _repo_audit_from_payload(payload):
    return RepoAudit(
        repo_name=payload["repo_name"],
        summary=payload.get("summary", ""),
        what_it_does=payload.get("what_it_does", ""),
        key_technologies=list(payload.get("key_technologies", [])),
        strengths=list(payload.get("strengths", [])),
        weaknesses=list(payload.get("weaknesses", [])),
        recommendations=list(payload.get("recommendations", [])),
        showcase_value=payload.get("showcase_value", ""),
        recruiter_signal=payload.get("recruiter_signal", ""),
    )


def _portfolio_summary_from_payload(payload):
    return PortfolioSummary(
        summary=payload.get("summary", ""),
        strongest_repos=list(payload.get("strongest_repos", [])),
        improvement_areas=list(payload.get("improvement_areas", [])),
        top_actions=list(payload.get("top_actions", [])),
    )


def _report_from_payload(payload):
    return PortfolioReport(
        github_username=payload["github_username"],
        repo_count=payload["repo_count"],
        feedback_markdown=payload.get("feedback_markdown", ""),
        analysis_label=payload.get("analysis_label", ""),
        repo_facts=[_repo_facts_from_payload(item) for item in payload.get("repo_facts", [])],
        repo_checks=[_repo_check_from_payload(item) for item in payload.get("repo_checks", [])],
        repo_audits=[_repo_audit_from_payload(item) for item in payload.get("repo_audits", [])],
        portfolio_summary=_portfolio_summary_from_payload(payload.get("portfolio_summary", {})),
        portfolio_score=_score_from_payload(payload.get("portfolio_score", {})),
    )


def load_cached_report(analysis_key, freshness_signature, db_path=None):
    initialize_analysis_store(db_path=db_path)

    with _connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT report_json
            FROM analysis_cache
            WHERE analysis_key = ?
              AND freshness_signature = ?
              AND analysis_version = ?
            """,
            (analysis_key, freshness_signature, ANALYSIS_CACHE_VERSION),
        ).fetchone()

    if not row:
        return None

    payload = json.loads(row["report_json"])
    return _report_from_payload(payload)


def save_cached_report(analysis_key, github_username, freshness_signature, report, db_path=None):
    initialize_analysis_store(db_path=db_path)
    serialized_report = json.dumps(asdict(report), ensure_ascii=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO analysis_cache (
                analysis_key,
                github_username,
                freshness_signature,
                analysis_version,
                report_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(analysis_key) DO UPDATE SET
                github_username = excluded.github_username,
                freshness_signature = excluded.freshness_signature,
                analysis_version = excluded.analysis_version,
                report_json = excluded.report_json,
                updated_at = excluded.updated_at
            """,
            (
                analysis_key,
                (github_username or "").strip().lower(),
                freshness_signature,
                ANALYSIS_CACHE_VERSION,
                serialized_report,
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
