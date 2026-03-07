import html
import re
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _clean_inline_markdown(text):
    cleaned = (text or "").strip()
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    return cleaned


def _paragraph_text(text):
    return html.escape(_clean_inline_markdown(text))


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            textColor=colors.HexColor("#1f2933"),
            alignment=TA_LEFT,
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=21,
            textColor=colors.HexColor("#1f2933"),
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#334155"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCopy",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#243240"),
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletCopy",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#243240"),
            leftIndent=14,
            firstLineIndent=0,
            bulletIndent=0,
            spaceAfter=5,
        )
    )
    return styles


def generate_pdf(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=42,
        leftMargin=42,
        topMargin=52,
        bottomMargin=42,
        title="GitHub Portfolio Review",
    )

    styles = _build_styles()
    flowables = []
    title_rendered = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()

        if not stripped:
            flowables.append(Spacer(1, 6))
            continue

        if stripped.startswith("# "):
            line_text = _paragraph_text(stripped[2:])
            style = styles["ReportTitle"] if not title_rendered else styles["SectionHeading"]
            flowables.append(Paragraph(line_text, style))
            title_rendered = True
            continue

        if stripped.startswith("## "):
            flowables.append(Paragraph(_paragraph_text(stripped[3:]), styles["SectionHeading"]))
            continue

        if stripped.startswith("### "):
            flowables.append(Paragraph(_paragraph_text(stripped[4:]), styles["SubHeading"]))
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flowables.append(Paragraph(_paragraph_text(stripped), styles["BodyCopy"]))
            continue

        if stripped.startswith("- "):
            flowables.append(
                Paragraph(
                    _paragraph_text(stripped[2:]),
                    styles["BulletCopy"],
                    bulletText="•",
                )
            )
            continue

        flowables.append(Paragraph(_paragraph_text(stripped), styles["BodyCopy"]))

    doc.build(flowables)
    buffer.seek(0)
    return buffer


def generate_markdown(text):
    return BytesIO((text or "").encode("utf-8"))
