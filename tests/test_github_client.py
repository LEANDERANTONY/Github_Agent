import unittest
from unittest.mock import MagicMock, patch

from src.github_client import _get_header_candidates, _request, get_github_repos


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


if __name__ == "__main__":
    unittest.main()
