import base64

import requests

from src.config import (
    GITHUB_API_BASE_URL,
    GITHUB_PAGE_SIZE,
    REQUEST_TIMEOUT_SECONDS,
    load_github_token,
)
from src.schemas import RepoFacts


def _base_headers():
    return {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

 
def _get_header_candidates(require_auth=False):
    anonymous_headers = _base_headers()
    token = load_github_token(required=False)

    if token:
        authenticated_headers = _base_headers()
        authenticated_headers["Authorization"] = f"token {token}"
        if require_auth:
            return [authenticated_headers]
        return [authenticated_headers, anonymous_headers]

    if require_auth:
        load_github_token(required=True)

    return [anonymous_headers]


def _request(url, header_candidates, params=None):
    last_response = None

    for headers in header_candidates:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            return response

        last_response = response
        if response.status_code != 401:
            break

    raise Exception(
        f"GitHub API error {last_response.status_code}: {last_response.text}"
    )


def _request_json(url, header_candidates, params=None):
    return _request(url, header_candidates=header_candidates, params=params).json()


def _get_repo_languages(owner_login, repo_name, header_candidates):
    url = f"{GITHUB_API_BASE_URL}/repos/{owner_login}/{repo_name}/languages"
    return _request_json(url, header_candidates=header_candidates)


def _get_repo_readme(owner_login, repo_name, header_candidates):
    url = f"{GITHUB_API_BASE_URL}/repos/{owner_login}/{repo_name}/readme"
    try:
        response = _request(url, header_candidates=header_candidates)
    except Exception as error:
        if "GitHub API error 404" in str(error):
            return False, ""
        raise

    payload = response.json()
    content = payload.get("content") or ""
    encoding = payload.get("encoding")

    if encoding == "base64" and content:
        decoded = base64.b64decode(content).decode("utf-8", errors="replace")
        return True, decoded

    return False, ""


def _get_repo_root_entries(owner_login, repo_name, header_candidates):
    url = f"{GITHUB_API_BASE_URL}/repos/{owner_login}/{repo_name}/contents"
    try:
        response = _request(url, header_candidates=header_candidates)
    except Exception as error:
        if "GitHub API error 404" in str(error):
            return []
        raise

    payload = response.json()
    if not isinstance(payload, list):
        return []

    return [entry.get("name", "") for entry in payload if entry.get("name")]


def _build_repo_facts(repo, header_candidates):
    owner_login = (repo.get("owner") or {}).get("login", "")
    license_info = repo.get("license") or {}
    languages = _get_repo_languages(owner_login, repo["name"], header_candidates)
    readme_present, readme_text = _get_repo_readme(owner_login, repo["name"], header_candidates)
    root_entries = _get_repo_root_entries(owner_login, repo["name"], header_candidates)

    return RepoFacts(
        name=repo["name"],
        description=repo.get("description") or "No description",
        owner_login=owner_login,
        html_url=repo.get("html_url") or "",
        language=repo.get("language") or "",
        topics=repo.get("topics") or [],
        homepage=repo.get("homepage") or "",
        updated_at=repo.get("updated_at") or "",
        stargazers_count=repo.get("stargazers_count") or 0,
        forks_count=repo.get("forks_count") or 0,
        open_issues_count=repo.get("open_issues_count") or 0,
        license_name=license_info.get("name") or "",
        default_branch=repo.get("default_branch") or "",
        repo_size_kb=repo.get("size") or 0,
        is_fork=bool(repo.get("fork")),
        languages=languages,
        root_entries=root_entries,
        readme_present=readme_present,
        readme_text=readme_text,
    )


def _sort_repos(repos):
    return sorted(
        repos,
        key=lambda repo: repo.get("updated_at") or "",
        reverse=True,
    )


def _filter_repos(repos, selected_repo_names=None, max_repos=None, skip_forks=False):
    filtered_repos = list(repos)

    if selected_repo_names:
        selected_lookup = {name: index for index, name in enumerate(selected_repo_names)}
        filtered_repos = [
            repo for repo in filtered_repos if repo.get("name") in selected_lookup
        ]
        filtered_repos.sort(key=lambda repo: selected_lookup[repo.get("name")])
        return filtered_repos

    if skip_forks:
        filtered_repos = [repo for repo in filtered_repos if not repo.get("fork")]

    filtered_repos = _sort_repos(filtered_repos)

    if max_repos:
        filtered_repos = filtered_repos[:max_repos]

    return filtered_repos


def get_github_repos(username=None):
    params = {"per_page": GITHUB_PAGE_SIZE, "sort": "updated"}

    if username:
        url = f"{GITHUB_API_BASE_URL}/users/{username}/repos"
        header_candidates = _get_header_candidates(require_auth=False)
    else:
        url = f"{GITHUB_API_BASE_URL}/user/repos"
        params["affiliation"] = "owner,collaborator"
        header_candidates = _get_header_candidates(require_auth=True)

    repos = []
    page = 1

    while True:
        batch = _request_json(
            url,
            header_candidates=header_candidates,
            params={**params, "page": page},
        )
        repos.extend(batch)

        if len(batch) < GITHUB_PAGE_SIZE:
            break

        page += 1

    return _sort_repos(repos)


def get_portfolio_repo_facts(
    username=None,
    selected_repo_names=None,
    max_repos=None,
    skip_forks=False,
):
    repos = get_github_repos(username=username)
    repos = _filter_repos(
        repos,
        selected_repo_names=selected_repo_names,
        max_repos=max_repos,
        skip_forks=skip_forks,
    )

    if not repos:
        raise Exception("No repositories matched the selected analysis scope.")

    header_candidates = _get_header_candidates(require_auth=not username)
    repo_facts = []

    for repo in repos:
        repo_facts.append(_build_repo_facts(repo, header_candidates))

    return repo_facts
