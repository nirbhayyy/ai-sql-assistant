import os
from dotenv import load_dotenv

load_dotenv()

DB_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY")

if not DB_ENCRYPTION_KEY:
    raise ValueError("DB_ENCRYPTION_KEY is missing from environment variables")

print("Encryption key loaded:", bool(DB_ENCRYPTION_KEY))