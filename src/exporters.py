import html
import re
from io import BytesIO

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)

from src.errors import ExportError


_MARKDOWN = MarkdownIt("commonmark", {"html": False})


def _clean_inline_markdown(text):
    cleaned = (text or "").strip()
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    return cleaned


def _paragraph_text(text):
    return html.escape(text or "")


def _extract_tag_block(content, start_index, tag_name):
    open_tag = "<{tag}".format(tag=tag_name)
    close_tag = "</{tag}>".format(tag=tag_name)
    depth = 0
    index = start_index

    while index < len(content):
        next_open = content.find(open_tag, index)
        next_close = content.find(close_tag, index)

        if next_close == -1:
            raise ValueError("Missing closing tag for {tag}".format(tag=tag_name))

        if next_open != -1 and next_open < next_close:
            depth += 1
            index = next_open + len(open_tag)
            continue

        depth -= 1
        index = next_close + len(close_tag)
        if depth == 0:
            return content[start_index:index], index

    raise ValueError("Unbalanced tag block for {tag}".format(tag=tag_name))


def _split_top_level_list_items(list_html):
    items = []
    current = 0

    while True:
        li_start = list_html.find("<li>", current)
        if li_start == -1:
            break
        item_html, next_index = _extract_tag_block(list_html, li_start, "li")
        items.append(item_html)
        current = next_index

    return items


def _split_list_item_content(inner_html):
    inline_parts = []
    nested_parts = []
    index = 0

    while index < len(inner_html):
        next_ul = inner_html.find("<ul>", index)
        next_ol = inner_html.find("<ol>", index)
        candidates = [(pos, tag) for pos, tag in ((next_ul, "ul"), (next_ol, "ol")) if pos != -1]

        if not candidates:
            inline_parts.append(inner_html[index:])
            break

        next_index, tag_name = min(candidates, key=lambda value: value[0])
        inline_parts.append(inner_html[index:next_index])
        block_html, index = _extract_tag_block(inner_html, next_index, tag_name)
        nested_parts.append(block_html)

    return "".join(inline_parts).strip(), "".join(nested_parts).strip()


def _extract_paragraphs(html_fragment):
    paragraphs = re.findall(r"<p(?: [^>]*)?>(.*?)</p>", html_fragment or "", flags=re.DOTALL)
    if paragraphs:
        return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]

    cleaned = (html_fragment or "").strip()
    return [cleaned] if cleaned else []


def _split_title_body(paragraph_html):
    title_match = re.match(r"^<strong>(.*?)</strong>:\s*(.*)$", paragraph_html or "", flags=re.DOTALL)
    if title_match:
        return title_match.group(1).strip(), title_match.group(2).strip()

    if re.fullmatch(r"<strong>.*?</strong>", paragraph_html or "", flags=re.DOTALL):
        title = re.sub(r"^<strong>|</strong>$", "", paragraph_html, flags=re.DOTALL).strip()
        return title, ""

    return "", (paragraph_html or "").strip()


def _build_insight_card(item_html):
    inner_html = re.sub(r"^<li>|</li>$", "", item_html.strip(), flags=re.DOTALL).strip()
    summary_html, nested_html = _split_list_item_content(inner_html)
    paragraphs = _extract_paragraphs(summary_html)
    title = ""
    body_parts = []

    if paragraphs:
        title, first_body = _split_title_body(paragraphs[0])
        if first_body:
            body_parts.append(first_body)
        body_parts.extend(paragraphs[1:])
    else:
        title = ""
        body_parts = []

    body = "".join('<p class="insight-card-body">{body}</p>'.format(body=part) for part in body_parts)

    card_parts = ['<article class="insight-card">']
    if title:
        card_parts.append('<p class="insight-card-title">{title}</p>'.format(title=title))
    elif body_parts:
        body = "".join('<p class="insight-card-body">{body}</p>'.format(body=part) for part in body_parts[:1])
        body_parts = body_parts[1:]

    if body:
        card_parts.append(body)
    if nested_html:
        card_parts.append(nested_html)
    card_parts.append("</article>")
    return "".join(card_parts)


