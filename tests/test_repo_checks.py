import unittest

from src.repo_checks import run_repo_checks
from src.schemas import RepoFacts


class RepoChecksTestCase(unittest.TestCase):
    def test_flags_missing_basics(self):
        repo_facts = RepoFacts(
            name="demo",
            description="No description",
            updated_at="2023-01-01T00:00:00Z",
            repo_size_kb=10,
            readme_present=False,
        )

        result = run_repo_checks(repo_facts)

        self.assertIn("Missing repository description.", result.findings)
        self.assertIn("No README detected.", result.findings)
        self.assertIn("No homepage or live demo link set.", result.findings)
        self.assertIn("No GitHub topics configured.", result.findings)
        self.assertIn("No license detected.", result.findings)
        self.assertIn("Repository has not been updated in over a year.", result.findings)
        self.assertIn("Repository is very small and may look incomplete.", result.findings)
        self.assertEqual("Needs Work", result.score.label)
        self.assertLess(result.score.overall, 55)

    def test_detects_strength_signals(self):
        repo_facts = RepoFacts(
            name="strong-repo",
            description="Production-ready service",
            homepage="https://example.com",
            topics=["python", "api"],
            updated_at="2099-01-01T00:00:00Z",
            license_name="MIT",
            repo_size_kb=500,
            languages={"Python": 1000},
            root_entries=["tests", "pyproject.toml", ".github"],
            readme_present=True,
            readme_text="This project includes installation, usage, and deployment details." * 10,
        )

        result = run_repo_checks(repo_facts)

        self.assertIn("Repository description is present.", result.strengths)
        self.assertIn("README file detected.", result.strengths)
        self.assertIn("Homepage or live demo link is configured.", result.strengths)
        self.assertIn("GitHub topics are configured.", result.strengths)
        self.assertIn("Repository license is configured.", result.strengths)
        self.assertIn("Test-related files or directories are present.", result.strengths)
        self.assertIn("Setup or dependency files are present at the repository root.", result.strengths)
        self.assertIn("Repository appears to include CI or automation configuration.", result.strengths)
        self.assertEqual([], result.findings)
        self.assertEqual("Excellent", result.score.label)
        self.assertGreaterEqual(result.score.overall, 85)


if __name__ == "__main__":
    unittest.main()
