def _truncate_readme(text, limit=600):
    cleaned = " ".join(text.split())
    return cleaned[:limit]


def _format_repo_facts(repo):
    return "\n".join(
        [
            "Repository: {name}".format(name=repo.name),
            "Description: {description}".format(description=repo.description),
            "Primary language: {language}".format(
                language=repo.language or "Not detected"
            ),
            "Languages: {languages}".format(
                languages=", ".join(repo.languages.keys()) or "Not detected"
            ),
            "Topics: {topics}".format(
                topics=", ".join(repo.topics) or "None"
            ),
            "Homepage: {homepage}".format(homepage=repo.homepage or "None"),
            "License: {license_name}".format(
                license_name=repo.license_name or "None"
            ),
            "Stars: {stars}, Forks: {forks}, Open issues: {issues}".format(
                stars=repo.stargazers_count,
                forks=repo.forks_count,
                issues=repo.open_issues_count,
            ),
            "Updated at: {updated_at}".format(updated_at=repo.updated_at or "Unknown"),
            "Repository size (KB): {size}".format(size=repo.repo_size_kb),
            "Fork: {is_fork}".format(is_fork="Yes" if repo.is_fork else "No"),
            "Root entries: {root_entries}".format(
                root_entries=", ".join(repo.root_entries[:20]) or "None"
            ),
            "README present: {readme_present}".format(
                readme_present="Yes" if repo.readme_present else "No"
            ),
            "README excerpt: {readme_excerpt}".format(
                readme_excerpt=_truncate_readme(repo.readme_text, limit=1200)
                or "No README content"
            ),
        ]
    )


def _format_repo_checks(repo_check):
    findings = repo_check.findings or ["None"]
    strengths = repo_check.strengths or ["None"]
    return "\n".join(
        [
            "Deterministic strengths:",
            "\n".join("- {item}".format(item=item) for item in strengths),
            "Deterministic findings:",
            "\n".join("- {item}".format(item=item) for item in findings),
        ]
    )


def build_repo_audit_prompt(repo_facts, repo_check):
    return (
        "You are reviewing a single GitHub repository for portfolio quality. "
        "Use the repository metadata, README excerpt, and deterministic checks below. "
        "Return a JSON object with these exact keys: "
        "summary, what_it_does, key_technologies, strengths, weaknesses, recommendations, "
        "showcase_value, recruiter_signal. "
        "The summary, what_it_does, showcase_value, and recruiter_signal fields must be strings. "
        "Each list should contain concise items. "
        "Ground the analysis in the provided facts and avoid inventing implementation details.\n\n"
        + _format_repo_facts(repo_facts)
        + "\n\n"
        + _format_repo_checks(repo_check)
    )


def build_portfolio_summary_prompt(repo_audits, repo_checks):
    repo_blocks = []

    for repo_audit, repo_check in zip(repo_audits, repo_checks):
        repo_blocks.append(
            "\n".join(
                [
                    "Repository: {name}".format(name=repo_audit.repo_name),
                    "Summary: {summary}".format(summary=repo_audit.summary),
                    "Showcase value: {showcase_value}".format(
                        showcase_value=repo_audit.showcase_value
                    ),
                    "Recruiter signal: {recruiter_signal}".format(
                        recruiter_signal=repo_audit.recruiter_signal
                    ),
                    "Top strengths: {strengths}".format(
                        strengths=", ".join(repo_audit.strengths[:3]) or "None"
                    ),
                    "Top weaknesses: {weaknesses}".format(
                        weaknesses=", ".join(repo_audit.weaknesses[:3]) or "None"
                    ),
                    "Top recommendations: {recommendations}".format(
                        recommendations=", ".join(repo_audit.recommendations[:3]) or "None"
                    ),
                    "Deterministic findings: {findings}".format(
                        findings=", ".join(repo_check.findings[:4]) or "None"
                    ),
                ]
            )
        )

    return (
        "You are reviewing an entire GitHub portfolio made up of multiple repositories. "
        "Return a JSON object with these exact keys: summary, strongest_repos, "
        "improvement_areas, top_actions. "
        "The summary field must be a string. The strongest_repos, improvement_areas, and "
        "top_actions fields must each be arrays of plain strings only. "
        "Use the repository-level audit outputs and findings below.\n\n"
        + "\n\n".join(repo_blocks)
    )


