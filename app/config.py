import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
INDEX_DIR = BASE_DIR / "knowledge_base_index"
EXPORTS_DIR = BASE_DIR / "exports"
SETTINGS_FILE = BASE_DIR / "settings.json"

INDEX_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_api_key(env_var_name: str) -> str | None:
    val = os.environ.get(env_var_name, "").strip()
    return val if val else None
