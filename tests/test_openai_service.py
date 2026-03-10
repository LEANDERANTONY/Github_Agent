import unittest
from unittest.mock import MagicMock, patch

from src.errors import OpenAIAnalysisError
from src.openai_service import _extract_json_payload, _request_json, summarize_portfolio
from src.schemas import RepoAudit, RepoCheckResult, ScoreSummary


class OpenAIServiceTestCase(unittest.TestCase):
    def test_extract_json_payload_raises_when_no_json_is_present(self):
        with self.assertRaises(OpenAIAnalysisError) as error:
            _extract_json_payload("not json at all")

        self.assertIn("invalid response format", error.exception.user_message.lower())

    def test_request_json_wraps_client_failure(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = RuntimeError("upstream failure")

        with self.assertRaises(OpenAIAnalysisError) as error:
            _request_json(client, "prompt", "gpt-test")

        self.assertIn("analysis request failed", error.exception.user_message.lower())

    def test_summarize_portfolio_requires_repo_audits(self):
        with self.assertRaises(OpenAIAnalysisError):
            summarize_portfolio([], [])

    @patch("src.openai_service._create_client")
    def test_summarize_portfolio_normalizes_model_payload(self, mock_create_client):
        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content='{"summary":"S","strongest_repos":["a"],"improvement_areas":["b"],"top_actions":["c"]}'))]

        client = MagicMock()
        client.chat.completions.create.return_value = response
        mock_create_client.return_value = client

        summary = summarize_portfolio(
            [RepoAudit(repo_name="demo", summary="Repo summary")],
            [RepoCheckResult(repo_name="demo", findings=["No tests"], score=ScoreSummary(overall=70, label="Strong"))],
        )

        self.assertEqual("S", summary.summary)
        self.assertEqual(["a"], summary.strongest_repos)
        self.assertEqual(["b"], summary.improvement_areas)
        self.assertEqual(["c"], summary.top_actions)


if __name__ == "__main__":
    unittest.main()
