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

## March 10, 2026 - Cache-Aware UI

Made the persistence layer visible in the product experience:

- added cache status messaging so users can see whether a report was loaded from persistent cache or freshly generated
- added a `Force refresh analysis` control to bypass cached results and rerun the audit
- kept the saved-report path explicit instead of silently reusing prior results

## March 10, 2026 - Failure Handling and Graceful Fallbacks

Improved robustness across the most common failure cases:

- added shared typed application errors in `src/errors.py`
- surfaced clearer GitHub API, OAuth, OpenAI, and export error messages in the UI
- added deterministic fallback behavior when portfolio synthesis or repo analysis fails
- made export failures and inaccessible repositories fail more cleanly instead of producing vague errors

## March 10, 2026 - GitHub Fetch Performance and Retry Handling

Improved backend responsiveness and resilience for larger analyses:

- parallelized repository detail fetching with low-concurrency workers
- added retry handling for transient GitHub failures
- respected GitHub retry hints such as rate-limit reset timing where available
- preserved stable repository ordering despite parallel fetch execution

## March 10, 2026 - Expanded Edge-Case Test Coverage

Broadened automated coverage around non-happy-path behavior:

- added OpenAI service tests for invalid JSON, wrapped request failures, and payload normalization
- added exporter tests for dual-backend PDF failure handling
- added OAuth tests for authenticated-user fetch failures
- added report-builder tests for repo-analysis fallback warnings and deterministic output guarantees

## March 10, 2026 - Docs and Sample Asset Refresh

Updated repository-facing documentation to match the current product:

- refreshed README screenshots to reflect the current UI, cache flow, and report exports
- added current sample reports under `docs/reports/`
- removed outdated screenshot assets that reflected older app states

## March 10, 2026 - Architecture Decision Records

Added explicit decision records for the app's major product and architecture choices:

- documented the public-only GitHub OAuth scope decision
- documented the move to deterministic final report formatting
- documented the SQLite-backed persistent cache with repo freshness fingerprints
- documented the Playwright-based HTML/CSS PDF rendering choice with ReportLab fallback

## March 10, 2026 - Architecture and Config Docs

Rounded out the repository documentation with operational references:

- added `.env.example` to show the supported deployment-oriented environment variables
- added `docs/architecture.md` with a high-level walkthrough of runtime flow, modules, cache design, auth model, and export pipeline
- kept `DEVLOG.md` at the repository root so change history stays easy to discover alongside `README.md`

## March 10, 2026 - UI Interaction and Demo Asset Polish

Improved the last visible friction points in the local app flow and refreshed demo assets:

- kept the GitHub OAuth authorize flow in the same browser tab instead of opening a new tab
- changed the username-to-repository-load interaction to use a Streamlit form so the typed username submits cleanly on the first click
- aligned the `Load Repositories` form-submit button styling with the rest of the UI button system
- removed a flashing `Download Report` heading that appeared during export-format rerenders
- added focused demo recordings for GitHub OAuth sign-in and single-repository analysis/report download
- kept the large full-workflow video out of git history and linked it from the README as an external Google Drive demo

## March 11, 2026 - Hosted OAuth Flow and Download UX

Hardened the hosted Streamlit experience around GitHub sign-in and report export:

- bridged Streamlit secrets into runtime environment loading so hosted OAuth configuration is detected consistently
- moved hosted GitHub OAuth to Streamlit's native link-button flow and aligned the sign-in button styling with the rest of the UI
- changed hosted OAuth state validation to use a signed, self-validating state so callbacks work across new tabs and fresh hosted sessions
- clarified the signed-in guidance so users know they can continue in the authenticated tab, close the previous tab, and click `Load Repositories`
- simplified the public-username input copy and removed redundant helper text below the repository form
- kept repository-audit expander headers visually stable after interaction in the multi-repo report view
- changed PDF export so the expensive PDF generation starts only when the user clicks the download button instead of when they merely switch the format selector

---

## Next Steps

- deployment setup for public usage
- final deployment-oriented configuration and secrets hardening
- update the GitHub OAuth callback URL and verify browser sign-in on the deployed app
- validate end-to-end hosted flows for single-repo, multi-repo, cache hit, force refresh, and export behavior
- decide whether SQLite remains sufficient for hosted single-instance use or needs to be replaced later
- future product upgrade path: optional repository RAG / Q&A mode for deeper codebase exploration
