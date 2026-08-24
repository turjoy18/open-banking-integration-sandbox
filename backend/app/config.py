import os
from pathlib import Path

from dotenv import load_dotenv

# Load repo-root .env (one level above backend/)
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)

OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "sandbox-tpp")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "sandbox-tpp-secret-change-me")
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI",
    "http://127.0.0.1:5173/callback",
)
OAUTH_CLIENT_NAME = os.getenv("OAUTH_CLIENT_NAME", "Sandbox TPP")
