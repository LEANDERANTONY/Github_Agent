import unittest

from src.report_builder import _fallback_repo_audit, _format_markdown_report
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
                    strengths=["Readable README"],
                    weaknesses=["No tests"],
                    recommendations=["Add tests"],
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
        self.assertIn("## Repository Score", markdown)
        self.assertIn("## Repository Summary", markdown)
        self.assertIn("## Top Priority Actions", markdown)
        self.assertIn("- Add tests", markdown)

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
                    strengths=["Readable README"],
                    weaknesses=["No tests"],
                    recommendations=["Add tests"],
                    showcase_value="Medium",
                    recruiter_signal="Needs polish",
                ),
                RepoAudit(
                    repo_name="demo-b",
                    summary="Another demo repository.",
                    what_it_does="Shows multi-repo output.",
                    key_technologies=["SQL"],
                    strengths=["Good docs"],
                    weaknesses=["No homepage"],
                    recommendations=["Add homepage"],
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


if __name__ == "__main__":
    unittest.main()
