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

---

## Next Steps

- GitHub OAuth for real-user authorization
- deployment setup for public usage
- further PDF/report-template polish
- broader tests around GitHub parsing and model failure handling
