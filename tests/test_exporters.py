import unittest
from unittest.mock import patch

from src.errors import ExportError
from src.exporters import (
    _build_report_html,
    _clean_inline_markdown,
    _parse_markdown_blocks,
    generate_pdf,
)


class ExportersTestCase(unittest.TestCase):
    def test_clean_inline_markdown_strips_common_formatting(self):
        cleaned = _clean_inline_markdown("**Bold** `code` and *italic*")

        self.assertEqual("Bold code and italic", cleaned)

    def test_parse_markdown_blocks_groups_lists_and_paragraphs(self):
        blocks = _parse_markdown_blocks(
            "# Title\n\n"
            "## Section\n"
            "Paragraph line one\n"
            "Paragraph line two\n\n"
            "- First bullet\n"
            "- Second bullet\n\n"
            "1. First step\n"
            "2. Second step\n"
        )

        self.assertEqual(("title", "Title"), blocks[0])
        self.assertEqual(("heading", "Section"), blocks[1])
        self.assertEqual(("paragraph", "Paragraph line one Paragraph line two"), blocks[2])
        self.assertEqual(
            (
                "list",
                [
                    {
                        "kind": "list_paragraph",
                        "level": 0,
                        "bullet": "•",
                        "text": "First bullet",
                        "continued": False,
                    },
                    {
                        "kind": "list_paragraph",
                        "level": 0,
                        "bullet": "•",
                        "text": "Second bullet",
                        "continued": False,
                    },
                ],
            ),
            blocks[3],
        )
        self.assertEqual(
            (
                "list",
                [
                    {
                        "kind": "list_paragraph",
                        "level": 0,
                        "bullet": "1.",
                        "text": "First step",
                        "continued": False,
                    },
                    {
                        "kind": "list_paragraph",
                        "level": 0,
                        "bullet": "2.",
                        "text": "Second step",
                        "continued": False,
                    },
                ],
            ),
            blocks[4],
        )

    def test_parse_markdown_blocks_keeps_spaced_ordered_items_in_one_list(self):
        blocks = _parse_markdown_blocks(
            "## Top Priority Actions\n\n"
            "1. First action\n\n"
            "1. Second action\n\n"
            "1. Third action\n"
        )

        self.assertEqual(("heading", "Top Priority Actions"), blocks[0])
        self.assertEqual(
            (
                "list",
                [
                    {
                        "kind": "list_paragraph",
                        "level": 0,
                        "bullet": "1.",
                        "text": "First action",
                        "continued": False,
                    },
                    {
                        "kind": "list_paragraph",
                        "level": 0,
                        "bullet": "2.",
                        "text": "Second action",
                        "continued": False,
                    },
                    {
                        "kind": "list_paragraph",
                        "level": 0,
                        "bullet": "3.",
                        "text": "Third action",
                        "continued": False,
                    },
                ],
            ),
            blocks[1],
        )

    def test_parse_markdown_blocks_preserves_nested_list_levels(self):
        blocks = _parse_markdown_blocks(
            "## Strengths\n\n"
            "- Parent point\n"
            "  - Child point one\n"
            "  - Child point two\n\n"
            "1. Action one\n"
            "   - Detail one\n"
            "   - Detail two\n"
        )

        self.assertEqual(("heading", "Strengths"), blocks[0])
        self.assertEqual(
            (
                "list",
                [
                    {
                        "kind": "list_paragraph",
                        "level": 0,
                        "bullet": "•",
                        "text": "Parent point",
                        "continued": False,
                    },
                    {
                        "kind": "list_paragraph",
                        "level": 1,
                        "bullet": "–",
                        "text": "Child point one",
                        "continued": False,
                    },
                    {
                        "kind": "list_paragraph",
                        "level": 1,
                        "bullet": "–",
                        "text": "Child point two",
                        "continued": False,
                    },
                ],
            ),
            blocks[1],
        )
        self.assertEqual(
            (
                "list",
                [
                    {
                        "kind": "list_paragraph",
                        "level": 0,
                        "bullet": "1.",
                        "text": "Action one",
                        "continued": False,
                    },
                    {
                        "kind": "list_paragraph",
                        "level": 1,
                        "bullet": "–",
                        "text": "Detail one",
                        "continued": False,
                    },
                    {
                        "kind": "list_paragraph",
                        "level": 1,
                        "bullet": "–",
                        "text": "Detail two",
                        "continued": False,
                    },
                ],
            ),
            blocks[2],
        )

    def test_generate_pdf_returns_pdf_bytes(self):
        report = (
            "# GitHub Portfolio Audit\n\n"
            "## Executive Summary\n"
            "A concise summary for the PDF export.\n\n"
            "### Strongest Repositories\n"
            "- Repo A\n"
            "- Repo B\n"
        )

        pdf = generate_pdf(report).getvalue()

        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 500)

    def test_build_report_html_contains_rendered_markdown_structure(self):
        html_output = _build_report_html(
            "# Title\n\n"
            "Paragraph with **bold** text.\n\n"
            "## Strengths\n"
            "- Strong point\n\n"
            "1. First action\n"
            "   - Nested detail\n"
        )

        self.assertIn("<h1>Title</h1>", html_output)
        self.assertIn("<strong>bold</strong>", html_output)
        self.assertIn("<ol>", html_output)
        self.assertIn("<ul>", html_output)
        self.assertIn("section-strengths", html_output)
        self.assertIn("insight-card", html_output)
        self.assertIn("section-lead", html_output)

    def test_build_report_html_turns_nested_strengths_into_cards(self):
        html_output = _build_report_html(
            "# Title\n\n"
            "## Strengths\n"
            "- **Clear project positioning**\n"
            "  - Focused README with screenshots\n"
            "  - Clear project purpose\n\n"
            "## Weaknesses\n"
            "- **No live demo or homepage**\n"
            "  - Recruiters cannot evaluate the project quickly\n"
        )

        self.assertIn('<section class="report-section section-strengths">', html_output)
        self.assertIn('<article class="insight-card">', html_output)
        self.assertIn("insight-card-title", html_output)
        self.assertIn("Focused README with screenshots", html_output)
        self.assertIn('<section class="report-section section-weaknesses">', html_output)

    def test_build_report_html_strips_full_bold_from_findings(self):
        html_output = _build_report_html(
            "# Title\n\n"
            "## Findings\n"
            "- **No homepage or live demo link is set.**\n"
            "- There is a **model naming inconsistency** between the repo description and README.\n"
        )

        findings_start = html_output.index('<section class="report-section section-findings">')
        findings_html = html_output[findings_start:]

        self.assertIn("No homepage or live demo link is set.", findings_html)
        self.assertIn("model naming inconsistency", findings_html)
        self.assertNotIn("<strong>", findings_html)

    @patch("src.exporters._generate_pdf_with_playwright", side_effect=RuntimeError("no browser"))
    def test_generate_pdf_falls_back_when_playwright_backend_fails(self, _mock_generate_pdf):
        pdf = generate_pdf("# Fallback Test").getvalue()

        self.assertTrue(pdf.startswith(b"%PDF"))

    @patch("src.exporters._generate_pdf_with_reportlab", side_effect=RuntimeError("reportlab failed"))
    @patch("src.exporters._generate_pdf_with_playwright", side_effect=RuntimeError("playwright failed"))
    def test_generate_pdf_raises_export_error_when_both_backends_fail(
        self,
        _mock_generate_pdf,
        _mock_reportlab,
    ):
        with self.assertRaises(ExportError):
            generate_pdf("# Export Failure Test")


if __name__ == "__main__":
    unittest.main()
