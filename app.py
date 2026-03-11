import html
import json
import textwrap
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from src.errors import AppError, ExportError, GithubRateLimitError
from src.exporters import generate_markdown, generate_pdf
from src.github_auth import (
    build_authorize_url,
    consume_oauth_state,
    exchange_code_for_token,
    generate_oauth_state,
    get_authenticated_user,
    oauth_is_configured,
    register_oauth_state,
)
from src.github_client import get_github_repos, get_portfolio_repo_facts
from src.report_builder import build_portfolio_feedback


def _inject_styles():
    st.markdown(
        textwrap.dedent(
            """
            <style>
            :root {
                --paper: #06080d;
                --page-ink: #e7eefc;
                --page-muted: #aab6cc;
                --ink: #142033;
                --muted: #5b6b83;
                --card: #ffffff;
                --line: rgba(255, 255, 255, 0.16);
                --surface-line: rgba(20, 32, 51, 0.14);
                --accent: #1d4ed8;
                --accent-strong: #2563eb;
                --success: #166534;
                --warning: #b45309;
                --danger: #b91c1c;
                --shadow: 0 24px 48px rgba(0, 0, 0, 0.34);
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(37, 99, 235, 0.22), transparent 26%),
                    radial-gradient(circle at top right, rgba(14, 165, 233, 0.14), transparent 24%),
                    linear-gradient(180deg, #070a10 0%, #0b1220 48%, #05070c 100%);
            }

            .block-container {
                max-width: 1180px;
                padding-top: 2.4rem;
                padding-bottom: 3rem;
            }

            .stApp,
            .stMarkdown,
            .stMarkdown p,
            .stMarkdown li,
            .stCaption,
            [data-testid="stMarkdownContainer"] p,
            [data-testid="stMarkdownContainer"] li,
            [data-testid="stWidgetLabel"] p,
            [data-testid="stRadio"] label,
            [data-testid="stCheckbox"] label,
            [data-testid="stFileUploaderDropzoneInstructions"] {
                color: var(--page-ink);
            }

            h1, h2, h3, h4 {
                color: var(--page-ink);
                letter-spacing: -0.02em;
            }

            .audit-hero {
                background: #ffffff !important;
                border: 1px solid var(--surface-line);
                border-radius: 24px;
                padding: 1.4rem 1.5rem;
                box-shadow: var(--shadow);
                margin-bottom: 1rem;
            }

            .audit-kicker {
                text-transform: uppercase;
                letter-spacing: 0.16em;
                font-size: 0.72rem;
                color: var(--accent-strong);
                font-weight: 700;
                margin-bottom: 0.35rem;
            }

            .audit-hero h1 {
                color: var(--ink);
            }

            .audit-copy {
                color: #2563eb !important;
                font-size: 1rem;
                line-height: 1.6;
                font-weight: 500;
                opacity: 1 !important;
                margin: 0;
            }

            .repo-shell {
                background: #ffffff !important;
                border: 1px solid var(--surface-line);
                border-radius: 18px;
                padding: 1rem;
                margin-top: -0.3rem;
                margin-bottom: 0.72rem;
                box-shadow: var(--shadow);
            }

            .auth-divider {
                display: flex;
                align-items: center;
                gap: 0.8rem;
                color: var(--muted);
                margin: 0.9rem 0 1rem;
                font-size: 0.9rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                font-weight: 700;
            }

            .auth-divider::before,
            .auth-divider::after {
                content: "";
                flex: 1;
                height: 1px;
                background: var(--line);
            }

            .repo-shell h4 {
                margin: 0 0 0.25rem;
                font-size: 1.15rem;
                color: var(--ink);
            }

            .repo-meta {
                color: var(--muted);
                font-size: 0.92rem;
            }

            .single-shell-marker {
                display: none;
            }

            div[data-testid="stMarkdownContainer"]:has(.single-shell-marker),
            div[data-testid="stMarkdownContainer"]:has(.portfolio-shell-marker),
            div[data-testid="stMarkdownContainer"]:has(.portfolio-narrative-marker) {
                display: none !important;
                margin: 0 !important;
                padding: 0 !important;
            }

            .single-shell-active {
                background: #ffffff !important;
                border: 1px solid var(--surface-line) !important;
                border-radius: 24px !important;
                box-shadow: var(--shadow) !important;
                padding: 0.12rem 0.95rem 1.02rem 0.95rem !important;
                margin: 0.35rem 0 1.2rem 0 !important;
            }

            .single-shell-active h3,
            .single-shell-active h4,
            .single-shell-active h5,
            .single-shell-active p,
            .single-shell-active li,
            .single-shell-active label,
            .single-shell-active [data-testid="stMarkdownContainer"] {
                color: var(--ink) !important;
            }

            .portfolio-shell-marker {
                display: none;
            }

            .portfolio-shell-active {
                background: #ffffff !important;
                border: 1px solid var(--surface-line) !important;
                border-radius: 24px !important;
                box-shadow: var(--shadow) !important;
                padding: 0.12rem 0.95rem 1.02rem 0.95rem !important;
                margin: 0.35rem 0 1.2rem 0 !important;
            }

            .portfolio-shell-active > div[data-testid="stVerticalBlock"] {
                gap: 0.3rem !important;
            }

            .portfolio-shell-active > div[data-testid="stVerticalBlock"] > div:first-child {
                margin-top: -0.28rem !important;
            }

            .portfolio-shell-active h3,
            .portfolio-shell-active h4,
            .portfolio-shell-active h5,
            .portfolio-shell-active p,
            .portfolio-shell-active li,
            .portfolio-shell-active label,
            .portfolio-shell-active [data-testid="stMarkdownContainer"] {
                color: var(--ink) !important;
            }

            .portfolio-narrative-marker {
                display: none;
            }

            .portfolio-narrative-active {
                background: linear-gradient(180deg, rgba(5, 12, 24, 0.98), rgba(9, 20, 38, 0.98)) !important;
                border: 1px solid rgba(96, 165, 250, 0.16) !important;
                border-radius: 22px !important;
                padding: 1.15rem 1.2rem 1.25rem !important;
                margin-top: 0.45rem !important;
                box-shadow: 0 18px 34px rgba(0, 0, 0, 0.22) !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.portfolio-narrative-marker) {
                margin-top: -0.18rem !important;
            }

            .portfolio-narrative-active,
            .portfolio-narrative-active * {
                color: #eef4ff !important;
            }

            .portfolio-narrative-active h3,
            .portfolio-narrative-active h4,
            .portfolio-narrative-active h5 {
                color: #f8fbff !important;
            }

            .portfolio-narrative-active p,
            .portfolio-narrative-active li {
                color: #eef4ff !important;
                line-height: 1.65;
            }

            .portfolio-narrative-divider {
                margin-top: 1rem;
                padding-top: 1rem;
                border-top: 1px solid rgba(96, 165, 250, 0.14);
            }

            .repo-narrative {
                background: linear-gradient(180deg, rgba(5, 12, 24, 0.98), rgba(9, 20, 38, 0.98));
                border: 1px solid rgba(96, 165, 250, 0.16);
                border-radius: 22px;
                padding: 1.15rem 1.2rem 1.25rem;
                margin-top: 0.75rem;
                box-shadow: 0 18px 34px rgba(0, 0, 0, 0.22);
            }

            .repo-narrative h4 {
                color: #f8fbff !important;
                font-size: 1.28rem;
                font-weight: 800;
                margin: 0 0 0.55rem 0;
            }

            .repo-narrative p {
                color: #f3f7ff !important;
                margin: 0 0 1rem 0;
                line-height: 1.7;
            }

            .repo-narrative,
            .repo-narrative *,
            .stExpander .repo-narrative,
            .stExpander .repo-narrative *,
            .stExpander .repo-narrative p,
            .stExpander .repo-narrative li,
            .stExpander .repo-narrative ul,
            .stExpander .repo-narrative span,
            .stExpander .repo-narrative div {
                color: #eef4ff !important;
            }

            .repo-narrative h4,
            .repo-narrative h5,
            .stExpander .repo-narrative h4,
            .stExpander .repo-narrative h5 {
                color: #f8fbff !important;
            }

            .repo-narrative-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 1.1rem 1.4rem;
                margin-top: 1rem;
                padding-top: 1rem;
            }

            .repo-narrative-grid.row-divider {
                border-top: 1px solid rgba(96, 165, 250, 0.14);
            }

            .repo-narrative-block h5 {
                color: #f8fbff !important;
                font-size: 1.12rem;
                font-weight: 800;
                margin: 0 0 0.5rem 0;
            }

            .repo-narrative-block ul {
                margin: 0;
                padding-left: 1.1rem;
            }

            .repo-narrative-block li {
                color: #eef4ff !important;
                margin: 0 0 0.45rem 0;
                line-height: 1.65;
            }

            .repo-narrative-meta {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 1rem 1.4rem;
                margin-top: 1rem;
                padding-top: 1rem;
                border-top: 1px solid rgba(96, 165, 250, 0.14);
            }

            .repo-narrative-meta h5 {
                color: #f8fbff !important;
                font-size: 1.08rem;
                font-weight: 800;
                margin: 0 0 0.45rem 0;
            }

            .repo-narrative-meta p,
            .repo-narrative-meta li {
                color: #eef4ff !important;
                margin: 0;
                line-height: 1.65;
            }

            .repo-narrative-meta ul {
                margin: 0;
                padding-left: 1.1rem;
            }

            .metric-card {
                background: #ffffff !important;
                border: 1px solid var(--surface-line);
                border-radius: 18px;
                padding: 1rem 1rem 0.9rem;
                box-shadow: var(--shadow);
                min-height: 138px;
                margin-bottom: 0.8rem;
            }

            .metric-label {
                font-size: 0.74rem;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                color: var(--muted);
                margin-bottom: 0.35rem;
                font-weight: 700;
            }

            .metric-value {
                font-size: 2rem;
                font-weight: 800;
                color: var(--ink);
                line-height: 1.08;
                margin-bottom: 0.45rem;
            }

            .metric-value-copy {
                font-size: 1.05rem;
                font-weight: 600;
                color: var(--ink);
                line-height: 1.55;
                margin-bottom: 0.6rem;
            }

            .metric-note {
                color: var(--muted);
                font-size: 0.95rem;
                line-height: 1.55;
            }

            .score-pill {
                display: inline-block;
                padding: 0.32rem 0.7rem;
                border-radius: 999px;
                font-size: 0.84rem;
                font-weight: 700;
                margin-top: 0.1rem;
                margin-bottom: 0.6rem;
            }

            .pill-excellent { background: rgba(22, 101, 52, 0.12); color: var(--success); }
            .pill-strong { background: rgba(15, 118, 110, 0.12); color: var(--accent); }
            .pill-fair { background: rgba(180, 83, 9, 0.12); color: var(--warning); }
            .pill-needs { background: rgba(185, 28, 28, 0.12); color: var(--danger); }

            .stExpander {
                border: 1px solid var(--surface-line) !important;
                border-radius: 18px !important;
                background: #ffffff !important;
                overflow: hidden;
            }

            .stExpander details summary p {
                font-weight: 700;
                color: var(--ink) !important;
            }

            .stExpander,
            .stExpander p,
            .stExpander li,
            .stExpander label,
            .stExpander h1,
            .stExpander h2,
            .stExpander h3,
            .stExpander h4,
            .stExpander h5,
            .stExpander h6,
            .stExpander [data-testid="stMarkdownContainer"] p,
            .stExpander [data-testid="stMarkdownContainer"] li,
            .stExpander [data-testid="stWidgetLabel"] p,
            .stExpander .stCaption {
                color: var(--ink) !important;
            }

            .stExpander .metric-note,
            .stExpander .repo-meta,
            .stExpander .stCaption,
            .stExpander [data-testid="stMarkdownContainer"] p:has(code) {
                color: var(--muted) !important;
            }

            .stExpander [data-testid="stMarkdownContainer"] .repo-narrative,
            .stExpander [data-testid="stMarkdownContainer"] .repo-narrative p,
            .stExpander [data-testid="stMarkdownContainer"] .repo-narrative li,
            .stExpander [data-testid="stMarkdownContainer"] .repo-narrative div,
            .stExpander [data-testid="stMarkdownContainer"] .repo-narrative span,
            .stExpander [data-testid="stMarkdownContainer"] .repo-narrative ul {
                color: #eef4ff !important;
            }

            .stExpander [data-testid="stMarkdownContainer"] .repo-narrative h4,
            .stExpander [data-testid="stMarkdownContainer"] .repo-narrative h5 {
                color: #f8fbff !important;
            }

            .single-shell-active .repo-narrative,
            .single-shell-active .repo-narrative p,
            .single-shell-active .repo-narrative li,
            .single-shell-active .repo-narrative div,
            .single-shell-active .repo-narrative span,
            .single-shell-active .repo-narrative ul {
                color: #eef4ff !important;
            }

            .single-shell-active .repo-narrative h4,
            .single-shell-active .repo-narrative h5 {
                color: #f8fbff !important;
            }

            .single-report-body [data-testid="stMarkdownContainer"] ul {
                margin-top: 0.05rem !important;
                margin-bottom: 0.3rem !important;
                padding-left: 1.08rem !important;
            }

            .single-report-body [data-testid="stMarkdownContainer"] li {
                margin-bottom: 0.34rem !important;
                line-height: 1.62 !important;
            }

            .stTextInput input,
            .stTextArea textarea,
            div[data-baseweb="input"] input,
            div[data-baseweb="base-input"] input {
                background: #ffffff !important;
                color: var(--ink) !important;
                border-color: rgba(20, 32, 51, 0.14) !important;
            }

            .stTextInput input::placeholder,
            .stTextArea textarea::placeholder,
            div[data-baseweb="input"] input::placeholder,
            div[data-baseweb="base-input"] input::placeholder {
                color: var(--muted) !important;
                opacity: 1 !important;
            }

            .stTextInput input:focus,
            .stTextArea textarea:focus,
            div[data-baseweb="input"] input:focus,
            div[data-baseweb="base-input"] input:focus {
                background: #ffffff !important;
                color: var(--ink) !important;
                border-color: rgba(20, 32, 51, 0.14) !important;
                box-shadow: none !important;
            }

            div[data-baseweb="select"] > div,
            div[data-baseweb="select"] input {
                background: #ffffff !important;
                color: var(--ink) !important;
            }

            div[data-baseweb="select"] svg,
            div[data-baseweb="input"] svg,
            div[data-baseweb="base-input"] svg {
                fill: #f8fafc !important;
            }

            div[data-baseweb="select"] svg {
                fill: var(--ink) !important;
            }

            .stRadio input[type="radio"] {
                accent-color: var(--accent-strong) !important;
            }

            .stCheckbox input[type="checkbox"] {
                accent-color: var(--accent-strong) !important;
            }

            [data-testid="stRadio"] input[type="radio"] {
                accent-color: var(--accent-strong) !important;
            }

            [data-testid="stCheckbox"] input[type="checkbox"] {
                accent-color: var(--accent-strong) !important;
            }

            input[type="radio"],
            input[type="checkbox"] {
                accent-color: var(--accent-strong) !important;
            }


            div[role="listbox"],
            div[role="option"] {
                background: rgba(255, 255, 255, 0.98) !important;
                color: var(--ink) !important;
            }

            [data-baseweb="tag"] {
                background: rgba(15, 118, 110, 0.12) !important;
                color: var(--ink) !important;
            }

            .stButton > button,
            .stDownloadButton > button,
            .stFormSubmitButton > button {
                background: var(--accent-strong) !important;
                color: #f8fafc !important;
                border: 1px solid var(--accent-strong) !important;
            }

            .oauth-link {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-height: 2.5rem;
                padding: 0.5rem 0.95rem;
                border-radius: 0.5rem;
                background: var(--accent-strong);
                color: #f8fafc !important;
                text-decoration: none !important;
                border: 1px solid var(--accent-strong);
                font-weight: 600;
            }

            .oauth-link:hover {
                background: #1d4ed8;
                border-color: #1d4ed8;
                color: #f8fafc !important;
            }

            .stButton > button *,
            .stDownloadButton > button *,
            .stFormSubmitButton > button * {
                color: #f8fafc !important;
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover,
            .stFormSubmitButton > button:hover {
                background: #1d4ed8 !important;
                color: #f8fafc !important;
                border-color: #1d4ed8 !important;
            }

            div[data-testid="stAlert"] {
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 16px 32px rgba(0, 0, 0, 0.22);
            }

            div[data-testid="stAlert"][kind="success"] {
                background: rgba(15, 43, 82, 0.95) !important;
                border-color: rgba(96, 165, 250, 0.28) !important;
            }

            div[data-testid="stAlert"][kind="success"] * {
                color: #dbeafe !important;
            }

            div[data-testid="stAlertContentSuccess"] {
                background: transparent !important;
                color: #dbeafe !important;
            }

            div[data-testid="stAlert"] div[data-testid="stAlertContainer"]:has(div[data-testid="stAlertContentSuccess"]) {
                background: rgba(15, 43, 82, 0.95) !important;
                border: 1px solid rgba(96, 165, 250, 0.28) !important;
            }

            div[data-testid="stAlert"][kind="info"] {
                background: rgba(15, 23, 42, 0.78) !important;
                border-color: rgba(96, 165, 250, 0.28) !important;
            }

            div[data-testid="stAlert"][kind="info"] * {
                color: #dbeafe !important;
            }

            div[data-testid="stAlertContentInfo"] {
                background: transparent !important;
                color: #dbeafe !important;
            }

            div[data-testid="stAlert"] div[data-testid="stAlertContainer"]:has(div[data-testid="stAlertContentInfo"]) {
                background: rgba(15, 43, 82, 0.95) !important;
                border: 1px solid rgba(96, 165, 250, 0.28) !important;
            }

            div[data-testid="stAlertContentWarning"] {
                background: transparent !important;
                color: #fff6d8 !important;
            }

            div[data-testid="stAlert"] div[data-testid="stAlertContainer"]:has(div[data-testid="stAlertContentWarning"]) {
                background: linear-gradient(135deg, rgba(104, 69, 10, 0.96), rgba(84, 58, 12, 0.94)) !important;
                border: 1px solid rgba(245, 199, 94, 0.34) !important;
                box-shadow: 0 16px 32px rgba(0, 0, 0, 0.22);
            }

            div[data-testid="stAlert"] div[data-testid="stAlertContainer"]:has(div[data-testid="stAlertContentWarning"]) * {
                color: #fff6d8 !important;
            }

            div[data-testid="stAlertContentError"] {
                background: transparent !important;
                color: #ffe4e6 !important;
            }

            div[data-testid="stAlert"] div[data-testid="stAlertContainer"]:has(div[data-testid="stAlertContentError"]) {
                background: linear-gradient(135deg, rgba(122, 24, 38, 0.96), rgba(91, 18, 33, 0.94)) !important;
                border: 1px solid rgba(251, 113, 133, 0.34) !important;
                box-shadow: 0 16px 32px rgba(0, 0, 0, 0.22);
            }

            div[data-testid="stAlert"] div[data-testid="stAlertContainer"]:has(div[data-testid="stAlertContentError"]) * {
                color: #ffe4e6 !important;
            }

            @media (max-width: 900px) {
                .block-container {
                    padding-top: 1.4rem;
                }

                .audit-hero {
                    padding: 1.05rem;
                }

                .metric-value {
                    font-size: 1.7rem;
                }

                .repo-narrative-grid,
                .repo-narrative-meta {
                    grid-template-columns: 1fr;
                }
            }
            </style>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def _score_pill_class(label):
    label = (label or "").lower()
    if label == "excellent":
        return "pill-excellent"
    if label == "strong":
        return "pill-strong"
    if label == "fair":
        return "pill-fair"
    return "pill-needs"


def _escape(value):
    return html.escape(str(value or ""))


def _render_intro():
    st.markdown(
        textwrap.dedent(
            """
            <div class="audit-hero">
                <div class="audit-kicker">Portfolio Auditor</div>
                <h1 style="margin:0 0 0.45rem 0;">GitHub Portfolio Reviewer Agent</h1>
                <p class="audit-copy">
                    Load a GitHub profile, pick the analysis scope, and generate a recruiter-facing
                    audit with deterministic checks, repository scoring, and model-written feedback.
                </p>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def _render_metric_card(label, value, note, label_badge=None, emphasize=False):
    badge_html = ""
    if label_badge:
        badge_html = '<div class="score-pill {klass}">{label}</div>'.format(
            klass=_score_pill_class(label_badge),
            label=_escape(label_badge),
        )

    value_class = "metric-value-copy" if emphasize else "metric-value"
    card_html = "".join(
        [
            '<div class="metric-card">',
            '<div class="metric-label">{label}</div>'.format(label=_escape(label)),
            '<div class="{value_class}">{value}</div>'.format(
                value_class=value_class,
                value=_escape(value),
            ),
            badge_html,
            '<div class="metric-note">{note}</div>'.format(note=_escape(note)),
            "</div>",
        ]
    )
    st.markdown(
        card_html,
        unsafe_allow_html=True,
    )


def _render_score_breakdown(score_summary, title="Score Breakdown"):
    st.markdown("#### {title}".format(title=title))
    items = list(score_summary.category_scores.items())
    if not items:
        st.caption("No score breakdown available.")
        return

    for start in range(0, len(items), 3):
        chunk = items[start : start + 3]
        cols = st.columns(len(chunk))
        for col, (category, score) in zip(cols, chunk):
            with col:
                _render_metric_card(category, "{score}/100".format(score=score), "Category score")


def _render_bullet_panel(title, items, empty_text):
    st.markdown("#### {title}".format(title=title))
    values = items or [empty_text]
    for item in values:
        st.markdown("- {item}".format(item=item))


def _render_repo_header(title, subtitle):
    st.markdown(
        textwrap.dedent(
            """
            <div class="repo-shell">
                <h4>{title}</h4>
                <div class="repo-meta">{subtitle}</div>
            </div>
            """.format(title=_escape(title), subtitle=_escape(subtitle))
        ).strip(),
        unsafe_allow_html=True,
    )


def _render_list_html(items, empty_text):
    values = items or [empty_text]
    return "".join("<li>{item}</li>".format(item=_escape(item)) for item in values)


def _render_portfolio_repo_narrative(repo_audit, repo_check):
    narrative_html = textwrap.dedent(
        """
        <div class="repo-narrative">
            <h4>Summary</h4>
            <p>{summary}</p>
            <h4>What It Does</h4>
            <p>{what_it_does}</p>
            <div class="repo-narrative-grid row-divider">
                <div class="repo-narrative-block">
                    <h5>Strengths</h5>
                    <ul>{strengths}</ul>
                </div>
                <div class="repo-narrative-block">
                    <h5>Weaknesses</h5>
                    <ul>{weaknesses}</ul>
                </div>
            </div>
            <div class="repo-narrative-grid row-divider">
                <div class="repo-narrative-block">
                    <h5>Recommendations</h5>
                    <ul>{recommendations}</ul>
                </div>
                <div class="repo-narrative-block">
                    <h5>Findings</h5>
                    <ul>{findings}</ul>
                </div>
            </div>
            <div class="repo-narrative-meta">
                <div class="repo-narrative-block">
                    <h5>Key Technologies</h5>
                    <ul>{technologies}</ul>
                </div>
                <div class="repo-narrative-block">
                    <h5>Positive Signals</h5>
                    <ul>{signals}</ul>
                </div>
            </div>
        </div>
        """
    ).format(
        summary=_escape(repo_audit.summary or "No summary generated."),
        what_it_does=_escape(repo_audit.what_it_does or "Not enough information."),
        strengths=_render_list_html(repo_audit.strengths, "No strengths generated."),
        weaknesses=_render_list_html(repo_audit.weaknesses, "No weaknesses generated."),
        recommendations=_render_list_html(repo_audit.recommendations, "No recommendations generated."),
        findings=_render_list_html(repo_check.findings, "No findings."),
        technologies=_render_list_html(repo_audit.key_technologies, "Not identified."),
        signals=_render_list_html(repo_check.strengths, "No positive signals identified."),
    )
    st.markdown(narrative_html, unsafe_allow_html=True)


def _render_single_repo_narrative(repo_audit, repo_check):
    narrative_html = textwrap.dedent(
        """
        <div class="repo-narrative">
            <h4>Repository Summary</h4>
            <p>{summary}</p>
            <h4>What It Does</h4>
            <p>{what_it_does}</p>
            <div class="repo-narrative-grid row-divider">
                <div class="repo-narrative-block">
                    <h5>Strengths</h5>
                    <ul>{strengths}</ul>
                </div>
                <div class="repo-narrative-block">
                    <h5>Weaknesses</h5>
                    <ul>{weaknesses}</ul>
                </div>
            </div>
            <div class="repo-narrative-grid row-divider">
                <div class="repo-narrative-block">
                    <h5>Recommendations</h5>
                    <ul>{recommendations}</ul>
                </div>
                <div class="repo-narrative-block">
                    <h5>Findings</h5>
                    <ul>{findings}</ul>
                </div>
            </div>
            <div class="repo-narrative-meta">
                <div class="repo-narrative-block">
                    <h5>Key Technologies</h5>
                    <ul>{technologies}</ul>
                </div>
                <div class="repo-narrative-block">
                    <h5>Positive Signals</h5>
                    <ul>{signals}</ul>
                </div>
            </div>
        </div>
        """
    ).format(
        summary=_escape(repo_audit.summary or "No summary generated."),
        what_it_does=_escape(repo_audit.what_it_does or "Not enough information."),
        strengths=_render_list_html(repo_audit.strengths, "No strengths generated."),
        weaknesses=_render_list_html(repo_audit.weaknesses, "No weaknesses generated."),
        recommendations=_render_list_html(repo_audit.recommendations, "No recommendations generated."),
        findings=_render_list_html(repo_check.findings, "No findings."),
        technologies=_render_list_html(repo_audit.key_technologies, "Not identified."),
        signals=_render_list_html(repo_check.strengths, "No positive signals identified."),
    )
    st.markdown(narrative_html, unsafe_allow_html=True)


def _render_portfolio_narrative(report):
    with st.container(border=True):
        st.markdown(
            '<div id="portfolio-narrative-marker" class="portfolio-narrative-marker"></div>',
            unsafe_allow_html=True,
        )
        _activate_portfolio_narrative()

        st.markdown("### Portfolio Summary")
        st.write(report.portfolio_summary.summary or "No portfolio summary generated.")
        st.markdown('<div class="portfolio-narrative-divider"></div>', unsafe_allow_html=True)

        panel_col1, panel_col2, panel_col3 = st.columns(3)
        with panel_col1:
            _render_bullet_panel(
                "Strongest Repositories",
                report.portfolio_summary.strongest_repos,
                "No strongest repositories identified.",
            )
        with panel_col2:
            _render_bullet_panel(
                "Improvement Areas",
                report.portfolio_summary.improvement_areas,
                "No improvement areas identified.",
            )
        with panel_col3:
            _render_bullet_panel(
                "Recommendations",
                report.portfolio_summary.top_actions,
                "No top actions identified.",
            )


def _activate_single_report_shell():
    components.html(
        """
        <script>
        const marker = window.parent.document.getElementById("single-shell-marker");
        if (marker) {
            const wrapper = marker.closest('div[data-testid="stVerticalBlockBorderWrapper"]');
            if (wrapper) {
                wrapper.classList.add("single-shell-active");
            }
        }
        </script>
        """,
        height=0,
    )


def _activate_portfolio_shell():
    components.html(
        """
        <script>
        const marker = window.parent.document.getElementById("portfolio-shell-marker");
        if (marker) {
            const wrapper = marker.closest('div[data-testid="stVerticalBlockBorderWrapper"]');
            if (wrapper) {
                wrapper.classList.add("portfolio-shell-active");
            }
        }
        </script>
        """,
        height=0,
    )


def _activate_portfolio_narrative():
    components.html(
        """
        <script>
        const marker = window.parent.document.getElementById("portfolio-narrative-marker");
        if (marker) {
            const wrapper = marker.closest('div[data-testid="stVerticalBlockBorderWrapper"]');
            if (wrapper) {
                wrapper.classList.add("portfolio-narrative-active");
            }
        }
        </script>
        """,
        height=0,
    )


def _format_cache_timestamp(timestamp):
    if not timestamp:
        return ""
    try:
        normalized = timestamp.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).strftime("%b %d, %Y %I:%M %p UTC")
    except ValueError:
        return timestamp


def _render_cache_status(report):
    saved_at = _format_cache_timestamp(report.cache_saved_at)

    if report.cache_hit:
        message = "Analysis complete. Loaded from persistent cache."
        if saved_at:
            message += " Saved {saved_at}.".format(saved_at=saved_at)
        st.info(message)
        return

    if report.cache_status == "refreshed":
        message = "Analysis complete. Fresh analysis generated after bypassing the saved cache."
    else:
        message = "Analysis complete. Fresh analysis generated and saved to persistent cache."

    if saved_at:
        message += " Cached {saved_at}.".format(saved_at=saved_at)
    st.success(message)


def _error_message(error):
    if isinstance(error, AppError):
        return error.user_message
    return str(error)


def _render_report_warnings(report):
    for warning in report.report_warnings or []:
        st.warning(warning)


def _normalize_username(username):
    return (username or "").strip()


def _init_auth_state():
    auth_defaults = {
        "github_auth_login": "",
        "github_auth_error": "",
    }
    for key, value in auth_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_loaded_data():
    st.session_state.repo_catalog = None
    st.session_state.report = None


def _clear_query_params():
    st.query_params.clear()


def _disconnect_github_auth():
    st.session_state.github_auth_login = ""
    st.session_state.github_auth_error = ""
    _reset_loaded_data()
    _clear_query_params()


def _handle_github_oauth_callback():
    if not oauth_is_configured():
        return

    query_params = st.query_params.to_dict()
    code = query_params.get("code")
    state = query_params.get("state")
    error = query_params.get("error")

    if not any([code, state, error]):
        return

    if error:
        description = query_params.get("error_description") or error
        st.session_state.github_auth_error = "GitHub sign-in failed: {error}".format(
            error=description
        )
        _clear_query_params()
        return

    if not code or not state or not consume_oauth_state(state):
        st.session_state.github_auth_error = "GitHub sign-in failed: invalid OAuth state."
        _clear_query_params()
        return

    access_token = exchange_code_for_token(code, state=state)
    user = get_authenticated_user(access_token)
    st.session_state.github_auth_login = user.get("login") or ""
    st.session_state.github_auth_error = ""
    _reset_loaded_data()
    _clear_query_params()


def _render_auth_panel():
    if st.session_state.get("github_auth_error"):
        st.error(st.session_state.github_auth_error)
        st.session_state.github_auth_error = ""

    if not oauth_is_configured():
        st.caption(
            "GitHub OAuth is not configured. Public repositories can still be analyzed by username."
        )
        return

    auth_login = st.session_state.get("github_auth_login")
    if auth_login:
        _render_repo_header(
            "GitHub Connected",
            "Signed in as {login}. Leave the username blank to analyze this account's public repositories.".format(
                login=auth_login
            ),
        )
        st.caption(
            "OAuth sign-in is used for identity here. Only publicly visible repositories are analyzed."
        )
        if st.button("Disconnect GitHub"):
            _disconnect_github_auth()
            st.rerun()
        return

    oauth_state = generate_oauth_state()
    register_oauth_state(oauth_state)
    authorize_url = build_authorize_url(oauth_state)
    _render_repo_header(
        "Connect GitHub",
        "Authorize the app to identify your GitHub account and analyze its public repositories.",
    )
    st.markdown(
        '<a class="oauth-link" href="{url}" target="_top" rel="noopener noreferrer" onclick=\'window.top.location.href={js_url}; return false;\'>Sign in with GitHub</a>'.format(
            url=_escape(authorize_url),
            js_url=json.dumps(authorize_url),
        ),
        unsafe_allow_html=True,
    )
    st.markdown('<div class="auth-divider">or</div>', unsafe_allow_html=True)


def _catalog_target(username):
    normalized_username = _normalize_username(username)
    if normalized_username:
        return normalized_username.lower()
    return "__my_profile__"

@st.cache_data(show_spinner=False, ttl=900)
def _load_public_repo_catalog(username):
    return get_github_repos(username=username)


def load_repo_catalog(username):
    normalized_username = _normalize_username(username)
    if normalized_username:
        return _load_public_repo_catalog(normalized_username)
    raise Exception("Enter a public GitHub username or sign in with GitHub to analyze public repositories.")


@st.cache_data(show_spinner=False, ttl=900)
def _load_public_repo_facts(username, selected_repo_names, max_repos, skip_forks):
    repo_names = list(selected_repo_names) if selected_repo_names else None
    return get_portfolio_repo_facts(
        username=username,
        selected_repo_names=repo_names,
        max_repos=max_repos,
        skip_forks=skip_forks,
    )


def load_repo_facts(username, selected_repo_names, max_repos, skip_forks):
    normalized_username = _normalize_username(username)
    repo_names = list(selected_repo_names) if selected_repo_names else None
    if normalized_username:
        return _load_public_repo_facts(
            normalized_username,
            repo_names,
            max_repos,
            skip_forks,
        )
    raise Exception("Enter a public GitHub username or sign in with GitHub to analyze public repositories.")


def _reset_catalog_if_target_changed(target):
    if st.session_state.get("repo_catalog_target") != target:
        st.session_state.repo_catalog_target = target
        st.session_state.repo_catalog = None
        st.session_state.report = None


def _get_repo_labels(repo_catalog):
    labels = []
    for repo in repo_catalog:
        name = repo["name"]
        if repo.get("fork"):
            name = "{name} (fork)".format(name=name)
        description = repo.get("description") or "No description"
        labels.append("{name} - {description}".format(name=name, description=description))
    return labels


def _render_single_repo_report(report):
    repo_audit = report.repo_audits[0]
    repo_check = report.repo_checks[0]

    with st.container(border=True):
        st.markdown('<div id="single-shell-marker" class="single-shell-marker"></div>', unsafe_allow_html=True)
        _activate_single_report_shell()

        _render_repo_header(
            repo_audit.repo_name,
            "Single repository audit with recruiter-oriented feedback and deterministic checks.",
        )

        hero_col1, hero_col2, hero_col3 = st.columns([1.05, 1.5, 1.5])
        with hero_col1:
            _render_metric_card(
                "Repository Score",
                "{score}/100".format(score=repo_check.score.overall),
                "Weighted from documentation, discoverability, engineering, maintenance, and originality.",
                repo_check.score.label or "Not rated.",
            )
        with hero_col2:
            _render_metric_card(
                "Showcase Value",
                repo_audit.showcase_value or "Not rated",
                "How compelling this repo is as a portfolio artifact.",
                emphasize=True,
            )
        with hero_col3:
            _render_metric_card(
                "Recruiter Signal",
                repo_audit.recruiter_signal or "Not rated",
                "What this repository likely communicates during a quick profile review.",
                emphasize=True,
            )

        _render_score_breakdown(repo_check.score)
        _render_single_repo_narrative(repo_audit, repo_check)


def _render_portfolio_report(report):
    with st.container(border=True):
        st.markdown('<div id="portfolio-shell-marker" class="portfolio-shell-marker"></div>', unsafe_allow_html=True)
        _activate_portfolio_shell()

        hero_col1, hero_col2, hero_col3 = st.columns([1.05, 1.15, 1.15])
        with hero_col1:
            _render_metric_card(
                "Portfolio Score",
                "{score}/100".format(score=report.portfolio_score.overall),
                "Averages deterministic repo scores across the selected analysis scope.",
                report.portfolio_score.label or "Not rated.",
            )
        with hero_col2:
            _render_metric_card(
                "Repositories Reviewed",
                str(report.repo_count),
                "Scope-aware count after filters, selection rules, and fork exclusions.",
            )
        with hero_col3:
            strongest_count = len(report.portfolio_summary.strongest_repos or [])
            _render_metric_card(
                "Standout Repos",
                str(strongest_count),
                "Repositories the model highlighted as the strongest signals in the portfolio.",
            )

        _render_score_breakdown(report.portfolio_score)
        _render_portfolio_narrative(report)

    st.markdown("### Repository Audits")
    for repo_audit, repo_check in zip(report.repo_audits, report.repo_checks):
        with st.expander(repo_audit.repo_name, expanded=False):
            repo_col1, repo_col2, repo_col3 = st.columns([1.0, 1.2, 1.2])
            with repo_col1:
                _render_metric_card(
                    "Repository Score",
                    "{score}/100".format(score=repo_check.score.overall),
                    "Deterministic score from repo quality signals.",
                    repo_check.score.label or "Not rated.",
                )
            with repo_col2:
                _render_metric_card(
                    "Showcase Value",
                    repo_audit.showcase_value or "Not rated",
                    "Portfolio usefulness of this repository.",
                    emphasize=True,
                )
            with repo_col3:
                _render_metric_card(
                    "Recruiter Signal",
                    repo_audit.recruiter_signal or "Not rated",
                    "What this project likely communicates at first glance.",
                    emphasize=True,
                )

            _render_score_breakdown(repo_check.score, title="Repository Score Breakdown")
            _render_portfolio_repo_narrative(repo_audit, repo_check)


def _render_downloads(report, github_username):
    file_format = st.selectbox(
        "Choose download format",
        [
            "Markdown (.md)",
            "PDF (.pdf)",
        ],
    )

    try:
        if file_format == "Markdown (.md)":
            file_data = generate_markdown(report.feedback_markdown)
            mime_type = "text/markdown"
            file_ext = "md"
        else:
            file_data = generate_pdf(report.feedback_markdown)
            mime_type = "application/pdf"
            file_ext = "pdf"
    except ExportError as error:
        st.error(_error_message(error))
        return

    st.download_button(
        label="Download Report as {label}".format(label=file_format.split()[0]),
        data=file_data.getvalue(),
        file_name="{name}_portfolio_suggestions.{ext}".format(
            name=github_username or "my",
            ext=file_ext,
        ),
        mime=mime_type,
    )


def main():
    st.set_page_config(page_title="GitHub Portfolio Reviewer", page_icon="GitHub")
    _inject_styles()
    _init_auth_state()
    try:
        _handle_github_oauth_callback()
    except Exception as error:
        st.session_state.github_auth_error = _error_message(error)
    _render_intro()
    _render_auth_panel()

    with st.form("repo_catalog_form", clear_on_submit=False):
        github_username = st.text_input(
            "Enter your GitHub username to analyze profile",
            placeholder="e.g. torvalds",
        )
        load_repositories = st.form_submit_button("Load Repositories")
    auth_login = st.session_state.get("github_auth_login") or ""
    effective_username = _normalize_username(github_username) or auth_login
    target = _catalog_target(effective_username)

    if auth_login and not _normalize_username(github_username):
        st.caption(
            "Using your signed-in GitHub username `{login}`. Only public repositories will be analyzed.".format(
                login=auth_login
            )
        )
    elif not _normalize_username(github_username):
        st.caption("Enter a public GitHub username, or sign in to analyze your own public repositories.")

    if "repo_catalog_target" not in st.session_state:
        st.session_state.repo_catalog_target = target
    if "repo_catalog" not in st.session_state:
        st.session_state.repo_catalog = None
    if "report" not in st.session_state:
        st.session_state.report = None
    if "analysis_status_message" not in st.session_state:
        st.session_state.analysis_status_message = ""
    if "analysis_status_kind" not in st.session_state:
        st.session_state.analysis_status_kind = "success"

    _reset_catalog_if_target_changed(target)

    if load_repositories:
        try:
            with st.spinner("Loading repositories..."):
                st.session_state.repo_catalog = load_repo_catalog(
                    effective_username,
                )
                st.session_state.report = None
                st.session_state.analysis_status_message = ""
        except Exception as error:
            message = _error_message(error)
            if isinstance(error, GithubRateLimitError):
                st.warning(message)
            else:
                st.error(message)

    repo_catalog = st.session_state.repo_catalog

    if repo_catalog:
        repo_count = len(repo_catalog)
        _render_repo_header(
            "Repository Catalog Ready",
            "{count} repositories loaded. Choose a scope and run the audit.".format(count=repo_count),
        )

        scope = st.radio(
            "Analysis scope",
            ["Single repository", "Selected repositories", "Portfolio slice"],
            horizontal=True,
        )

        repo_options = [repo["name"] for repo in repo_catalog]
        repo_labels = dict(zip(repo_options, _get_repo_labels(repo_catalog)))
        selected_repo_names = None
        max_repos = None
        skip_forks = False

        if scope == "Single repository":
            selected_repo = st.selectbox(
                "Choose one repository",
                repo_options,
                format_func=lambda repo_name: repo_labels[repo_name],
            )
            selected_repo_names = [selected_repo]
        elif scope == "Selected repositories":
            selected_repo_names = st.multiselect(
                "Choose repositories to analyze",
                repo_options,
                format_func=lambda repo_name: repo_labels[repo_name],
            )
            st.caption("Select multiple repositories for a smaller custom portfolio audit.")
        else:
            skip_forks = st.checkbox("Skip forked repositories", value=True)
            eligible_repos = [repo for repo in repo_catalog if not skip_forks or not repo.get("fork")]
            if not eligible_repos:
                st.warning("No repositories match the current portfolio-slice filters.")
            max_default = min(5, len(eligible_repos)) if eligible_repos else 1
            max_repos = st.slider(
                "How many repositories to analyze",
                min_value=1,
                max_value=max(1, len(eligible_repos)),
                value=max_default,
            )
            st.caption("Repositories are taken from the most recently updated list.")

        force_refresh = st.checkbox(
            "Force refresh analysis (tick to generate a fresh repo analysis and skip any cached saves)",
            value=False,
            help="Ignore any saved report for this exact repo selection and regenerate a new one from GitHub + OpenAI.",
        )

        if st.button("Run Analysis"):
            if scope == "Selected repositories" and not selected_repo_names:
                st.error("Choose at least one repository to analyze.")
            else:
                try:
                    status_placeholder = st.empty()
                    progress_bar = st.progress(0)

                    def update_progress(message, value):
                        status_placeholder.info(message)
                        progress_bar.progress(int(value))

                    update_progress("Loading cached GitHub data...", 5)
                    selected_repo_tuple = tuple(selected_repo_names or [])
                    repo_facts = load_repo_facts(
                        effective_username,
                        selected_repo_tuple,
                        max_repos if scope == "Portfolio slice" else None,
                        skip_forks if scope == "Portfolio slice" else False,
                    )

                    st.session_state.report = build_portfolio_feedback(
                        github_username=effective_username,
                        selected_repo_names=selected_repo_names,
                        max_repos=max_repos if scope == "Portfolio slice" else None,
                        skip_forks=skip_forks if scope == "Portfolio slice" else False,
                        repo_facts=repo_facts,
                        force_refresh=force_refresh,
                        progress_callback=update_progress,
                    )
                    report = st.session_state.report
                    saved_at = _format_cache_timestamp(report.cache_saved_at)
                    if report.cache_hit:
                        message = "Analysis complete. Loaded from persistent cache."
                        if saved_at:
                            message += " Saved {saved_at}.".format(saved_at=saved_at)
                        st.session_state.analysis_status_kind = "info"
                    elif report.cache_status == "refreshed":
                        message = "Analysis complete. Fresh analysis generated after bypassing the saved cache."
                        if saved_at:
                            message += " Cached {saved_at}.".format(saved_at=saved_at)
                        st.session_state.analysis_status_kind = "success"
                    else:
                        message = "Analysis complete. Fresh analysis generated and saved to persistent cache."
                        if saved_at:
                            message += " Cached {saved_at}.".format(saved_at=saved_at)
                        st.session_state.analysis_status_kind = "success"

                    st.session_state.analysis_status_message = message
                    status_placeholder.empty()
                    progress_bar.empty()
                except Exception as error:
                    message = _error_message(error)
                    st.session_state.analysis_status_message = ""
                    if isinstance(error, GithubRateLimitError):
                        st.warning(message)
                    else:
                        st.error(message)

    if st.session_state.get("analysis_status_message"):
        if st.session_state.get("analysis_status_kind") == "info":
            st.info(st.session_state.analysis_status_message)
        else:
            st.success(st.session_state.analysis_status_message)

    report = st.session_state.report
    if report:
        st.markdown(
            '<div style="height:6px; border-radius:999px; background:#2563eb; margin:1rem 0 1.5rem 0;"></div>',
            unsafe_allow_html=True,
        )
        st.subheader(report.analysis_label or "Portfolio Analysis")
        st.caption("Analyzed repositories: {count}".format(count=report.repo_count))
        _render_report_warnings(report)

        if report.repo_count == 1:
            _render_single_repo_report(report)
        else:
            _render_portfolio_report(report)

        _render_downloads(report, effective_username)

    st.markdown("---")
    st.caption("Built by Leander Antony | Powered by OpenAI and the GitHub API")


if __name__ == "__main__":
    main()
