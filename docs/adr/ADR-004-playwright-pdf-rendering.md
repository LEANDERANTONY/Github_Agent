# ADR-004: HTML/CSS PDF Rendering via Playwright

## Status

Accepted

## Context

The initial PDF export path relied on a custom Markdown parser plus ReportLab layout. That approach was fast, but it produced recurring formatting issues:

- ordered lists and nested lists were brittle
- spacing and pagination were difficult to stabilize
- exported reports felt more like raw text conversion than polished documents

The app needed higher-quality, presentation-ready PDF output while still keeping a fallback path available.

## Decision

Use HTML/CSS rendering with Playwright/Chromium as the primary PDF generation path, with ReportLab retained as a fallback.

The report is first transformed into structured HTML, then rendered to PDF by a browser engine that handles layout more naturally than the earlier custom parser path.

## Alternatives Considered

### 1. Keep only ReportLab with a custom parser

Rejected because the maintenance burden kept rising while output quality remained limited.

### 2. Use Pandoc-based document conversion

Deferred because it adds external binary/toolchain complexity, especially on Windows and in app deployment environments.

### 3. Use another Markdown parser but keep the same ReportLab-centric layout model

Partially helpful for parsing correctness, but it would not fully address the presentation-quality and layout issues that motivated the change.

## Consequences

- PDF output is more faithful to the intended structure and visual hierarchy
- styling is easier to evolve through HTML/CSS than low-level PDF drawing code
- the export path now depends on Playwright/Chromium being available in the environment
- a fallback path still exists if the browser-based export backend fails
