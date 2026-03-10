# DEVLOG.md - GitHub Portfolio Reviewer Agent

This log tracks the major implementation milestones for the current modular Streamlit app.

---

## March 7, 2026 - Modular Audit Pipeline

Implemented the current application architecture:

- moved GitHub API logic into `src/github_client.py`
- moved deterministic checks into `src/repo_checks.py`
- moved prompt and OpenAI logic into `src/prompts.py` and `src/openai_service.py`
- added shared schemas in `src/schemas.py`
- added orchestration in `src/report_builder.py`
- kept `app.py` focused on Streamlit UI and flow control

This replaced the earlier single-file prototype and made the app testable and easier to extend.

## March 7, 2026 - Scoped Analysis and Scoring

Added the main user-facing audit features:

- single-repository analysis
- selected-repository analysis
- portfolio-slice analysis
- deterministic scoring across documentation, discoverability, engineering, maintenance, and originality
- portfolio-level summary plus per-repo audits

The output is now structured enough to be used as a real GitHub improvement plan instead of a generic LLM summary.

## March 7, 2026 - UI and Export Cleanup

Improved the Streamlit experience and export flow:

- polished the audit dashboard layout
- fixed broken HTML/CSS rendering issues in the UI
- simplified audit labels to `Findings` and `Positive Signals`
- reduced download formats to Markdown and PDF
- rebuilt PDF export to handle headings, paragraphs, and bullet lists more cleanly

## March 8, 2026 - Repository Cleanup

Removed obsolete files from the older prototype:

- deleted the legacy CLI script `analyze_github_profile.py`
- deleted `generate_suggestions_files.py`
- deleted the tracked `suggestions/` markdown artifacts
- updated root documentation so it reflects the current app instead of the initial prototype

## March 8, 2026 - GitHub OAuth Sign-In

Added the first production-facing auth upgrade:

- added GitHub OAuth app configuration support via environment variables or local ignored files
- added browser-based GitHub sign-in flow in the Streamlit UI
- stored the authenticated GitHub login in session flow so a signed-in user can analyze their own public repositories
- kept the OAuth scope limited to public-profile access rather than broad private-repo permissions
- added auth-focused tests and removed unused dependencies from `requirements.txt`

## March 8, 2026 - Public-Only Auth and PDF Polish

Tightened the app around the public-facing product direction:

- removed the legacy local GitHub token access path from the fetch pipeline
- kept repository loading strictly public-username based, including signed-in self-analysis
- expanded test coverage for GitHub client failures and exporter behavior
- rebuilt the PDF exporter to produce cleaner hierarchy, list rendering, separators, and page footers
- upgraded PDF generation to use browser-rendered HTML/CSS via Playwright with a ReportLab fallback

## March 9, 2026 - PDF Layout Hardening

Stabilized export quality so Markdown structure renders more consistently across reports:

- normalized ordered-list and nested-list rendering in the PDF output
- improved spacing behavior for bullet sections such as `Strengths`, `Weaknesses`, and `Top Priority Actions`
- changed report accent styling from green to blue for a more formal presentation
- prevented orphaned section headings where possible during page breaks
- added stronger exporter regression tests around list parsing and layout edge cases

## March 9, 2026 - Deterministic Single-Repo Reports

Replaced the final freeform single-repository rewrite step with a fixed report template:

- kept repo-level analysis content sourced from structured `RepoAudit` output
- formatted `Strengths` and `Weaknesses` as bullet items with bold lead phrases and explanations
- formatted `Top Priority Actions` as stable numbered actions
- kept `Findings` tied to deterministic checks rather than expanded narrative
- reduced repo-to-repo formatting drift in exported Markdown and PDF reports

## March 10, 2026 - Deterministic Portfolio Reports

Applied the same report-structure discipline to multi-repository analysis:

- removed the final freeform portfolio rewrite step
- rendered portfolio reports directly from `PortfolioSummary`, per-repo `RepoAudit`, and deterministic findings
- standardized portfolio `Top Actions`, per-repo `Recommendations`, and per-repo `Findings`
- kept multi-repo content rich while making section layout uniform across different portfolios

## March 10, 2026 - Report Identification and Header Clarity

Improved the beginning of single-repository exports so the target repository is obvious:

- added the repository name directly below the main `GitHub Repository Audit` title
- made it clear which repository a single-repo report belongs to before the score section starts
- added tests to lock in the updated header structure

## March 10, 2026 - Persistent Analysis Cache

Added the first durable caching layer for repeated analysis runs:

- added a SQLite-backed analysis store in `src/analysis_store.py`
- cache keys now include analysis scope and are invalidated using repository `updated_at`, default branch, and default-branch head commit SHA
- repository facts now capture the latest default-branch commit SHA from GitHub
- completed reports are now reused across browser sessions when the repository fingerprint has not changed
- added regression tests for cache round-trips, cached-report reuse, and commit-SHA fetch behavior

---

## Next Steps

- deployment setup for public usage
- further performance and rate-limit resilience improvements
- broader tests around GitHub parsing and model failure handling
