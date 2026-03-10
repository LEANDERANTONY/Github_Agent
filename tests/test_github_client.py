import unittest
from unittest.mock import MagicMock, patch

from src.errors import GithubRateLimitError
from src.github_client import (
    _get_default_branch_head_sha,
    _get_header_candidates,
    _request,
    get_portfolio_repo_facts,
    get_github_repos,
)
from src.schemas import RepoFacts


class GithubClientTestCase(unittest.TestCase):
    def test_get_header_candidates_returns_anonymous_headers_only(self):
        candidates = _get_header_candidates()

        self.assertEqual(1, len(candidates))
        self.assertEqual("application/vnd.github+json", candidates[0]["Accept"])
        self.assertNotIn("Authorization", candidates[0])

    def test_get_github_repos_requires_public_username(self):
        with self.assertRaises(Exception):
            get_github_repos(username=None)

    @patch("src.github_client.requests.get")
    def test_request_raises_with_github_api_status_details(self, mock_get):
        response = MagicMock()
        response.status_code = 403
        response.text = "rate limit exceeded"
        mock_get.return_value = response

        with self.assertRaises(Exception) as error:
            _request("https://api.github.com/users/demo/repos", _get_header_candidates())

        self.assertIn("GitHub API error 403", str(error.exception))
        self.assertIn("rate limit exceeded", str(error.exception))

    @patch("src.github_client.requests.get")
    def test_request_raises_rate_limit_error_with_specific_message(self, mock_get):
        response = MagicMock()
        response.status_code = 403
        response.text = "API rate limit exceeded"
        response.headers = {"X-RateLimit-Remaining": "0"}
        mock_get.return_value = response

        with self.assertRaises(GithubRateLimitError) as error:
            _request("https://api.github.com/users/demo/repos", _get_header_candidates())

        self.assertIn("GitHub rate limit reached", error.exception.user_message)

    @patch("src.github_client.time.sleep")
    @patch("src.github_client.requests.get")
    def test_request_retries_transient_server_error_before_succeeding(self, mock_get, mock_sleep):
        response_502 = MagicMock()
        response_502.status_code = 502
        response_502.text = "bad gateway"
        response_502.headers = {}

        response_200 = MagicMock()
        response_200.status_code = 200

        mock_get.side_effect = [response_502, response_200]

        response = _request("https://api.github.com/users/demo/repos", _get_header_candidates())

        self.assertIs(response_200, response)
        self.assertEqual(2, mock_get.call_count)
        mock_sleep.assert_called_once()

    @patch("src.github_client._request_json")
    def test_get_default_branch_head_sha_returns_commit_sha(self, mock_request_json):
        mock_request_json.return_value = {
            "commit": {
                "sha": "abc123def456",
            }
        }

        sha = _get_default_branch_head_sha(
            owner_login="demo",
            repo_name="sample",
            default_branch="main",
            header_candidates=_get_header_candidates(),
        )

        self.assertEqual("abc123def456", sha)

    @patch("src.github_client._build_repo_facts")
    @patch("src.github_client.get_github_repos")
    def test_get_portfolio_repo_facts_preserves_repo_order_when_fetching_in_parallel(
        self,
        mock_get_github_repos,
        mock_build_repo_facts,
    ):
        repos = [
            {"name": "repo-a", "owner": {"login": "demo"}, "updated_at": "2026-03-10T00:00:00Z"},
            {"name": "repo-b", "owner": {"login": "demo"}, "updated_at": "2026-03-09T00:00:00Z"},
            {"name": "repo-c", "owner": {"login": "demo"}, "updated_at": "2026-03-08T00:00:00Z"},
        ]
        mock_get_github_repos.return_value = repos
        mock_build_repo_facts.side_effect = [
            RepoFacts(name="repo-a", description="A"),
            RepoFacts(name="repo-b", description="B"),
            RepoFacts(name="repo-c", description="C"),
        ]

        repo_facts = get_portfolio_repo_facts(username="demo")

        self.assertEqual(["repo-a", "repo-b", "repo-c"], [item.name for item in repo_facts])


if __name__ == "__main__":
    unittest.main()
