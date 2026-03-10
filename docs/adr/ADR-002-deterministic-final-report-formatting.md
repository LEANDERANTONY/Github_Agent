# ADR-002: Deterministic Final Report Formatting

## Status

Accepted

## Context

Early versions of the app used an LLM to produce a final freeform Markdown rewrite of the completed analysis. While this created fluent reports, it also caused section drift across repositories and portfolios:

- headings stayed mostly consistent, but internal section shape varied
- `Findings`, `Strengths`, `Weaknesses`, and action lists changed format from run to run
- PDF export quality became harder to control because content structure was unstable

The app already had structured analysis data available through deterministic checks, `RepoAudit`, and `PortfolioSummary`.

## Decision

The app keeps LLM assistance for repo-level analysis and portfolio synthesis, but renders the final Markdown report through deterministic templates.

Key rules:

- `Strengths` and `Weaknesses` use bullet items with bold lead phrases plus explanation
- `Top Priority Actions` and recommendations use stable numbered formatting
- `Findings` are rendered as short deterministic bullets
- single-repo and multi-repo reports follow fixed section order

## Alternatives Considered

### 1. Keep the final report fully freeform

Rejected because formatting drift made exported reports inconsistent and harder to style reliably.

### 2. Remove LLM-generated content entirely

Rejected because that would reduce the quality of repo summaries, strengths, weaknesses, and portfolio synthesis.

### 3. Post-process freeform LLM output aggressively

Partially useful, but still weaker than generating the final report from structured inputs with a fixed template.

## Consequences

- report structure is much more consistent across repositories and portfolios
- export formatting is easier to control and test
- content quality is preserved because the LLM still contributes analysis inside fixed report slots
- the final report has less stylistic variation, which is acceptable for a recruiter-facing audit product
