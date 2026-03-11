import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import requests

from src.errors import GithubOAuthError
from src.github_auth import (
    build_authorize_url,
    consume_oauth_state,
    exchange_code_for_token,
    get_authenticated_user,
    oauth_is_configured,
    register_oauth_state,
)


class GithubAuthTestCase(unittest.TestCase):
    @patch("src.github_auth.load_github_oauth_client_id", return_value="client-123")
    @patch("src.github_auth.load_github_oauth_redirect_uri", return_value="http://localhost:8501")
    def test_build_authorize_url_contains_required_oauth_parameters(
        self,
        _mock_redirect_uri,
        _mock_client_id,
    ):
        url = build_authorize_url("state-abc")
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        self.assertEqual("https", parsed.scheme)
        self.assertEqual("github.com", parsed.netloc)
        self.assertEqual(["client-123"], params["client_id"])
        self.assertEqual(["http://localhost:8501"], params["redirect_uri"])
        self.assertEqual(["state-abc"], params["state"])

    @patch("src.github_auth.requests.post")
    @patch("src.github_auth.load_github_oauth_client_id", return_value="client-123")
    @patch("src.github_auth.load_github_oauth_client_secret", return_value="secret-456")
    @patch("src.github_auth.load_github_oauth_redirect_uri", return_value="http://localhost:8501")
    def test_exchange_code_for_token_returns_access_token(
        self,
        _mock_redirect_uri,
        _mock_client_secret,
        _mock_client_id,
        mock_post,
    ):
        response = MagicMock()
        response.json.return_value = {"access_token": "token-xyz"}
        response.raise_for_status.return_value = None
        mock_post.return_value = response

        token = exchange_code_for_token("code-123", state="state-abc")

        self.assertEqual("token-xyz", token)
        mock_post.assert_called_once()

    @patch("src.github_auth.requests.post")
    @patch("src.github_auth.load_github_oauth_client_id", return_value="client-123")
    @patch("src.github_auth.load_github_oauth_client_secret", return_value="secret-456")
    @patch("src.github_auth.load_github_oauth_redirect_uri", return_value="http://localhost:8501")
    def test_exchange_code_for_token_raises_oauth_error_on_http_failure(
        self,
        _mock_redirect_uri,
        _mock_client_secret,
        _mock_client_id,
        mock_post,
    ):
        response = MagicMock()
        response.raise_for_status.side_effect = requests.RequestException("boom")
        mock_post.return_value = response

        with self.assertRaises(GithubOAuthError):
            exchange_code_for_token("code-123", state="state-abc")

    @patch("src.github_auth.requests.get")
    def test_get_authenticated_user_raises_oauth_error_on_http_failure(self, mock_get):
        response = MagicMock()
        response.raise_for_status.side_effect = requests.RequestException("boom")
        mock_get.return_value = response

        with self.assertRaises(GithubOAuthError):
            get_authenticated_user("token-xyz")

    @patch("src.github_auth.load_github_oauth_client_id", return_value="client-123")
    @patch("src.github_auth.load_github_oauth_client_secret", return_value="secret-456")
    @patch("src.github_auth.load_github_oauth_redirect_uri", return_value="http://localhost:8501")
    def test_oauth_is_configured_returns_true_when_all_values_exist(
        self,
        _mock_redirect_uri,
        _mock_client_secret,
        _mock_client_id,
    ):
        self.assertTrue(oauth_is_configured())

    def test_registered_oauth_state_can_be_consumed_once(self):
        register_oauth_state("state-123")

        self.assertTrue(consume_oauth_state("state-123"))
        self.assertFalse(consume_oauth_state("state-123"))

    def test_registered_oauth_state_can_use_custom_registry(self):
        registry = {}

        register_oauth_state("state-456", registry=registry)

        self.assertIn("state-456", registry)
        self.assertTrue(consume_oauth_state("state-456", registry=registry))
        self.assertFalse(consume_oauth_state("state-456", registry=registry))

    @patch("src.github_auth.load_github_oauth_scope", return_value="read:user user:email")
    @patch("src.github_auth.load_github_oauth_client_id", return_value="client-123")
    @patch("src.github_auth.load_github_oauth_redirect_uri", return_value="http://localhost:8501")
    def test_build_authorize_url_uses_runtime_scope_loader(
        self,
        _mock_redirect_uri,
        _mock_client_id,
        _mock_scope,
    ):
        url = build_authorize_url("state-scope")
        params = parse_qs(urlparse(url).query)

        self.assertEqual(["read:user user:email"], params["scope"])


if __name__ == "__main__":
    unittest.main()
