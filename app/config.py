from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'approveit.db').as_posix()}")
USERS_FILE = Path(os.getenv("USERS_FILE", str(DATA_DIR / "users.json")))
ALLOW_TEST_DATE_OVERRIDE = os.getenv("ALLOW_TEST_DATE_OVERRIDE", "true").lower() == "true"
