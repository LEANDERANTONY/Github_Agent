# ADR-001: Public-Only GitHub OAuth Scope

## Status

Accepted

## Context

The app needs a sign-in flow so a user can conveniently analyze their own GitHub profile from the browser. At the same time, the product should remain acceptable for public users who may not trust a broad repository permission prompt.

GitHub OAuth Apps do not provide a true read-only private-repository source-code scope. Accessing private repositories through an OAuth App requires the broad `repo` scope, which includes write-capable repository permissions. That is too permissive for the current public-facing product direction.

## Decision

The app uses GitHub OAuth only for identity and public-profile convenience.

- default OAuth scope is `read:user user:email`
- the app analyzes public repositories only
- private-repository access is intentionally not requested in the current product flow

## Alternatives Considered

### 1. Request OAuth `repo` scope

Rejected because the consent prompt is too broad for this app's current trust model and intended audience.

### 2. Use a fine-grained personal access token flow

Not adopted as the primary product path because it is less suitable for public browser users, though it remains a viable future option for advanced/private workflows.

### 3. Build a GitHub App for repo access

Deferred. This is the better long-term path for granular private-repo permissions, but it adds setup and product complexity that was not required for the current phase.

## Consequences

- users can sign in safely without being asked for private-repo write-capable access
- the app is currently limited to public repository analysis
- future private-repo support should likely use a GitHub App rather than widening OAuth scope
