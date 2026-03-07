import html

import streamlit as st

from src.exporters import generate_docx, generate_markdown, generate_pdf, generate_txt
from src.github_client import get_github_repos, get_portfolio_repo_facts
from src.report_builder import build_portfolio_feedback


def _inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --paper: #f5efe1;
            --ink: #1f2933;
            --muted: #52606d;
            --card: rgba(255, 252, 247, 0.88);
            --line: rgba(31, 41, 51, 0.12);
            --accent: #0f766e;
            --accent-2: #c2410c;
            --success: #166534;
            --warning: #b45309;
            --danger: #b91c1c;
            --shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(15, 118, 110, 0.18), transparent 28%),
                radial-gradient(circle at top right, rgba(194, 65, 12, 0.12), transparent 25%),
                linear-gradient(180deg, #f7f1e4 0%, #f2ebdc 100%);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2.4rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: -0.02em;
        }

        .audit-hero {
            background: linear-gradient(135deg, rgba(255,255,255,0.82), rgba(245,239,225,0.92));
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1.4rem 1.5rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .audit-kicker {
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-size: 0.72rem;
            color: var(--accent);
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        .audit-copy {
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.6;
            margin: 0;
        }

        .stat-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 1rem 1rem 0.9rem;
            box-shadow: var(--shadow);
            min-height: 130px;
        }

        .stat-label {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--muted);
            margin-bottom: 0.35rem;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 800;
            color: var(--ink);
            line-height: 1;
            margin-bottom: 0.45rem;
        }

        .stat-note {
            color: var(--muted);
            font-size: 0.96rem;
            line-height: 1.5;
        }

        .score-pill {
            display: inline-block;
            padding: 0.32rem 0.7rem;
            border-radius: 999px;
            font-size: 0.84rem;
            font-weight: 700;
            margin-top: 0.18rem;
        }

        .pill-excellent { background: rgba(22, 101, 52, 0.12); color: var(--success); }
        .pill-strong { background: rgba(15, 118, 110, 0.12); color: var(--accent); }
        .pill-fair { background: rgba(180, 83, 9, 0.12); color: var(--warning); }
        .pill-needs { background: rgba(185, 28, 28, 0.12); color: var(--danger); }

        .section-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            box-shadow: var(--shadow);
            height: 100%;
        }

        .section-title {
            font-size: 0.86rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--muted);
            margin-bottom: 0.65rem;
            font-weight: 700;
        }

        .score-chip-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
            gap: 0.7rem;
            margin: 0.45rem 0 1rem;
        }

        .score-chip {
            background: rgba(255,255,255,0.62);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 0.8rem 0.85rem;
        }

        .score-chip-label {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--muted);
            margin-bottom: 0.25rem;
        }

        .score-chip-value {
            font-size: 1.2rem;
            font-weight: 800;
            color: var(--ink);
        }

        .repo-shell {
            background: rgba(255,255,255,0.52);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 1rem;
            margin-bottom: 0.9rem;
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

        .stExpander {
            border: 1px solid var(--line) !important;
            border-radius: 18px !important;
            background: rgba(255,255,255,0.55) !important;
            overflow: hidden;
        }

        .stExpander details summary p {
            font-weight: 700;
            color: var(--ink);
        }

        @media (max-width: 900px) {
            .block-container {
                padding-top: 1.4rem;
            }

            .audit-hero {
                padding: 1.05rem;
            }

            .stat-value {
                font-size: 1.7rem;
            }
        }
        </style>
        """,
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


def _render_intro():
    st.markdown(
        """
        <div class="audit-hero">
            <div class="audit-kicker">Portfolio Auditor</div>
            <h1 style="margin:0 0 0.45rem 0;">GitHub Portfolio Reviewer Agent</h1>
            <p class="audit-copy">
                Load a GitHub profile, pick the analysis scope, and generate a recruiter-facing
                audit with deterministic checks, repository scoring, and model-written feedback.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_stat_card(label, value, note, label_badge=None):
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))
    safe_note = html.escape(str(note))
    badge_html = ""
    if label_badge:
        badge_html = '<div class="score-pill {klass}">{label}</div>'.format(
            klass=_score_pill_class(label_badge),
            label=html.escape(str(label_badge)),
        )
    st.markdown(
        """
        <div class="stat-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            {badge}
            <div class="stat-note">{note}</div>
        </div>
        """.format(label=safe_label, value=safe_value, note=safe_note, badge=badge_html),
        unsafe_allow_html=True,
    )


