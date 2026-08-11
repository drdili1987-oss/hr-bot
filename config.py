import os
import sys

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

_admin_id_raw = os.getenv("ADMIN_ID")
try:
    ADMIN_ID = int(_admin_id_raw) if _admin_id_raw else None
except ValueError:
    ADMIN_ID = None

_hr_group_raw = os.getenv("HR_GROUP_ID")
try:
    HR_GROUP_ID = int(_hr_group_raw) if _hr_group_raw else None
except ValueError:
    HR_GROUP_ID = None

if not BOT_TOKEN:
    sys.exit("BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")

if HR_GROUP_ID is None:
    sys.exit("HR_GROUP_ID is not set or invalid. Copy .env.example to .env and fill it in.")

# Allowed resume file extensions/mime types
ALLOWED_RESUME_EXTENSIONS = (".pdf", ".doc", ".docx")
ALLOWED_RESUME_MIME_TYPES = (
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)
MAX_RESUME_SIZE_MB = 20