def _render_insight_cards(section_html):
    list_start = section_html.find("<ul>")
    if list_start == -1:
        return section_html, ""
    list_html, _ = _extract_tag_block(section_html, list_start, "ul")
    cards = [
        _build_insight_card(item_html)
        for item_html in _split_top_level_list_items(list_html)
    ]
    if not cards:
        return section_html, ""

    trailing_html = section_html.replace(list_html, "", 1).strip()
    lead_html = cards[0]
    grid_html = ""
    if len(cards) > 1:
        grid_html = '<div class="insight-grid">{cards}</div>'.format(cards="".join(cards[1:]))

    return trailing_html, lead_html + grid_html


def _strip_all_bold(html_fragment):
    return re.sub(r"</?strong>", "", html_fragment)


def _normalize_supporting_html(html_fragment):
    normalized = html_fragment or ""
    normalized = re.sub(
        r"<p>\s*<strong>([^<]+)</strong>\s*</p>",
        r'<p class="standalone-label">\1</p>',
        normalized,
    )
    normalized = re.sub(
        r"<p><strong>([^<]+)</strong>:\s*(.*?)</p>",
        r'<div class="inline-callout"><span class="inline-callout-label">\1</span><span class="inline-callout-body">\2</span></div>',
        normalized,
        flags=re.DOTALL,
    )
    return normalized


def _render_action_items(section_html):
    list_start = section_html.find("<ol>")
    if list_start == -1:
        return section_html

    list_html, _ = _extract_tag_block(section_html, list_start, "ol")
    items_html = []

    for index, item_html in enumerate(_split_top_level_list_items(list_html), start=1):
        inner_html = re.sub(r"^<li>|</li>$", "", item_html.strip(), flags=re.DOTALL).strip()
        summary_html, nested_html = _split_list_item_content(inner_html)
        paragraphs = _extract_paragraphs(summary_html)

        title = ""
        body_parts = []
        if paragraphs:
            title, first_body = _split_title_body(paragraphs[0])
            if not title:
                title = re.sub(r"<[^>]+>", "", paragraphs[0]).strip()
                first_body = ""
            if first_body:
                body_parts.append(first_body)
            body_parts.extend(paragraphs[1:])

        body_html = "".join(
            '<p class="action-body">{body}</p>'.format(body=paragraph)
            for paragraph in body_parts
        )
        nested_block_html = nested_html
        items_html.append(
            (
                '<article class="action-item">'
                '<div class="action-number">{number}</div>'
                '<div class="action-content">'
                '<p class="action-title">{title}</p>'
                '{body}{nested}'
                '</div>'
                '</article>'
            ).format(number=index, title=title, body=body_html, nested=nested_block_html)
        )

    rendered = '<div class="action-list">{items}</div>'.format(items="".join(items_html))
    return section_html.replace(list_html, rendered, 1)


def _render_findings_list(section_html):
    list_start = section_html.find("<ul>")
    list_tag = "ul"
    if list_start == -1:
        list_start = section_html.find("<ol>")
        list_tag = "ol"
    if list_start == -1:
        return section_html

    list_html, _ = _extract_tag_block(section_html, list_start, list_tag)
    items_html = []

    for item_html in _split_top_level_list_items(list_html):
        inner_html = re.sub(r"^<li>|</li>$", "", item_html.strip(), flags=re.DOTALL).strip()
        summary_html, nested_html = _split_list_item_content(inner_html)
        paragraphs = _extract_paragraphs(summary_html)

        body_parts = []
        if paragraphs:
            title, first_body = _split_title_body(paragraphs[0])
            if title and first_body:
                body_parts.append("<strong>{title}:</strong> {body}".format(title=title, body=first_body))
            elif title:
                body_parts.append(title)
            else:
                body_parts.append(paragraphs[0])
            body_parts.extend(paragraphs[1:])

        body_html = "".join(
            '<p class="finding-body">{body}</p>'.format(body=paragraph)
            for paragraph in body_parts
        )
        items_html.append(
            '<article class="finding-item"><div class="finding-marker"></div><div class="finding-content">{body}{nested}</div></article>'.format(
                body=body_html,
                nested=nested_html,
            )
        )

    rendered = '<div class="finding-list">{items}</div>'.format(items="".join(items_html))
    return section_html.replace(list_html, rendered, 1)


