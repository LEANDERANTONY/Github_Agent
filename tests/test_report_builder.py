import unittest
from unittest.mock import patch

from src.report_builder import _fallback_repo_audit, _format_markdown_report, build_portfolio_feedback
from src.schemas import PortfolioReport, PortfolioSummary, RepoAudit, RepoCheckResult, RepoFacts, ScoreSummary


class ReportBuilderTestCase(unittest.TestCase):
    def test_format_markdown_report_uses_single_repo_layout(self):
        report = PortfolioReport(
            github_username="demo",
            repo_count=1,
            feedback_markdown="",
            repo_audits=[
                RepoAudit(
                    repo_name="demo",
                    summary="A demo repository.",
                    what_it_does="Shows the full report format.",
                    key_technologies=["Python"],
                    strengths=["Readable README: Setup and usage are easy to follow."],
                    weaknesses=["No tests: There is no automated validation yet."],
                    recommendations=["Add tests: Introduce smoke tests for the core workflow."],
                    showcase_value="Medium",
                    recruiter_signal="Needs polish",
                )
            ],
            repo_checks=[RepoCheckResult(repo_name="demo", findings=["No tests found."])],
            portfolio_summary=PortfolioSummary(
                summary="Useful portfolio start.",
                strongest_repos=["demo"],
                improvement_areas=["Testing"],
                top_actions=["Add tests"],
            ),
        )

        markdown = _format_markdown_report(report)

        self.assertIn("# GitHub Repository Audit", markdown)
        self.assertIn("**Repository**\ndemo", markdown)
        self.assertIn("## Repository Score", markdown)
        self.assertIn("## Repository Summary", markdown)
        self.assertIn("## Top Priority Actions", markdown)
        self.assertIn("## Findings", markdown)
        self.assertIn("- **Readable README**: Setup and usage are easy to follow.", markdown)
        self.assertIn("- **No tests**: There is no automated validation yet.", markdown)
        self.assertIn("1. **Add tests**: Introduce smoke tests for the core workflow.", markdown)

    def test_format_markdown_report_includes_portfolio_sections(self):
        report = PortfolioReport(
            github_username="demo",
            repo_count=2,
            feedback_markdown="",
            repo_audits=[
                RepoAudit(
                    repo_name="demo-a",
                    summary="A demo repository.",
                    what_it_does="Shows the full report format.",
                    key_technologies=["Python"],
                    strengths=["Readable README: Setup and usage are easy to follow."],
                    weaknesses=["No tests: There is no automated validation yet."],
                    recommendations=["Add tests: Introduce smoke tests for the core workflow."],
                    showcase_value="Medium",
                    recruiter_signal="Needs polish",
                ),
                RepoAudit(
                    repo_name="demo-b",
                    summary="Another demo repository.",
                    what_it_does="Shows multi-repo output.",
                    key_technologies=["SQL"],
                    strengths=["Good docs: The repository is easy to understand."],
                    weaknesses=["No homepage: Reviewers cannot try it quickly."],
                    recommendations=["Add homepage: Publish a simple public entry point."],
                    showcase_value="High",
                    recruiter_signal="Useful portfolio signal",
                ),
            ],
            repo_checks=[
                RepoCheckResult(
                    repo_name="demo-a",
                    findings=["No tests found."],
                    score=ScoreSummary(overall=62, label="Fair", category_scores={"Documentation": 70}),
                ),
                RepoCheckResult(
                    repo_name="demo-b",
                    findings=["No homepage set."],
                    score=ScoreSummary(overall=78, label="Strong", category_scores={"Documentation": 85}),
                ),
            ],
            portfolio_summary=PortfolioSummary(
                summary="Useful portfolio start.",
                strongest_repos=["demo-a"],
                improvement_areas=["Testing"],
                top_actions=["Add tests"],
            ),
            portfolio_score=ScoreSummary(
                overall=70,
                label="Strong",
                category_scores={"Documentation": 78, "Engineering": 74},
            ),
        )

        markdown = _format_markdown_report(report)

        self.assertIn("# GitHub Portfolio Audit", markdown)
        self.assertIn("## Portfolio Score", markdown)
        self.assertIn("### demo-a", markdown)
        self.assertIn("## Portfolio Summary", markdown)
        self.assertIn("1. Add tests", markdown)
        self.assertIn("- **Readable README**: Setup and usage are easy to follow.", markdown)
        self.assertIn("- **No homepage**: Reviewers cannot try it quickly.", markdown)
        self.assertIn("1. **Add tests**: Introduce smoke tests for the core workflow.", markdown)

    def test_fallback_repo_audit_uses_deterministic_findings(self):
        repo_fact = RepoFacts(
            name="demo",
            description="A demo repository.",
            languages={"Python": 100},
        )
        repo_check = RepoCheckResult(
            repo_name="demo",
            findings=["No tests found.", "No license detected."],
            strengths=["README file detected."],
            score=ScoreSummary(overall=42, label="Needs Work", category_scores={"Engineering": 10}),
        )

        audit = _fallback_repo_audit(repo_fact, repo_check, RuntimeError("boom"))

        self.assertEqual("demo", audit.repo_name)
        self.assertIn("Automated repo analysis was unavailable", audit.summary)
        self.assertIn("No tests found.", audit.recommendations)
        self.assertIn("README file detected.", audit.strengths)

    @patch("src.report_builder.build_portfolio_score")
    @patch("src.report_builder.save_cached_report")
    @patch("src.report_builder.load_cached_report")
    @patch("src.report_builder.build_freshness_signature")
    @patch("src.report_builder.build_analysis_key")
    @patch("src.report_builder.analyze_repo")
    @patch("src.report_builder.run_repo_checks")
    def test_build_portfolio_feedback_uses_deterministic_format_for_single_repo(
        self,
        mock_run_repo_checks,
        mock_analyze_repo,
        mock_build_analysis_key,
        mock_build_freshness_signature,
        mock_load_cached_report,
        mock_save_cached_report,
        mock_build_portfolio_score,
    ):
        repo_fact = RepoFacts(name="demo", description="Demo repo", languages={"Python": 100})
        repo_check = RepoCheckResult(
            repo_name="demo",
            findings=["No tests found."],
            score=ScoreSummary(overall=72, label="Strong", category_scores={"Engineering": 70}),
        )
        repo_audit = RepoAudit(
            repo_name="demo",
            summary="A demo repository.",
            what_it_does="Shows the full report format.",
            key_technologies=["Python"],
            strengths=["Readable README: Setup and usage are easy to follow."],
            weaknesses=["No tests: There is no automated validation yet."],
            recommendations=["Add tests: Introduce smoke tests for the core workflow."],
            showcase_value="Medium",
            recruiter_signal="Needs polish",
        )

        mock_run_repo_checks.return_value = repo_check
        mock_analyze_repo.return_value = repo_audit
        mock_build_analysis_key.return_value = "analysis-key"
        mock_build_freshness_signature.return_value = "freshness-signature"
        mock_load_cached_report.return_value = None
        mock_save_cached_report.return_value = "2026-03-10T12:00:00+00:00"
        mock_build_portfolio_score.return_value = ScoreSummary(
            overall=72,
            label="Strong",
            category_scores={"Engineering": 70},
        )

        report = build_portfolio_feedback(
            github_username="demo",
            repo_facts=[repo_fact],
        )

        self.assertIn("**Repository**\ndemo", report.feedback_markdown)
        self.assertIn("## Strengths", report.feedback_markdown)
        self.assertIn("- **Readable README**: Setup and usage are easy to follow.", report.feedback_markdown)
        self.assertIn("## Findings", report.feedback_markdown)
        self.assertIn("- No tests found.", report.feedback_markdown)
        self.assertFalse(report.cache_hit)
        self.assertEqual("generated", report.cache_status)
        self.assertEqual("2026-03-10T12:00:00+00:00", report.cache_saved_at)
        mock_save_cached_report.assert_called_once()

    @patch("src.report_builder.build_portfolio_score")
    @patch("src.report_builder.save_cached_report")
    @patch("src.report_builder.load_cached_report")
    @patch("src.report_builder.build_freshness_signature")
    @patch("src.report_builder.build_analysis_key")
    @patch("src.report_builder.summarize_portfolio")
    @patch("src.report_builder.analyze_repo")
    @patch("src.report_builder.run_repo_checks")
    def test_build_portfolio_feedback_uses_deterministic_format_for_multi_repo(
        self,
        mock_run_repo_checks,
        mock_analyze_repo,
        mock_summarize_portfolio,
        mock_build_analysis_key,
        mock_build_freshness_signature,
        mock_load_cached_report,
        mock_save_cached_report,
        mock_build_portfolio_score,
    ):
        repo_facts = [
            RepoFacts(name="demo-a", description="Demo A", languages={"Python": 100}),
            RepoFacts(name="demo-b", description="Demo B", languages={"SQL": 100}),
        ]
        repo_checks = [
            RepoCheckResult(
                repo_name="demo-a",
                findings=["No tests found."],
                score=ScoreSummary(overall=72, label="Strong", category_scores={"Engineering": 70}),
            ),
            RepoCheckResult(
                repo_name="demo-b",
                findings=["No homepage set."],
                score=ScoreSummary(overall=68, label="Fair", category_scores={"Documentation": 60}),
            ),
        ]
        repo_audits = [
            RepoAudit(
                repo_name="demo-a",
                summary="A demo repository.",
                what_it_does="Shows the full report format.",
                key_technologies=["Python"],
                strengths=["Readable README: Setup and usage are easy to follow."],
                weaknesses=["No tests: There is no automated validation yet."],
                recommendations=["Add tests: Introduce smoke tests for the core workflow."],
                showcase_value="Medium",
                recruiter_signal="Needs polish",
            ),
            RepoAudit(
                repo_name="demo-b",
                summary="Another demo repository.",
                what_it_does="Shows multi-repo output.",
                key_technologies=["SQL"],
                strengths=["Good docs: The repository is easy to understand."],
                weaknesses=["No homepage: Reviewers cannot try it quickly."],
                recommendations=["Add homepage: Publish a simple public entry point."],
                showcase_value="High",
                recruiter_signal="Useful portfolio signal",
            ),
        ]

        mock_run_repo_checks.side_effect = repo_checks
        mock_analyze_repo.side_effect = repo_audits
        mock_build_analysis_key.return_value = "analysis-key"
        mock_build_freshness_signature.return_value = "freshness-signature"
        mock_load_cached_report.return_value = None
        mock_save_cached_report.return_value = "2026-03-10T12:00:00+00:00"
        mock_summarize_portfolio.return_value = PortfolioSummary(
            summary="Useful portfolio start.",
            strongest_repos=["demo-a"],
            improvement_areas=["Testing"],
            top_actions=["Add tests: Improve confidence in the codebase."],
        )
        mock_build_portfolio_score.return_value = ScoreSummary(
            overall=70,
            label="Strong",
            category_scores={"Documentation": 78, "Engineering": 74},
        )

        report = build_portfolio_feedback(
            github_username="demo",
            repo_facts=repo_facts,
        )

        self.assertIn("# GitHub Portfolio Audit", report.feedback_markdown)
        self.assertIn("### Top Actions", report.feedback_markdown)
        self.assertIn("1. **Add tests**: Improve confidence in the codebase.", report.feedback_markdown)
        self.assertIn("### demo-a", report.feedback_markdown)
        self.assertIn("- **Readable README**: Setup and usage are easy to follow.", report.feedback_markdown)
        self.assertIn("1. **Add homepage**: Publish a simple public entry point.", report.feedback_markdown)
        self.assertIn("- No homepage set.", report.feedback_markdown)
        self.assertFalse(report.cache_hit)
        self.assertEqual("generated", report.cache_status)
        mock_save_cached_report.assert_called_once()

    @patch("src.report_builder.load_cached_report")
    @patch("src.report_builder.build_freshness_signature")
    @patch("src.report_builder.build_analysis_key")
    @patch("src.report_builder.run_repo_checks")
    def test_build_portfolio_feedback_returns_cached_report_when_repo_fingerprint_matches(
        self,
        mock_run_repo_checks,
        mock_build_analysis_key,
        mock_build_freshness_signature,
        mock_load_cached_report,
    ):
        repo_fact = RepoFacts(
            name="demo",
            description="Demo repo",
            owner_login="demo",
            updated_at="2026-03-10T00:00:00Z",
            default_branch="main",
            default_branch_head_sha="abc123",
            languages={"Python": 100},
        )
        cached_report = PortfolioReport(
            github_username="demo",
            repo_count=1,
            feedback_markdown="# Cached",
            analysis_label="Selected Repository Analysis",
            cache_hit=True,
            cache_status="loaded",
            cache_saved_at="2026-03-10T12:00:00+00:00",
            repo_facts=[repo_fact],
            repo_checks=[RepoCheckResult(repo_name="demo")],
            repo_audits=[RepoAudit(repo_name="demo")],
        )

        mock_build_analysis_key.return_value = "analysis-key"
        mock_build_freshness_signature.return_value = "freshness-signature"
        mock_load_cached_report.return_value = cached_report

        report = build_portfolio_feedback(
            github_username="demo",
            repo_facts=[repo_fact],
        )

        self.assertEqual("# Cached", report.feedback_markdown)
        self.assertTrue(report.cache_hit)
        self.assertEqual("loaded", report.cache_status)
        mock_run_repo_checks.assert_not_called()

    @patch("src.report_builder.save_cached_report")
    @patch("src.report_builder.load_cached_report")
    @patch("src.report_builder.build_freshness_signature")
    @patch("src.report_builder.build_analysis_key")
    @patch("src.report_builder.analyze_repo")
    @patch("src.report_builder.run_repo_checks")
    @patch("src.report_builder.build_portfolio_score")
    def test_build_portfolio_feedback_force_refresh_bypasses_cache(
        self,
        mock_build_portfolio_score,
        mock_run_repo_checks,
        mock_analyze_repo,
        mock_build_analysis_key,
        mock_build_freshness_signature,
        mock_load_cached_report,
        mock_save_cached_report,
    ):
        repo_fact = RepoFacts(name="demo", description="Demo repo", languages={"Python": 100})
        repo_check = RepoCheckResult(
            repo_name="demo",
            findings=["No tests found."],
            score=ScoreSummary(overall=72, label="Strong", category_scores={"Engineering": 70}),
        )
        repo_audit = RepoAudit(
            repo_name="demo",
            summary="A demo repository.",
            what_it_does="Shows the full report format.",
            key_technologies=["Python"],
            strengths=["Readable README: Setup and usage are easy to follow."],
            weaknesses=["No tests: There is no automated validation yet."],
            recommendations=["Add tests: Introduce smoke tests for the core workflow."],
            showcase_value="Medium",
            recruiter_signal="Needs polish",
        )

        mock_run_repo_checks.return_value = repo_check
        mock_analyze_repo.return_value = repo_audit
        mock_build_analysis_key.return_value = "analysis-key"
        mock_build_freshness_signature.return_value = "freshness-signature"
        mock_load_cached_report.return_value = PortfolioReport(
            github_username="demo",
            repo_count=1,
            feedback_markdown="# Cached",
        )
        mock_save_cached_report.return_value = "2026-03-10T12:00:00+00:00"
        mock_build_portfolio_score.return_value = ScoreSummary(
            overall=72,
            label="Strong",
            category_scores={"Engineering": 70},
        )

        report = build_portfolio_feedback(
            github_username="demo",
            repo_facts=[repo_fact],
            force_refresh=True,
        )

        self.assertNotEqual("# Cached", report.feedback_markdown)
        self.assertFalse(report.cache_hit)
        self.assertEqual("refreshed", report.cache_status)
        mock_run_repo_checks.assert_called_once()


if __name__ == "__main__":
    unittest.main()
