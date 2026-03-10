import tempfile
import unittest
from pathlib import Path

from src.analysis_store import (
    build_analysis_key,
    build_freshness_signature,
    load_cached_report,
    save_cached_report,
)
from src.schemas import PortfolioReport, PortfolioSummary, RepoAudit, RepoCheckResult, RepoFacts, ScoreSummary


class AnalysisStoreTestCase(unittest.TestCase):
    def test_cached_report_round_trip_uses_freshness_signature(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "analysis_cache.sqlite3"
            report = PortfolioReport(
                github_username="demo",
                repo_count=1,
                feedback_markdown="# GitHub Repository Audit",
                analysis_label="Selected Repository Analysis",
                repo_facts=[
                    RepoFacts(
                        name="demo",
                        description="Demo repo",
                        owner_login="demo",
                        updated_at="2026-03-10T00:00:00Z",
                        default_branch="main",
                        default_branch_head_sha="abc123",
                        languages={"Python": 100},
                    )
                ],
                repo_checks=[
                    RepoCheckResult(
                        repo_name="demo",
                        findings=["No tests found."],
                        strengths=["README detected."],
                        score=ScoreSummary(overall=72, label="Strong", category_scores={"Engineering": 70}),
                    )
                ],
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
                portfolio_summary=PortfolioSummary(),
                portfolio_score=ScoreSummary(overall=72, label="Strong", category_scores={"Engineering": 70}),
            )

            analysis_key = build_analysis_key("demo", ["demo"], None, False)
            freshness_signature = build_freshness_signature(report.repo_facts)

            save_cached_report(
                analysis_key=analysis_key,
                github_username="demo",
                freshness_signature=freshness_signature,
                report=report,
                db_path=db_path,
            )

            loaded_report = load_cached_report(
                analysis_key=analysis_key,
                freshness_signature=freshness_signature,
                db_path=db_path,
            )

            self.assertIsNotNone(loaded_report)
            self.assertEqual("demo", loaded_report.repo_audits[0].repo_name)
            self.assertEqual("abc123", loaded_report.repo_facts[0].default_branch_head_sha)
            self.assertEqual("# GitHub Repository Audit", loaded_report.feedback_markdown)

            stale_report = load_cached_report(
                analysis_key=analysis_key,
                freshness_signature="different-signature",
                db_path=db_path,
            )

            self.assertIsNone(stale_report)


if __name__ == "__main__":
    unittest.main()