def _build_report_sections(body_html):
    parts = re.split(r"(<h2>.*?</h2>)", body_html or "", flags=re.DOTALL)
    sections = []

    intro_html = _normalize_supporting_html((parts[0] if parts else "").strip())
    if intro_html:
        sections.append(
            '<section class="report-section is-intro">{body}</section>'.format(body=intro_html)
        )

    for index in range(1, len(parts), 2):
        heading_html = parts[index]
        content_html = parts[index + 1] if index + 1 < len(parts) else ""
        title_match = re.search(r"<h2>(.*?)</h2>", heading_html, flags=re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Section"
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        normalized_content = _normalize_supporting_html(content_html.strip())
        section_class = "report-section section-{slug}".format(slug=slug)

        if slug in {"strengths", "weaknesses"}:
            trailing_html, cards_html = _render_insight_cards(normalized_content)
            section_body = '<div class="section-lead">{heading}{card}</div>{rest}'.format(
                heading=heading_html,
                card=cards_html,
                rest=trailing_html,
            )
        elif slug == "findings":
            section_body = "{heading}{body}".format(
                heading=heading_html,
                body=_render_findings_list(_strip_all_bold(normalized_content)),
            )
        elif slug == "top-priority-actions":
            section_body = "{heading}{body}".format(
                heading=heading_html,
                body=_render_action_items(normalized_content),
            )
        else:
            section_body = "{heading}{body}".format(
                heading=heading_html,
                body=normalized_content,
            )

        sections.append('<section class="{klass}">{body}</section>'.format(klass=section_class, body=section_body))

    return "".join(sections)


def _wrap_report_html(body_html):
    normalized_body = _build_report_sections(body_html or "<p>No report content available.</p>")

    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>GitHub Portfolio Review</title>
  <style>
    :root {{
      --ink: #162033;
      --muted: #546273;
      --accent: #1d4ed8;
      --accent-strong: #1e40af;
      --accent-soft: #e8f1ff;
      --blue-soft: #e8f1ff;
      --line: #d9e0e7;
      --paper: #fffdf8;
      --panel: #f8f3e8;
      --panel-strong: #f3ede0;
      --code: #f5f7fb;
    }}

    @page {{
      size: A4;
      margin: 22mm 16mm 22mm 16mm;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      color: var(--ink);
      background: var(--paper);
      line-height: 1.68;
      font-size: 10.8pt;
      text-rendering: geometricPrecision;
    }}

    .report-shell {{
      position: relative;
    }}

    .report-shell::before {{
      content: "";
      display: block;
      height: 5px;
      width: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, #1d4ed8 0%, #2563eb 58%, #60a5fa 100%);
      margin-bottom: 20px;
    }}

    .report-section {{
      background: linear-gradient(180deg, rgba(248, 243, 232, 0.82), rgba(255, 253, 248, 0.96));
      border: 1px solid rgba(217, 224, 231, 0.9);
      border-radius: 16px;
      padding: 16px 18px 14px;
      margin: 0 0 16px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.75);
      break-inside: avoid;
    }}

    .report-section.is-intro {{
      padding-top: 18px;
    }}

    .report-section.section-strengths,
    .report-section.section-weaknesses {{
      background: linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(255, 255, 255, 0.98));
    }}

    .section-lead {{
      break-inside: avoid;
      page-break-inside: avoid;
      margin-bottom: 12px;
    }}

    h1, h2, h3 {{
      color: var(--ink);
      margin: 0;
      break-after: avoid;
      page-break-after: avoid;
    }}

    h1 {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: 25pt;
      line-height: 1.12;
      margin-bottom: 16px;
      letter-spacing: -0.02em;
    }}

    h2 {{
      margin-top: 0;
      margin-bottom: 12px;
      padding: 0 0 8px;
      border-bottom: 1px solid rgba(217, 224, 231, 0.9);
      font-size: 15pt;
      font-weight: 700;
      letter-spacing: -0.01em;
      break-after: avoid;
      page-break-after: avoid;
    }}

    h2 + * {{
      break-before: avoid;
      page-break-before: avoid;
    }}

    h3 {{
      margin-top: 16px;
      margin-bottom: 7px;
      font-size: 12.1pt;
      color: #1d4ed8;
    }}

    p {{
      margin: 0 0 11px;
      orphans: 3;
      widows: 3;
    }}

    .standalone-label {{
      margin-top: 10px;
      margin-bottom: 5px;
      color: var(--accent-strong);
      font-size: 8.6pt;
      font-weight: 700;
      letter-spacing: 0.11em;
      text-transform: uppercase;
    }}

    ul, ol {{
      margin: 0 0 13px 1.25rem;
      padding: 0;
    }}

    li {{
      margin: 0;
      break-inside: avoid;
      padding-left: 4px;
      line-height: 1.46;
    }}

    li + li {{
      margin-top: 8px;
    }}

    li > p {{
      margin: 0;
    }}

    li > ul,
    li > ol {{
      margin-top: 6px;
      margin-bottom: 0;
    }}

    .insight-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
      margin-top: 2px;
    }}

    .insight-card {{
      position: relative;
      padding: 13px 15px 12px 18px;
      border-radius: 14px;
      border: 1px solid rgba(191, 219, 254, 0.98);
      border-left: 5px solid #2563eb;
      background: linear-gradient(180deg, rgba(255,255,255,1), rgba(246, 250, 255, 0.98));
      box-shadow: 0 10px 22px rgba(15, 23, 42, 0.05);
      break-inside: avoid;
      page-break-inside: avoid;
    }}

    .section-weaknesses .insight-card {{
      border-color: rgba(219, 234, 254, 0.98);
      border-left-color: #1d4ed8;
      background: linear-gradient(180deg, rgba(255,255,255,1), rgba(244, 248, 255, 0.98));
    }}

    .insight-card-title {{
      margin: 0 0 4px;
      font-size: 10.7pt;
      font-weight: 700;
      color: #10233a;
      line-height: 1.42;
    }}

    .insight-card-body {{
      margin: 0;
      font-size: 10.4pt;
      color: #243240;
      line-height: 1.58;
    }}

    .insight-card ul,
    .insight-card ol {{
      margin-top: 8px;
      margin-left: 1.1rem;
      margin-bottom: 0;
      padding-left: 0.1rem;
    }}

    .insight-card ul > li,
    .insight-card ol > li {{
      margin: 0;
      padding-left: 2px;
    }}

    .insight-card ul > li + li,
    .insight-card ol > li + li {{
      margin-top: 5px;
    }}

    .section-top-priority-actions ol {{
      margin-left: 1.4rem;
    }}

    .action-list {{
      display: grid;
      gap: 14px;
      margin-top: 4px;
    }}

    .action-item {{
      display: grid;
      grid-template-columns: 28px 1fr;
      gap: 10px;
      align-items: start;
      break-inside: avoid;
      page-break-inside: avoid;
    }}

    .action-number {{
      font-weight: 700;
      color: #1d4ed8;
      line-height: 1.45;
      padding-top: 1px;
    }}

    .action-content {{
      min-width: 0;
    }}

    .action-title {{
      margin: 0;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.46;
    }}

    .action-body {{
      margin: 5px 0 0;
      line-height: 1.5;
      color: #243240;
    }}

    .action-content > ul,
    .action-content > ol {{
      margin-top: 6px;
      margin-bottom: 0;
      margin-left: 1.1rem;
    }}

    .action-content > ul > li,
    .action-content > ol > li {{
      margin: 0;
      line-height: 1.46;
      padding-left: 2px;
    }}

    .action-content > ul > li + li,
    .action-content > ol > li + li {{
      margin-top: 5px;
    }}

    .finding-list {{
      display: grid;
      gap: 10px;
      margin-top: 4px;
    }}

    .finding-item {{
      display: grid;
      grid-template-columns: 12px 1fr;
      gap: 8px;
      align-items: start;
      break-inside: avoid;
      page-break-inside: avoid;
    }}

    .finding-marker {{
      width: 6px;
      height: 6px;
      border-radius: 999px;
      background: #1d4ed8;
      margin-top: 0.48rem;
      margin-left: 1px;
    }}

    .finding-content {{
      min-width: 0;
    }}

    .finding-body {{
      margin: 0;
      line-height: 1.5;
    }}

    .finding-body + .finding-body {{
      margin-top: 4px;
    }}

    .finding-content > ul,
    .finding-content > ol {{
      margin-top: 6px;
      margin-bottom: 0;
      margin-left: 1.1rem;
    }}

    ul li::marker {{
      color: var(--accent-strong);
      font-size: 0.95em;
    }}

    ol li::marker {{
      color: #1d4ed8;
      font-weight: 700;
    }}

    strong {{
      color: #0f172a;
    }}

    section > p:first-of-type {{
      font-size: 11.15pt;
      color: #203046;
    }}

    code {{
      font-family: "Cascadia Code", Consolas, monospace;
      font-size: 0.94em;
      background: var(--code);
      border: 1px solid #e3e8ef;
      border-radius: 4px;
      padding: 0.08rem 0.32rem;
    }}

    pre {{
      background: var(--code);
      border: 1px solid #e3e8ef;
      border-radius: 10px;
      padding: 12px 14px;
      overflow: hidden;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "Cascadia Code", Consolas, monospace;
      font-size: 9.5pt;
      line-height: 1.5;
      margin: 0 0 12px;
    }}

    hr {{
      border: 0;
      border-top: 1px solid var(--line);
      margin: 16px 0;
    }}

    blockquote {{
      margin: 0 0 12px;
      padding: 6px 0 6px 14px;
      border-left: 3px solid #bfdbfe;
      color: var(--muted);
      background: #f8fbff;
      border-radius: 0 10px 10px 0;
    }}

    a {{
      color: #1d4ed8;
      text-decoration: none;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 0 0 12px;
      font-size: 10pt;
    }}

    th, td {{
      border: 1px solid var(--line);
      padding: 7px 8px;
      text-align: left;
      vertical-align: top;
    }}

    th {{
      background: #f8fafc;
      font-weight: 700;
    }}

    .inline-callout {{
      display: flex;
      align-items: baseline;
      gap: 8px;
      margin: 0 0 10px;
      padding: 10px 12px;
      border-radius: 10px;
      background: linear-gradient(90deg, var(--accent-soft), rgba(232, 241, 255, 0.24));
      border: 1px solid rgba(37, 99, 235, 0.16);
      break-inside: avoid;
    }}

    .inline-callout-label {{
      min-width: 118px;
      font-size: 8.4pt;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--accent-strong);
    }}

    .inline-callout-body {{
      flex: 1;
      font-size: 10.35pt;
      color: var(--ink);
    }}
  </style>
