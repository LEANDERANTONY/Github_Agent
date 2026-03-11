import base64
import hashlib
import hmac
import secrets
import time

import requests

from src.config import (
    GITHUB_API_BASE_URL,
    REQUEST_TIMEOUT_SECONDS,
    load_github_oauth_client_id,
    load_github_oauth_client_secret,
    load_github_oauth_redirect_uri,
    load_github_oauth_scope,
)
from src.errors import GithubOAuthError


GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
OAUTH_STATE_TTL_SECONDS = 600
_OAUTH_STATE_REGISTRY = {}


def _urlsafe_b64encode(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _sign_oauth_state(payload):
    client_secret = load_github_oauth_client_secret(required=True).encode("utf-8")
    signature = hmac.new(client_secret, payload.encode("utf-8"), hashlib.sha256).digest()
    return _urlsafe_b64encode(signature)


def _validate_signed_oauth_state(state, now=None):
    try:
        nonce, issued_at, provided_signature = state.split(".", 2)
        issued_at_value = int(issued_at)
    except (AttributeError, ValueError):
        return False

    current_time = int(now or time.time())
    if current_time - issued_at_value > OAUTH_STATE_TTL_SECONDS:
        return False

    payload = "{nonce}.{issued_at}".format(nonce=nonce, issued_at=issued_at)
    expected_signature = _sign_oauth_state(payload)
    return hmac.compare_digest(provided_signature, expected_signature)


def oauth_is_configured():
    return bool(
        load_github_oauth_client_id(required=False)
        and load_github_oauth_client_secret(required=False)
        and load_github_oauth_redirect_uri(required=False)
    )


def generate_oauth_state():
    nonce = secrets.token_urlsafe(24)
    issued_at = str(int(time.time()))
    payload = "{nonce}.{issued_at}".format(nonce=nonce, issued_at=issued_at)
    signature = _sign_oauth_state(payload)
    return "{payload}.{signature}".format(payload=payload, signature=signature)


def _purge_expired_oauth_states(now=None, registry=None):
    registry = _OAUTH_STATE_REGISTRY if registry is None else registry
    now = now or time.time()
    expired_states = [
        state
        for state, created_at in registry.items()
        if now - created_at > OAUTH_STATE_TTL_SECONDS
    ]
    for state in expired_states:
        registry.pop(state, None)


def register_oauth_state(state, registry=None):
    registry = _OAUTH_STATE_REGISTRY if registry is None else registry
    _purge_expired_oauth_states(registry=registry)
    registry[state] = time.time()


def consume_oauth_state(state, registry=None):
    registry = _OAUTH_STATE_REGISTRY if registry is None else registry
    _purge_expired_oauth_states(registry=registry)
    created_at = registry.pop(state, None)
    if created_at is not None:
        return True
    return _validate_signed_oauth_state(state)


def build_authorize_url(state):
    params = {
        "client_id": load_github_oauth_client_id(required=True),
        "redirect_uri": load_github_oauth_redirect_uri(required=True),
        "scope": load_github_oauth_scope(),
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

    try:
        response = requests.post(
            GITHUB_OAUTH_ACCESS_TOKEN_URL,
            headers={"Accept": "application/json"},
            data=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.Timeout as error:
        raise GithubOAuthError(
            "GitHub sign-in timed out during token exchange. Please try again.",
            detail=str(error),
        ) from error
    except requests.RequestException as error:
        raise GithubOAuthError(
            "GitHub sign-in failed during token exchange. Please try again.",
            detail=str(error),
        ) from error
    token_payload = response.json()

    if token_payload.get("error"):
        raise GithubOAuthError(
            "GitHub OAuth exchange failed: {error}".format(
                error=token_payload.get("error_description") or token_payload["error"]
            )
        )

    access_token = token_payload.get("access_token")
    if not access_token:
        raise GithubOAuthError("GitHub OAuth exchange returned no access token.")

    return access_token


def get_authenticated_user(github_token):
    try:
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
    except requests.Timeout as error:
        raise GithubOAuthError(
            "GitHub sign-in timed out while loading your account. Please try again.",
            detail=str(error),
        ) from error
    except requests.RequestException as error:
        raise GithubOAuthError(
            "GitHub sign-in succeeded, but loading your account failed. Please try again.",
            detail=str(error),
        ) from error
    return response.json()