def _render_score_breakdown(score_summary, title="Score Breakdown"):
    st.markdown(
        '<div class="section-title">{title}</div>'.format(title=title),
        unsafe_allow_html=True,
    )
    chips = []
    for category, score in score_summary.category_scores.items():
        chips.append(
            """
            <div class="score-chip">
                <div class="score-chip-label">{category}</div>
                <div class="score-chip-value">{score}/100</div>
            </div>
            """.format(category=category, score=score)
        )
    st.markdown(
        '<div class="score-chip-grid">{chips}</div>'.format(chips="".join(chips)),
        unsafe_allow_html=True,
    )


def _render_bullet_panel(title, items, empty_text):
    st.markdown('<div class="section-title">{title}</div>'.format(title=title), unsafe_allow_html=True)
    values = items or [empty_text]
    for item in values:
        st.markdown(f"- {item}")


def _render_repo_header(title, subtitle):
    safe_title = html.escape(str(title))
    safe_subtitle = html.escape(str(subtitle))
    st.markdown(
        """
        <div class="repo-shell">
            <h4>{title}</h4>
            <div class="repo-meta">{subtitle}</div>
        </div>
        """.format(title=safe_title, subtitle=safe_subtitle),
        unsafe_allow_html=True,
    )


def _normalize_username(username):
    return (username or "").strip()


def _catalog_target(username):
    return _normalize_username(username) or "__my_profile__"


@st.cache_data(show_spinner=False, ttl=900)
def load_repo_catalog(username):
    normalized_username = _normalize_username(username)
    return get_github_repos(username=normalized_username or None)


