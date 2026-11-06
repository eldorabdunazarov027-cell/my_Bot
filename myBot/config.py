import os
from pathlib import Path
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Admin credentials & security
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Parol_2012").strip()
MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "5"))

# Timezone settings (O‘zbekiston vaqti)
TIMEZONE_STR = os.getenv("TIMEZONE", "Asia/Tashkent")
try:
    TIMEZONE = pytz.timezone(TIMEZONE_STR)
except Exception:
    TIMEZONE = pytz.timezone("Asia/Tashkent")

# Database configuration
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "tasks.db"

