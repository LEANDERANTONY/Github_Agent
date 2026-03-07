import json

from openai import OpenAI

from src.config import (
    OPENAI_FINAL_REPORT_MODEL,
    OPENAI_PORTFOLIO_MODEL,
    OPENAI_REPO_MODEL,
    load_openai_key,
)
from src.prompts import (
    build_final_report_prompt,
    build_portfolio_summary_prompt,
    build_repo_audit_prompt,
)
from src.schemas import PortfolioSummary, RepoAudit


def _extract_json_payload(content):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            raise
        return json.loads(content[start : end + 1])


def _normalize_text(value):
    if isinstance(value, list):
        return " ".join(str(item).strip() for item in value if str(item).strip()).strip()
    if value is None:
        return ""
    return str(value).strip()


def _normalize_list(value):
    def _normalize_item(item):
        if isinstance(item, dict):
            for key in ("action", "name", "title", "summary"):
                text = item.get(key)
                if text:
                    return str(text).strip()
            return json.dumps(item, ensure_ascii=True)
        return str(item).strip()

    if isinstance(value, list):
        normalized_items = []
        for item in value:
            text = _normalize_item(item)
            if text:
                normalized_items.append(text)
        return normalized_items
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _create_client():
    return OpenAI(api_key=load_openai_key())


def _request_json(client, prompt, model):
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful technical reviewer."},
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return _extract_json_payload(content)


def analyze_repo(repo_facts, repo_check, model=OPENAI_REPO_MODEL):
    client = _create_client()
    payload = _request_json(
        client=client,
        prompt=build_repo_audit_prompt(repo_facts, repo_check),
        model=model,
    )

    return RepoAudit(
        repo_name=repo_facts.name,
        summary=_normalize_text(payload.get("summary", "")),
        what_it_does=_normalize_text(payload.get("what_it_does", "")),
        key_technologies=_normalize_list(payload.get("key_technologies", [])),
        strengths=_normalize_list(payload.get("strengths", [])),
        weaknesses=_normalize_list(payload.get("weaknesses", [])),
        recommendations=_normalize_list(payload.get("recommendations", [])),
        showcase_value=_normalize_text(payload.get("showcase_value", "")),
        recruiter_signal=_normalize_text(payload.get("recruiter_signal", "")),
    )


def summarize_portfolio(repo_audits, repo_checks, model=OPENAI_PORTFOLIO_MODEL):
    if not repo_audits:
        raise Exception("No repository audits available for portfolio summary.")

    client = _create_client()
    payload = _request_json(
        client=client,
        prompt=build_portfolio_summary_prompt(repo_audits, repo_checks),
        model=model,
    )

    return PortfolioSummary(
        summary=_normalize_text(payload.get("summary", "")),
        strongest_repos=_normalize_list(payload.get("strongest_repos", [])),
        improvement_areas=_normalize_list(payload.get("improvement_areas", [])),
        top_actions=_normalize_list(payload.get("top_actions", [])),
    )


def polish_portfolio_report(report, model=OPENAI_FINAL_REPORT_MODEL):
    client = _create_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful technical reviewer."},
            {"role": "user", "content": build_final_report_prompt(report)},
        ],
    )
    content = response.choices[0].message.content or ""
    polished_report = content.strip()
    if not polished_report:
        raise RuntimeError("OpenAI returned an empty final report.")
    return polished_report
