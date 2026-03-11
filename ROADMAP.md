# Roadmap

This file captures the longer-term product direction for GitHub Portfolio Reviewer Agent.

It is intentionally vision-oriented rather than time-based.

## Current Foundation

The project already has:

- a hosted Streamlit app
- deterministic repository scoring
- per-repository and portfolio-level LLM analysis
- persistent SQLite-backed caching for single-instance hosting
- Markdown and PDF export
- GitHub OAuth for public-profile convenience
- baseline GitHub Actions CI

## Product Direction

### 1. Stronger Repository Presentation

Keep improving the recruiter-facing polish of the repository and the product:

- refine README screenshots and demo assets as the UI evolves
- keep exported reports visually stronger and more branded
- improve documentation around setup, testing, and expected outputs
- add clearer badges and public signals that make the repo easier to evaluate quickly

### 2. Production-Grade Backend and Hosting Model

The current app is a strong hosted prototype, but the long-term direction is a more explicit application backend:

- move from a Streamlit-only runtime toward a dedicated backend layer where appropriate
- introduce a FastAPI service for analysis orchestration, background jobs, and cleaner API boundaries
- support a more standard production deployment model beyond a single hosted Streamlit instance
- separate frontend presentation concerns from backend execution and persistence concerns

### 3. Shared Persistence Instead of Local SQLite

SQLite works well for local development and single-instance hosting, but the scaling path is a hosted/shared data layer:

- move persistent analysis storage to a hosted database
- support shared cache/report reuse across instances instead of host-local files only
- preserve repository freshness validation while making cached reports available across deployments
- create a cleaner path for usage analytics, audit history, and future team features

Possible future storage direction:

- hosted Postgres or similar managed relational database for persistent report state
- optional Redis-style cache layer for fast transient reuse and rate-limit protection

### 4. Containerized Deployment and More Portable Infrastructure

For a more production-style deployment model, the app should become easier to run outside the current Streamlit-hosted setup:

- add Docker support for reproducible local and cloud deployment
- make the runtime environment explicit instead of relying on host defaults
- support cleaner migration to VPS/cloud/container platforms
- make browser/PDF dependencies easier to manage consistently across environments

### 5. Repository RAG / Q&A Mode

One of the clearest future product extensions is a public-repo exploration mode:

- allow users to ask questions about a repository after analysis
- build retrieval over repository structure, README content, and selected source files
- support repository-level Q&A grounded in indexed public code and docs
- extend the app from static report generation into interactive repository understanding

This would complement the current audit flow rather than replace it.

### 6. Broader Report Intelligence

Beyond the current recruiter-facing audit, the report system could grow into a richer review layer:

- compare multiple repositories more explicitly
- cluster portfolio strengths and recurring weaknesses across projects
- support alternate report modes for recruiters, maintainers, or self-review
- add stronger export customization for portfolios, case studies, and public showcases

## Guiding Principle

The long-term goal is not just to analyze a GitHub profile once.

It is to turn this project into a more production-grade portfolio intelligence system:

- hosted
- shareable
- reproducible
- scalable
- and eventually interactive through deeper repository understanding workflows
