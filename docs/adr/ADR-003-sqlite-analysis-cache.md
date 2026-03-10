# ADR-003: Persistent Analysis Cache with SQLite and Repo Fingerprints

## Status

Accepted

## Context

The app originally relied on:

- short-lived Streamlit cache for GitHub fetches
- `st.session_state` for the generated report

That meant:

- closing or refreshing the browser lost the report
- repeated analyses for unchanged repositories reran deterministic checks and LLM calls unnecessarily
- there was no durable cache across sessions

The product needed persistent caching without introducing a separate infrastructure dependency during the current development phase.

## Decision

Use a local SQLite-backed analysis store to persist completed reports.

Cache invalidation is based on:

- analysis scope and repo selection
- repository `updated_at`
- default branch
- default-branch HEAD commit SHA
- internal analysis version

The cache is used as a server-side persistence layer, not a browser-side store.

## Alternatives Considered

### 1. Keep only Streamlit in-memory/session caching

Rejected because it does not survive browser refreshes, new sessions, or server restarts.

### 2. Add Redis immediately

Deferred because it adds operational complexity and another service dependency that is unnecessary for the current local or single-instance deployment stage.

### 3. Move directly to a hosted relational database

Deferred for the same reason. It is likely more appropriate once deployment and multi-instance hosting are in scope.

## Consequences

- repeated analysis of unchanged repositories is much faster
- saved reports persist across browser sessions on the same app instance
- cache freshness is tied to repository state rather than just repo name
- SQLite is appropriate for local development and single-instance hosting, but may need replacement for multi-instance or ephemeral-host environments
