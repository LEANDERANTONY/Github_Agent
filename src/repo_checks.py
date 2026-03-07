from datetime import datetime, timedelta, timezone

from src.schemas import RepoCheckResult, RepoFacts, ScoreSummary


TEST_HINTS = {
    "tests",
    "test",
    "__tests__",
    "spec",
    "specs",
    "pytest.ini",
    "tox.ini",
    "jest.config.js",
    "vitest.config.ts",
}

SETUP_HINTS = {
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "pom.xml",
    "build.gradle",
    "Cargo.toml",
    "go.mod",
    "environment.yml",
    "dockerfile",
    "docker-compose.yml",
}

CI_HINTS = {
    ".github",
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    ".circleci",
}

CATEGORY_WEIGHTS = {
    "Documentation": 0.30,
    "Discoverability": 0.20,
    "Engineering": 0.25,
    "Maintenance": 0.15,
    "Originality": 0.10,
}


def _normalize_root_entries(repo_facts):
    return {entry.lower() for entry in repo_facts.root_entries}


def _readme_is_thin(repo_facts):
    return len(repo_facts.readme_text.strip()) < 200


def _is_stale(repo_facts, days=365):
    if not repo_facts.updated_at:
        return False

    updated_at = datetime.strptime(repo_facts.updated_at, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    return updated_at < datetime.now(timezone.utc) - timedelta(days=days)


def _score_label(score):
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Strong"
    if score >= 55:
        return "Fair"
    return "Needs Work"


def _has_root_hint(root_entries, hints):
    return bool(root_entries.intersection(hints))


def _build_repo_score(repo_facts, root_entries):
    documentation = 0
    if repo_facts.description != "No description":
        documentation += 20
    if repo_facts.readme_present:
        documentation += 50
        if not _readme_is_thin(repo_facts):
            documentation += 20
    if repo_facts.homepage:
        documentation += 10

    discoverability = 0
    if repo_facts.topics:
        discoverability += 40
    if repo_facts.license_name:
        discoverability += 30
    if repo_facts.homepage:
        discoverability += 30

    engineering = 0
    if repo_facts.languages:
        engineering += 20
    if _has_root_hint(root_entries, SETUP_HINTS):
        engineering += 30
    if _has_root_hint(root_entries, TEST_HINTS):
        engineering += 30
    if _has_root_hint(root_entries, CI_HINTS):
        engineering += 20

    maintenance = 0
    if repo_facts.updated_at:
        maintenance += 20
    if not _is_stale(repo_facts):
        maintenance += 50
    if repo_facts.repo_size_kb >= 20:
        maintenance += 15
    if repo_facts.default_branch:
        maintenance += 15

    originality = 40 if repo_facts.is_fork else 100

    category_scores = {
        "Documentation": documentation,
        "Discoverability": discoverability,
        "Engineering": engineering,
        "Maintenance": maintenance,
        "Originality": originality,
    }

    overall = round(
        sum(category_scores[name] * weight for name, weight in CATEGORY_WEIGHTS.items())
    )
    return ScoreSummary(
        overall=overall,
        label=_score_label(overall),
        category_scores=category_scores,
    )


def build_portfolio_score(repo_checks):
    if not repo_checks:
        return ScoreSummary()

    category_totals = {}
    for repo_check in repo_checks:
        for category, score in repo_check.score.category_scores.items():
            category_totals[category] = category_totals.get(category, 0) + score

    category_scores = {
        category: round(total / len(repo_checks))
        for category, total in category_totals.items()
    }
    overall = round(sum(repo_check.score.overall for repo_check in repo_checks) / len(repo_checks))
    return ScoreSummary(
        overall=overall,
        label=_score_label(overall),
        category_scores=category_scores,
    )


def run_repo_checks(repo_facts):
    root_entries = _normalize_root_entries(repo_facts)
    findings = []
    strengths = []

    if repo_facts.description == "No description":
        findings.append("Missing repository description.")
    else:
        strengths.append("Repository description is present.")

    if repo_facts.readme_present:
        strengths.append("README file detected.")
        if _readme_is_thin(repo_facts):
            findings.append("README exists but looks too short to explain the project well.")
    else:
        findings.append("No README detected.")

    if repo_facts.homepage:
        strengths.append("Homepage or live demo link is configured.")
    else:
        findings.append("No homepage or live demo link set.")

    if repo_facts.topics:
        strengths.append("GitHub topics are configured.")
    else:
        findings.append("No GitHub topics configured.")

    if repo_facts.license_name:
        strengths.append("Repository license is configured.")
    else:
        findings.append("No license detected.")

    if repo_facts.languages:
        strengths.append("Language breakdown is available.")
    else:
        findings.append("Could not detect repository languages.")

    if repo_facts.repo_size_kb < 20:
        findings.append("Repository is very small and may look incomplete.")

    if repo_facts.is_fork:
        findings.append("Repository is a fork, which may reduce portfolio originality unless your contribution is clarified.")

    if _is_stale(repo_facts):
        findings.append("Repository has not been updated in over a year.")

    if root_entries.intersection(TEST_HINTS):
        strengths.append("Test-related files or directories are present.")
    else:
        findings.append("No obvious test files or test directories detected at the repository root.")

    if root_entries.intersection(SETUP_HINTS):
        strengths.append("Setup or dependency files are present at the repository root.")
    else:
        findings.append("No obvious setup or dependency manifest detected at the repository root.")

    if root_entries.intersection(CI_HINTS):
        strengths.append("Repository appears to include CI or automation configuration.")
    else:
        findings.append("No obvious CI or automation configuration detected.")

    score = _build_repo_score(repo_facts, root_entries)

    return RepoCheckResult(
        repo_name=repo_facts.name,
        findings=findings,
        strengths=strengths,
        score=score,
    )
