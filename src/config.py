import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
OPENAI_KEY_PATH = BASE_DIR / "openai_key.txt"
GITHUB_TOKEN_PATH = BASE_DIR / "github_token.txt"

OPENAI_REPO_MODEL = os.getenv("OPENAI_REPO_MODEL", "gpt-5-mini")
OPENAI_PORTFOLIO_MODEL = os.getenv("OPENAI_PORTFOLIO_MODEL", "gpt-5.4")
OPENAI_FINAL_REPORT_MODEL = os.getenv("OPENAI_FINAL_REPORT_MODEL", "gpt-5.4")

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_PAGE_SIZE = 100
REQUEST_TIMEOUT_SECONDS = 30
REPO_ANALYSIS_MAX_WORKERS = 4


def _load_key_from_file(path):
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return None


def load_openai_key():
    key = os.getenv("OPENAI_API_KEY") or _load_key_from_file(OPENAI_KEY_PATH)
    if key:
        return key
    raise Exception("Missing OpenAI API key. Set OPENAI_API_KEY or add openai_key.txt.")


def load_github_token(required=False):
    token = os.getenv("GITHUB_TOKEN") or _load_key_from_file(GITHUB_TOKEN_PATH)
    if token or not required:
        return token
    raise Exception("Missing GitHub token. Set GITHUB_TOKEN or add github_token.txt.")
