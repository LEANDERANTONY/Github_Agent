from concurrent.futures import ThreadPoolExecutor

from src.config import REPO_ANALYSIS_MAX_WORKERS
from src.github_client import get_portfolio_repo_facts
from src.openai_service import analyze_repo, summarize_portfolio
from src.repo_checks import build_portfolio_score, run_repo_checks
from src.schemas import PortfolioReport, PortfolioSummary, RepoAudit


def _update_progress(progress_callback, message, value):
    if progress_callback:
        progress_callback(message, value)


def _split_emphasis_text(text):
    cleaned = str(text or "").strip()
    if not cleaned:
        return "", ""

    parts = cleaned.split(": ", 1)
    if len(parts) != 2:
        return "", cleaned

    title, detail = parts[0].strip(), parts[1].strip()
    if not title or not detail:
        return "", cleaned

    if len(title) > 90 or "http" in title.lower():
        return "", cleaned

    return title, detail


def _format_emphasized_bullets(items, default_message):
    normalized_items = items or [default_message]
    lines = []

    for item in normalized_items:
        title, detail = _split_emphasis_text(item)
        if title:
            lines.append("- **{title}**: {detail}".format(title=title, detail=detail))
        else:
            lines.append("- {item}".format(item=item))

    return lines


def _format_priority_actions(items):
    normalized_items = items or ["No recommendations generated."]
    lines = []

    for index, item in enumerate(normalized_items, start=1):
        title, detail = _split_emphasis_text(item)
        if title:
            lines.append("{index}. **{title}**: {detail}".format(index=index, title=title, detail=detail))
        else:
            lines.append("{index}. {item}".format(index=index, item=item))

    return lines


def _format_markdown_report(report):
    if report.repo_count == 1 and report.repo_audits:
        repo_audit = report.repo_audits[0]
        repo_check = report.repo_checks[0]
        lines = [
            "# GitHub Repository Audit",
            "",
            "**Repository**",
            repo_audit.repo_name,
            "",
            "## Repository Score",
            "{score}/100 ({label})".format(
                score=repo_check.score.overall,
                label=repo_check.score.label,
            ),
            "",
            "## Repository Summary",
            repo_audit.summary or "No summary generated.",
            "",
            "**What It Does**",
            repo_audit.what_it_does or "Not enough information.",
            "",
            "**Score Breakdown**",
        ]
        for category, score in repo_check.score.category_scores.items():
            lines.append("- {category}: {score}/100".format(category=category, score=score))
        lines.extend(
            [
                "",
                "**Key Technologies**",
            ]
        )
        technologies = repo_audit.key_technologies or ["Not identified."]
        lines.extend("- {item}".format(item=item) for item in technologies)
        lines.extend(["", "## Strengths"])
        lines.extend(
            _format_emphasized_bullets(
                repo_audit.strengths,
                "No strengths generated.",
            )
        )
        lines.extend(["", "## Weaknesses"])
        lines.extend(
            _format_emphasized_bullets(
                repo_audit.weaknesses,
                "No weaknesses generated.",
            )
        )
        lines.extend(["", "## Top Priority Actions"])
        lines.extend(_format_priority_actions(repo_audit.recommendations))
        lines.extend(
            [
                "",
                "**Showcase Value**",
                repo_audit.showcase_value or "Not rated.",
                "",
                "**Recruiter Signal**",
                repo_audit.recruiter_signal or "Not rated.",
                "",
                "## Findings",
            ]
        )
        findings = repo_check.findings or ["No findings."]
        lines.extend("- {item}".format(item=item) for item in findings)
        return "\n".join(lines).strip()

    lines = [
        "# GitHub Portfolio Audit",
        "",
        "## Portfolio Score",
        "{score}/100 ({label})".format(
            score=report.portfolio_score.overall,
            label=report.portfolio_score.label,
        ),
        "",
        "### Score Breakdown",
    ]
    for category, score in report.portfolio_score.category_scores.items():
        lines.append("- {category}: {score}/100".format(category=category, score=score))
    lines.extend(["", "## Portfolio Summary", report.portfolio_summary.summary, "", "### Strongest Repositories"])

    strongest_repos = report.portfolio_summary.strongest_repos or ["No strongest repositories identified."]
    lines.extend("- {item}".format(item=item) for item in strongest_repos)
    lines.extend(["", "### Improvement Areas"])

    improvement_areas = report.portfolio_summary.improvement_areas or ["No improvement areas identified."]
    lines.extend("- {item}".format(item=item) for item in improvement_areas)
    lines.extend(["", "### Top Actions"])

    lines.extend(
        _format_priority_actions(
            report.portfolio_summary.top_actions or ["No top actions identified."]
        )
    )
    lines.extend(["", "## Repository Audits"])

    for repo_audit, repo_check in zip(report.repo_audits, report.repo_checks):
        lines.extend(
            [
                "",
                "### {name}".format(name=repo_audit.repo_name),
                "",
                "**Score**",
                "{score}/100 ({label})".format(
                    score=repo_check.score.overall,
                    label=repo_check.score.label,
                ),
                "",
                "**Summary**",
                repo_audit.summary or "No summary generated.",
                "",
                "**What It Does**",
                repo_audit.what_it_does or "Not enough information.",
                "",
                "**Key Technologies**",
            ]
        )
        technologies = repo_audit.key_technologies or ["Not identified."]
        lines.extend("- {item}".format(item=item) for item in technologies)
        lines.extend(["", "**Strengths**"])
        lines.extend(
            _format_emphasized_bullets(
                repo_audit.strengths,
                "No strengths generated.",
            )
        )
        lines.extend(["", "**Weaknesses**"])
        lines.extend(
            _format_emphasized_bullets(
                repo_audit.weaknesses,
                "No weaknesses generated.",
            )
        )
        lines.extend(["", "**Recommendations**"])
        lines.extend(_format_priority_actions(repo_audit.recommendations))
        lines.extend(
            [
                "",
                "**Showcase Value**",
                repo_audit.showcase_value or "Not rated.",
                "",
                "**Recruiter Signal**",
                repo_audit.recruiter_signal or "Not rated.",
                "",
                "**Findings**",
            ]
        )
        findings = repo_check.findings or ["No findings."]
        lines.extend("- {item}".format(item=item) for item in findings)

    return "\n".join(lines).strip()


