import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
OPENAI_KEY_PATH = BASE_DIR / "openai_key.txt"
GITHUB_OAUTH_CLIENT_ID_PATH = BASE_DIR / "github_oauth_client_id.txt"
GITHUB_OAUTH_CLIENT_SECRET_PATH = BASE_DIR / "github_oauth_client_secret.txt"
GITHUB_OAUTH_REDIRECT_URI_PATH = BASE_DIR / "github_oauth_redirect_uri.txt"
ANALYSIS_CACHE_DB_PATH = BASE_DIR / "analysis_cache.sqlite3"

OPENAI_REPO_MODEL = os.getenv("OPENAI_REPO_MODEL", "gpt-5-mini")
OPENAI_PORTFOLIO_MODEL = os.getenv("OPENAI_PORTFOLIO_MODEL", "gpt-5.4")
OPENAI_FINAL_REPORT_MODEL = os.getenv("OPENAI_FINAL_REPORT_MODEL", "gpt-5.4")
GITHUB_OAUTH_SCOPE = os.getenv("GITHUB_OAUTH_SCOPE", "read:user user:email")
ANALYSIS_CACHE_VERSION = "2026-03-11-v2"

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_PAGE_SIZE = 100
REQUEST_TIMEOUT_SECONDS = 30
REPO_ANALYSIS_MAX_WORKERS = 4
GITHUB_FETCH_MAX_WORKERS = 3
GITHUB_RETRY_ATTEMPTS = 2


def _load_key_from_file(path):
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return None


def load_openai_key():
    key = os.getenv("OPENAI_API_KEY") or _load_key_from_file(OPENAI_KEY_PATH)
    if key:
        return key
    raise Exception("Missing OpenAI API key. Set OPENAI_API_KEY or add openai_key.txt.")


def load_github_oauth_client_id(required=False):
    client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID") or _load_key_from_file(
        GITHUB_OAUTH_CLIENT_ID_PATH
    )
    if client_id or not required:
        return client_id
    raise Exception(
        "Missing GitHub OAuth client ID. Set GITHUB_OAUTH_CLIENT_ID or add github_oauth_client_id.txt."
    )


def load_github_oauth_client_secret(required=False):
    client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET") or _load_key_from_file(
        GITHUB_OAUTH_CLIENT_SECRET_PATH
    )
    if client_secret or not required:
        return client_secret
    raise Exception(
        "Missing GitHub OAuth client secret. Set GITHUB_OAUTH_CLIENT_SECRET or add github_oauth_client_secret.txt."
    )


def load_github_oauth_redirect_uri(required=False):
    redirect_uri = os.getenv("GITHUB_OAUTH_REDIRECT_URI") or _load_key_from_file(
        GITHUB_OAUTH_REDIRECT_URI_PATH
    )
    if redirect_uri or not required:
        return redirect_uri
    raise Exception(
        "Missing GitHub OAuth redirect URI. Set GITHUB_OAUTH_REDIRECT_URI or add github_oauth_redirect_uri.txt."
    )
