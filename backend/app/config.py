from pathlib import Path

from dotenv import load_dotenv

# Load repo-root .env (one level above backend/)
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)