def _fallback_repo_audit(repo_fact, repo_check, error):
    fallback_recommendations = repo_check.findings[:3] or [
        "Retry the LLM analysis after checking API availability."
    ]
    return RepoAudit(
        repo_name=repo_fact.name,
        summary="Automated repo analysis was unavailable for this repository.",
        what_it_does=repo_fact.description,
        key_technologies=list(repo_fact.languages.keys())[:5],
        strengths=repo_check.strengths[:5],
        weaknesses=repo_check.findings[:5],
        recommendations=fallback_recommendations,
        showcase_value="Not rated because the LLM analysis step failed.",
        recruiter_signal="LLM analysis unavailable: {error}".format(error=str(error)),
    )


def _analyze_repo_pair(repo_fact, repo_check):
    try:
        return analyze_repo(repo_fact, repo_check)
    except Exception as error:
        return _fallback_repo_audit(repo_fact, repo_check, error)


def build_portfolio_feedback(
    github_username="",
    selected_repo_names=None,
    max_repos=None,
    skip_forks=False,
    repo_facts=None,
    progress_callback=None,
):
    normalized_username = (github_username or "").strip()
    _update_progress(progress_callback, "Fetching repository facts...", 10)
    if repo_facts is None:
        repo_facts = get_portfolio_repo_facts(
            username=normalized_username or None,
            selected_repo_names=selected_repo_names,
            max_repos=max_repos,
            skip_forks=skip_forks,
        )

    _update_progress(progress_callback, "Running deterministic checks...", 30)
    repo_checks = [run_repo_checks(repo_fact) for repo_fact in repo_facts]
    max_workers = min(REPO_ANALYSIS_MAX_WORKERS, max(1, len(repo_facts)))

    _update_progress(progress_callback, "Generating repository analyses...", 55)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        repo_audits = list(
            executor.map(
                _analyze_repo_pair,
                repo_facts,
                repo_checks,
            )
        )

    portfolio_summary = PortfolioSummary()
    analysis_label = "Selected Repository Analysis" if len(repo_facts) == 1 else "Portfolio Analysis"

    if len(repo_audits) > 1:
        _update_progress(progress_callback, "Generating portfolio summary...", 75)
        portfolio_summary = summarize_portfolio(repo_audits, repo_checks)

    report = PortfolioReport(
        github_username=normalized_username or "my",
        repo_count=len(repo_facts),
        feedback_markdown="",
        analysis_label=analysis_label,
        repo_facts=repo_facts,
        repo_checks=repo_checks,
        repo_audits=repo_audits,
        portfolio_summary=portfolio_summary,
        portfolio_score=build_portfolio_score(repo_checks),
    )
    _update_progress(progress_callback, "Building final report...", 90)
    report.feedback_markdown = _format_markdown_report(report)
    _update_progress(progress_callback, "Analysis complete.", 100)
    return report