@st.cache_data(show_spinner=False, ttl=900)
def load_repo_facts(username, selected_repo_names, max_repos, skip_forks):
    normalized_username = _normalize_username(username)
    repo_names = list(selected_repo_names) if selected_repo_names else None
    return get_portfolio_repo_facts(
        username=normalized_username or None,
        selected_repo_names=repo_names,
        max_repos=max_repos,
        skip_forks=skip_forks,
    )


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

    _render_repo_header(
        repo_audit.repo_name,
        "Single repository audit with recruiter-oriented feedback and deterministic checks.",
    )

    hero_col1, hero_col2, hero_col3 = st.columns([1.1, 1.6, 1.6])
    with hero_col1:
        _render_stat_card(
            "Repository Score",
            "{score}/100".format(score=repo_check.score.overall),
            "Weighted from documentation, discoverability, engineering, maintenance, and originality.",
            repo_check.score.label or "Not rated.",
        )
    with hero_col2:
        _render_stat_card(
            "Showcase Value",
            repo_audit.showcase_value or "Not rated",
            "How compelling this repo is as a portfolio artifact.",
        )
    with hero_col3:
        _render_stat_card(
            "Recruiter Signal",
            repo_audit.recruiter_signal or "Not rated",
            "What this repository likely communicates during a quick profile review.",
        )

    _render_score_breakdown(repo_check.score)

    summary_col1, summary_col2 = st.columns([1.35, 1])
    with summary_col1:
        st.markdown("### Repository Summary")
        st.write(repo_audit.summary or "No summary generated.")
        st.markdown("#### What It Does")
        st.write(repo_audit.what_it_does or "Not enough information.")
    with summary_col2:
        st.markdown("### Technologies")
        technologies = repo_audit.key_technologies or ["Not identified."]
        for item in technologies:
            st.markdown(f"- {item}")

    panel_col1, panel_col2 = st.columns(2)
    with panel_col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _render_bullet_panel("Strengths", repo_audit.strengths, "No strengths generated.")
        st.markdown("</div>", unsafe_allow_html=True)
    with panel_col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _render_bullet_panel("Weaknesses", repo_audit.weaknesses, "No weaknesses generated.")
        st.markdown("</div>", unsafe_allow_html=True)

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _render_bullet_panel(
            "Top Priority Actions",
            repo_audit.recommendations,
            "No recommendations generated.",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with action_col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _render_bullet_panel(
            "Deterministic Findings",
            repo_check.findings,
            "No deterministic findings.",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    _render_bullet_panel(
        "Deterministic Good Signals",
        repo_check.strengths,
        "No deterministic strengths identified.",
    )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_portfolio_report(report):
    hero_col1, hero_col2, hero_col3 = st.columns([1.1, 1.2, 1.2])
    with hero_col1:
        _render_stat_card(
            "Portfolio Score",
            "{score}/100".format(score=report.portfolio_score.overall),
            "Averages deterministic repo scores across the selected analysis scope.",
            report.portfolio_score.label or "Not rated.",
        )
    with hero_col2:
        _render_stat_card(
            "Repositories Reviewed",
            str(report.repo_count),
            "Scope-aware count after filters, selection rules, and fork exclusions.",
        )
    with hero_col3:
        strongest_count = len(report.portfolio_summary.strongest_repos or [])
        _render_stat_card(
            "Standout Repos",
            str(strongest_count),
            "Repositories the model highlighted as the strongest signals in the portfolio.",
        )

    _render_score_breakdown(report.portfolio_score)

    st.markdown("### Portfolio Summary")
    st.markdown(report.portfolio_summary.summary or "No portfolio summary generated.")

    panel_col1, panel_col2, panel_col3 = st.columns(3)
    with panel_col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _render_bullet_panel(
            "Strongest Repositories",
            report.portfolio_summary.strongest_repos,
            "No strongest repositories identified.",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with panel_col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _render_bullet_panel(
            "Improvement Areas",
            report.portfolio_summary.improvement_areas,
            "No improvement areas identified.",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with panel_col3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _render_bullet_panel(
            "Top Actions",
            report.portfolio_summary.top_actions,
            "No top actions identified.",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Repository Audits")
    for repo_audit, repo_check in zip(report.repo_audits, report.repo_checks):
        with st.expander(repo_audit.repo_name, expanded=False):
            repo_col1, repo_col2, repo_col3 = st.columns([1, 1.2, 1.2])
            with repo_col1:
                _render_stat_card(
                    "Repository Score",
                    "{score}/100".format(score=repo_check.score.overall),
                    "Deterministic score from repo quality signals.",
                    repo_check.score.label or "Not rated.",
                )
            with repo_col2:
                _render_stat_card(
                    "Showcase Value",
                    repo_audit.showcase_value or "Not rated",
                    "Portfolio usefulness of this repository.",
                )
            with repo_col3:
                _render_stat_card(
                    "Recruiter Signal",
                    repo_audit.recruiter_signal or "Not rated",
                    "What this project likely communicates at first glance.",
                )

            _render_score_breakdown(repo_check.score, title="Repository Score Breakdown")

            summary_col1, summary_col2 = st.columns([1.35, 1])
            with summary_col1:
                st.markdown("**Summary**")
                st.write(repo_audit.summary or "No summary generated.")
                st.markdown("**What It Does**")
                st.write(repo_audit.what_it_does or "Not enough information.")
            with summary_col2:
                _render_bullet_panel(
                    "Key Technologies",
                    repo_audit.key_technologies,
                    "Not identified.",
                )

            panel_col1, panel_col2 = st.columns(2)
            with panel_col1:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                _render_bullet_panel(
                    "Strengths",
                    repo_audit.strengths,
                    "No strengths generated.",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            with panel_col2:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                _render_bullet_panel(
                    "Weaknesses",
                    repo_audit.weaknesses,
                    "No weaknesses generated.",
                )
                st.markdown("</div>", unsafe_allow_html=True)

            panel_col3, panel_col4 = st.columns(2)
            with panel_col3:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                _render_bullet_panel(
                    "Recommendations",
                    repo_audit.recommendations,
                    "No recommendations generated.",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            with panel_col4:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                _render_bullet_panel(
                    "Deterministic Findings",
                    repo_check.findings,
                    "No deterministic findings.",
                )
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            _render_bullet_panel(
                "Deterministic Good Signals",
                repo_check.strengths,
                "No deterministic strengths identified.",
            )
            st.markdown("</div>", unsafe_allow_html=True)


def _render_downloads(report, github_username):
    st.markdown("#### Download Report")
    file_format = st.selectbox(
        "Choose download format",
        [
            "Markdown (.md)",
            "Text (.txt)",
            "Word (.docx)",
            "PDF (.pdf)",
        ],
    )

    if file_format == "Markdown (.md)":
        file_data = generate_markdown(report.feedback_markdown)
        mime_type = "text/markdown"
        file_ext = "md"
    elif file_format == "Text (.txt)":
        file_data = generate_txt(report.feedback_markdown)
        mime_type = "text/plain"
        file_ext = "txt"
    elif file_format == "Word (.docx)":
        file_data = generate_docx(report.feedback_markdown)
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        file_ext = "docx"
    else:
        file_data = generate_pdf(report.feedback_markdown)
        mime_type = "application/pdf"
        file_ext = "pdf"

    st.download_button(
        label=f"Download Report as {file_format.split()[0]}",
        data=file_data.getvalue(),
        file_name=f"{github_username or 'my'}_portfolio_suggestions.{file_ext}",
        mime=mime_type,
    )


def main():
    st.set_page_config(page_title="GitHub Portfolio Reviewer", page_icon="GitHub")
    _inject_styles()
    _render_intro()

    github_username = st.text_input("GitHub Username (optional)", placeholder="e.g. torvalds")
    target = _catalog_target(github_username)

    if "repo_catalog_target" not in st.session_state:
        st.session_state.repo_catalog_target = target
    if "repo_catalog" not in st.session_state:
        st.session_state.repo_catalog = None
    if "report" not in st.session_state:
        st.session_state.report = None

    _reset_catalog_if_target_changed(target)

    if st.button("Load Repositories"):
        try:
            with st.spinner("Loading repositories..."):
                st.session_state.repo_catalog = load_repo_catalog(github_username)
                st.session_state.report = None
        except Exception as error:
            st.error(f"Error: {error}")

    repo_catalog = st.session_state.repo_catalog

    if repo_catalog:
        repo_count = len(repo_catalog)
        st.markdown(
            """
            <div class="repo-shell">
                <h4>Repository Catalog Ready</h4>
                <div class="repo-meta">{count} repositories loaded. Choose a scope and run the audit.</div>
            </div>
            """.format(count=repo_count),
            unsafe_allow_html=True,
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
                        github_username,
                        selected_repo_tuple,
                        max_repos if scope == "Portfolio slice" else None,
                        skip_forks if scope == "Portfolio slice" else False,
                    )

                    st.session_state.report = build_portfolio_feedback(
                        github_username=github_username,
                        selected_repo_names=selected_repo_names,
                        max_repos=max_repos if scope == "Portfolio slice" else None,
                        skip_forks=skip_forks if scope == "Portfolio slice" else False,
                        repo_facts=repo_facts,
                        progress_callback=update_progress,
                    )
                    status_placeholder.success("Analysis complete.")
                except Exception as error:
                    st.error(f"Error: {error}")

    report = st.session_state.report
    if report:
        st.markdown("---")
        st.subheader(report.analysis_label or "Portfolio Analysis")
        st.caption("Analyzed repositories: {count}".format(count=report.repo_count))

        if report.repo_count == 1:
            _render_single_repo_report(report)
        else:
            _render_portfolio_report(report)

        _render_downloads(report, github_username)

    st.markdown("---")
    st.caption("Built by Leander Antony | Powered by OpenAI and the GitHub API")


if __name__ == "__main__":
    main()
