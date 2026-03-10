import unittest
from unittest.mock import MagicMock, patch

from src.errors import GithubRateLimitError
from src.github_client import (
    _get_default_branch_head_sha,
    _get_header_candidates,
    _request,
    get_github_repos,
)


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


if __name__ == "__main__":
    unittest.main()