</head>
<body>
  <main class="report-shell">
    {body}
  </main>
</body>
</html>
""".format(body=normalized_body)


def _build_report_html(text):
    return _wrap_report_html(_MARKDOWN.render(text or ""))


def _inline_to_markup(inline_node):
    parts = []
    for child in inline_node.children or []:
        if child.type == "text":
            parts.append(_paragraph_text(child.content))
        elif child.type == "softbreak":
            parts.append(" ")
        elif child.type == "hardbreak":
            parts.append("<br/><br/>")
        elif child.type == "strong":
            parts.append("<b>{text}</b>".format(text=_inline_to_markup(child)))
        elif child.type == "em":
            parts.append("<i>{text}</i>".format(text=_inline_to_markup(child)))
        elif child.type == "code_inline":
            parts.append(
                '<font face="Courier">{text}</font>'.format(
                    text=_paragraph_text(child.content)
                )
            )
        elif child.type == "link":
            href = _paragraph_text((child.attrs or {}).get("href", ""))
            label = _inline_to_markup(child)
            if href:
                parts.append('<link href="{href}">{label}</link>'.format(href=href, label=label))
            else:
                parts.append(label)
        elif child.type == "image":
            alt_text = ""
            if child.children:
                alt_text = _inline_to_markup(child)
            parts.append("[Image: {text}]".format(text=alt_text or "unnamed"))
        else:
            parts.append(_paragraph_text(child.content))
    return "".join(parts)


def _flatten_list_items(list_node, level=0):
    items = []
    for item_index, item_node in enumerate(list_node.children or [], start=1):
        bullet = "{index}.".format(index=item_index) if list_node.type == "ordered_list" else (
            "•" if level == 0 else "–"
        )
        first_paragraph_rendered = False

        for child in item_node.children or []:
            if child.type == "paragraph":
                items.append(
                    {
                        "kind": "list_paragraph",
                        "level": level,
                        "bullet": bullet if not first_paragraph_rendered else "",
                        "text": _inline_to_markup(child.children[0]) if child.children else "",
                        "continued": first_paragraph_rendered,
                    }
                )
                first_paragraph_rendered = True
            elif child.type in {"bullet_list", "ordered_list"}:
                items.extend(_flatten_list_items(child, level=level + 1))
            elif child.type == "code_block":
                items.append(
                    {
                        "kind": "code_block",
                        "level": level + 1,
                        "text": child.content.rstrip(),
                    }
                )
            elif child.type == "fence":
                items.append(
                    {
                        "kind": "code_block",
                        "level": level + 1,
                        "text": child.content.rstrip(),
                    }
                )

    return items


def _parse_markdown_blocks(text):
    root = SyntaxTreeNode(_MARKDOWN.parse(text or ""))
    blocks = []

    for node in root.children or []:
        if node.type == "heading":
            level = int(node.tag[1]) if node.tag.startswith("h") else 2
            title = _inline_to_markup(node.children[0]) if node.children else ""
            block_type = "title" if level == 1 else "heading" if level == 2 else "subheading"
            blocks.append((block_type, title))
            continue

        if node.type == "paragraph":
            content = _inline_to_markup(node.children[0]) if node.children else ""
            blocks.append(("paragraph", content))
            continue

        if node.type in {"bullet_list", "ordered_list"}:
            blocks.append(("list", _flatten_list_items(node)))
            continue

        if node.type in {"code_block", "fence"}:
            blocks.append(("code_block", node.content.rstrip()))
            continue

        if node.type == "hr":
            blocks.append(("rule", ""))

    return blocks


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_LEFT,
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=21,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=12,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=17,
            textColor=colors.HexColor("#1d4ed8"),
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCopy",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15.5,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ListCopy",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.25,
            leading=15,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8.8,
            leading=11,
            textColor=colors.HexColor("#1f2937"),
            backColor=colors.HexColor("#f8fafc"),
            borderColor=colors.HexColor("#d6dde6"),
            borderWidth=0.6,
            borderPadding=8,
            leftIndent=10,
            rightIndent=10,
            spaceBefore=3,
            spaceAfter=8,
        )
    )
    return styles


def _list_paragraph_style(base_style, level, continued=False):
    text_indent = 22 + (level * 16)
    return ParagraphStyle(
        name="ListLevel{level}{continued}".format(
            level=level,
            continued="Continued" if continued else "Lead",
        ),
        parent=base_style,
        leftIndent=text_indent,
        bulletIndent=text_indent - 12,
        firstLineIndent=0,
        spaceBefore=0 if continued else 1,
    )


def _render_page(canvas, doc):
    canvas.saveState()
    width, height = letter

    canvas.setStrokeColor(colors.HexColor("#1d4ed8"))
    canvas.setLineWidth(2)
    canvas.line(doc.leftMargin, height - 28, width - doc.rightMargin, height - 28)

    canvas.setStrokeColor(colors.HexColor("#bfdbfe"))
    canvas.setLineWidth(1)
    canvas.line(doc.leftMargin, 30, width - doc.rightMargin, 30)

    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(doc.leftMargin, 18, "GitHub Portfolio Reviewer Agent")
    canvas.drawRightString(
        width - doc.rightMargin,
        18,
        "Page {page}".format(page=canvas.getPageNumber()),
    )
    canvas.restoreState()


def _generate_pdf_with_reportlab(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=44,
        leftMargin=44,
        topMargin=48,
        bottomMargin=42,
        title="GitHub Portfolio Review",
    )

    styles = _build_styles()
    flowables = []
    blocks = _parse_markdown_blocks(text)

    for index, (block_type, value) in enumerate(blocks):
        if block_type == "title":
            flowables.append(Paragraph(value, styles["ReportTitle"]))
            flowables.append(
                HRFlowable(
                    width="100%",
                    thickness=1.2,
                    color=colors.HexColor("#cbd5e1"),
                    spaceBefore=0,
                    spaceAfter=10,
                )
            )
            continue

        if block_type == "heading":
            flowables.append(Paragraph(value, styles["SectionHeading"]))
            continue

        if block_type == "subheading":
            flowables.append(Paragraph(value, styles["SubHeading"]))
            continue

        if block_type == "paragraph":
            flowables.append(Paragraph(value, styles["BodyCopy"]))
            continue

        if block_type == "list":
            for item in value:
                if item["kind"] == "list_paragraph":
                    style = _list_paragraph_style(
                        styles["ListCopy"],
                        item["level"],
                        continued=item["continued"],
                    )
                    if item["bullet"]:
                        flowables.append(
                            Paragraph(
                                item["text"],
                                style,
                                bulletText=item["bullet"],
                            )
                        )
                    else:
                        flowables.append(Paragraph(item["text"], style))
                elif item["kind"] == "code_block":
                    code_style = ParagraphStyle(
                        name="NestedCodeLevel{level}".format(level=item["level"]),
                        parent=styles["CodeBlock"],
                        leftIndent=22 + (item["level"] * 16),
                        rightIndent=10,
                    )
                    flowables.append(Preformatted(item["text"], code_style))
            flowables.append(Spacer(1, 6))
            continue

        if block_type == "code_block":
            flowables.append(Preformatted(value, styles["CodeBlock"]))
            continue

        if block_type == "rule" and index != len(blocks) - 1:
            flowables.append(
                HRFlowable(
                    width="100%",
                    thickness=0.8,
                    color=colors.HexColor("#d6dde6"),
                    spaceBefore=2,
                    spaceAfter=8,
                )
            )

    doc.build(flowables, onFirstPage=_render_page, onLaterPages=_render_page)
    buffer.seek(0)
    return buffer


def _generate_pdf_with_playwright(text):
    from playwright.sync_api import sync_playwright

    html_document = _build_report_html(text)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html_document, wait_until="load")
            page.emulate_media(media="screen")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template="<div></div>",
                footer_template="""
                    <div style="width:100%;font-size:8px;padding:6px 14px 0;color:#64748b;
                                border-top:1px solid #bfdbfe;
                                display:flex;justify-content:space-between;align-items:center;">
                      <span>GitHub Portfolio Reviewer Agent</span>
                      <span class="pageNumber"></span>
                    </div>
                """,
                margin={
                    "top": "20mm",
                    "right": "14mm",
                    "bottom": "18mm",
                    "left": "14mm",
                },
            )
        finally:
            browser.close()

    return BytesIO(pdf_bytes)


def generate_pdf(text):
    try:
        return _generate_pdf_with_playwright(text)
    except Exception:
        try:
            return _generate_pdf_with_reportlab(text)
        except Exception as error:
            raise ExportError(
                "PDF export failed. Try downloading the Markdown report instead.",
                detail=str(error),
            ) from error


def generate_markdown(text):
    try:
        return BytesIO((text or "").encode("utf-8"))
    except Exception as error:
        raise ExportError(
            "Markdown export failed. Please try again.",
            detail=str(error),
        ) from error
