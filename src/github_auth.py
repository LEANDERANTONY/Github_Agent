import secrets
import time

import requests

from src.config import (
    GITHUB_API_BASE_URL,
    GITHUB_OAUTH_SCOPE,
    REQUEST_TIMEOUT_SECONDS,
    load_github_oauth_client_id,
    load_github_oauth_client_secret,
    load_github_oauth_redirect_uri,
)


GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
OAUTH_STATE_TTL_SECONDS = 600
_OAUTH_STATE_REGISTRY = {}


def oauth_is_configured():
    return bool(
        load_github_oauth_client_id(required=False)
        and load_github_oauth_client_secret(required=False)
        and load_github_oauth_redirect_uri(required=False)
    )


def generate_oauth_state():
    return secrets.token_urlsafe(24)


def _purge_expired_oauth_states(now=None):
    now = now or time.time()
    expired_states = [
        state
        for state, created_at in _OAUTH_STATE_REGISTRY.items()
        if now - created_at > OAUTH_STATE_TTL_SECONDS
    ]
    for state in expired_states:
        _OAUTH_STATE_REGISTRY.pop(state, None)


def register_oauth_state(state):
    _purge_expired_oauth_states()
    _OAUTH_STATE_REGISTRY[state] = time.time()


def consume_oauth_state(state):
    _purge_expired_oauth_states()
    created_at = _OAUTH_STATE_REGISTRY.pop(state, None)
    return created_at is not None


def build_authorize_url(state):
    params = {
        "client_id": load_github_oauth_client_id(required=True),
        "redirect_uri": load_github_oauth_redirect_uri(required=True),
        "scope": GITHUB_OAUTH_SCOPE,
        "state": state,
    }
    return requests.Request("GET", GITHUB_OAUTH_AUTHORIZE_URL, params=params).prepare().url


def exchange_code_for_token(code, state=None):
    payload = {
        "client_id": load_github_oauth_client_id(required=True),
        "client_secret": load_github_oauth_client_secret(required=True),
        "code": code,
        "redirect_uri": load_github_oauth_redirect_uri(required=True),
    }
    if state:
        payload["state"] = state

    response = requests.post(
        GITHUB_OAUTH_ACCESS_TOKEN_URL,
        headers={"Accept": "application/json"},
        data=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    token_payload = response.json()

    if token_payload.get("error"):
        raise RuntimeError(
            "GitHub OAuth exchange failed: {error}".format(
                error=token_payload.get("error_description") or token_payload["error"]
            )
        )

    access_token = token_payload.get("access_token")
    if not access_token:
        raise RuntimeError("GitHub OAuth exchange returned no access token.")

    return access_token


def get_authenticated_user(github_token):
    response = requests.get(
        f"{GITHUB_API_BASE_URL}/user",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {github_token}",
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()