def build_final_report_prompt(report):
    if report.repo_count == 1 and report.repo_audits:
        repo_audit = report.repo_audits[0]
        repo_check = report.repo_checks[0]
        return (
            "You are writing the final polished audit report for a single GitHub repository. "
            "Return clean Markdown only. "
            "Use these headings exactly: '# GitHub Repository Audit', "
            "'## Repository Summary', '## Strengths', '## Weaknesses', "
            "'## Top Priority Actions', and '## Deterministic Findings'. "
            "Do not invent facts not present in the input.\n\n"
            "Repository: {name}\n"
            "Summary: {summary}\n"
            "What it does: {what_it_does}\n"
            "Key technologies: {tech}\n"
            "Strengths: {strengths}\n"
            "Weaknesses: {weaknesses}\n"
            "Recommendations: {recommendations}\n"
            "Showcase value: {showcase_value}\n"
            "Recruiter signal: {recruiter_signal}\n"
            "Deterministic findings: {findings}".format(
                name=repo_audit.repo_name,
                summary=repo_audit.summary,
                what_it_does=repo_audit.what_it_does,
                tech=" | ".join(repo_audit.key_technologies) or "None",
                strengths=" | ".join(repo_audit.strengths) or "None",
                weaknesses=" | ".join(repo_audit.weaknesses) or "None",
                recommendations=" | ".join(repo_audit.recommendations) or "None",
                showcase_value=repo_audit.showcase_value,
                recruiter_signal=repo_audit.recruiter_signal,
                findings=" | ".join(repo_check.findings) or "None",
            )
        )

    repo_blocks = []

    for repo_audit, repo_check in zip(report.repo_audits, report.repo_checks):
        repo_blocks.append(
            "\n".join(
                [
                    "Repository: {name}".format(name=repo_audit.repo_name),
                    "Summary: {summary}".format(summary=repo_audit.summary),
                    "What it does: {what_it_does}".format(
                        what_it_does=repo_audit.what_it_does
                    ),
                    "Key technologies: {tech}".format(
                        tech=", ".join(repo_audit.key_technologies) or "Not identified"
                    ),
                    "Strengths: {strengths}".format(
                        strengths=" | ".join(repo_audit.strengths) or "None"
                    ),
                    "Weaknesses: {weaknesses}".format(
                        weaknesses=" | ".join(repo_audit.weaknesses) or "None"
                    ),
                    "Recommendations: {recommendations}".format(
                        recommendations=" | ".join(repo_audit.recommendations) or "None"
                    ),
                    "Showcase value: {showcase_value}".format(
                        showcase_value=repo_audit.showcase_value
                    ),
                    "Recruiter signal: {recruiter_signal}".format(
                        recruiter_signal=repo_audit.recruiter_signal
                    ),
                    "Deterministic findings: {findings}".format(
                        findings=" | ".join(repo_check.findings) or "None"
                    ),
                ]
            )
        )

    return (
        "You are writing the final polished GitHub portfolio audit report for a developer. "
        "Use the structured portfolio summary and repository audits below. "
        "Return clean Markdown only. "
        "Write concise, professional, recruiter-friendly sections with these headings exactly: "
        "'# GitHub Portfolio Audit', '## Executive Summary', '## Strongest Repositories', "
        "'## Improvement Areas', '## Top Priority Actions', and '## Repository Audits'. "
        "Under each repository in '## Repository Audits', include: Summary, What It Does, "
        "Key Technologies, Strengths, Weaknesses, Recommendations, Showcase Value, "
        "Recruiter Signal, and Deterministic Findings. "
        "Do not invent facts not present in the input.\n\n"
        "Portfolio summary:\n"
        "Summary: {summary}\n"
        "Strongest repositories: {strongest}\n"
        "Improvement areas: {improvement}\n"
        "Top actions: {actions}\n\n"
        "Repository audits:\n\n{repo_blocks}".format(
            summary=report.portfolio_summary.summary,
            strongest=" | ".join(report.portfolio_summary.strongest_repos) or "None",
            improvement=" | ".join(report.portfolio_summary.improvement_areas) or "None",
            actions=" | ".join(report.portfolio_summary.top_actions) or "None",
            repo_blocks="\n\n".join(repo_blocks),
        )
    )
