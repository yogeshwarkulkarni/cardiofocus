"""
Configuration for CardioFocus automation.
Uses environment variables for sensitive data; falls back to .env file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root if present
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

# Portal
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "https://portal.cardiofocus.com")
API_BASE_URL = os.getenv("API_BASE_URL", "https://portal.cardiofocus.com")

# Credentials (must be set via env or .env - never commit real values)
PORTAL_USERNAME = os.getenv("PORTAL_USERNAME", "")
PORTAL_PASSWORD = os.getenv("PORTAL_PASSWORD", "")

# API auth: support token or basic auth
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "")
API_BASIC_USER = os.getenv("API_BASIC_USER", "")
API_BASIC_PASSWORD = os.getenv("API_BASIC_PASSWORD", "")

# Test data
DEFAULT_DEVICE_ID = os.getenv("TEST_DEVICE_ID", "DEV-001")
EXPECTED_DEVICE_STATUS = os.getenv("EXPECTED_DEVICE_STATUS", "Active")

# Selenium
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() in ("1", "true", "yes")
IMPLICIT_WAIT_SECONDS = int(os.getenv("IMPLICIT_WAIT_SECONDS", "10"))
EXPLICIT_WAIT_TIMEOUT_SECONDS = int(os.getenv("EXPLICIT_WAIT_TIMEOUT_SECONDS", "15"))

# Optional: Email notification
REPORT_EMAIL_ENABLED = os.getenv("REPORT_EMAIL_ENABLED", "false").lower() in ("1", "true", "yes")
REPORT_EMAIL_TO = os.getenv("REPORT_EMAIL_TO", "")
REPORT_EMAIL_FROM = os.getenv("REPORT_EMAIL_FROM", "")
REPORT_EMAIL_SMTP_HOST = os.getenv("REPORT_EMAIL_SMTP_HOST", "localhost")
REPORT_EMAIL_SMTP_PORT = int(os.getenv("REPORT_EMAIL_SMTP_PORT", "587"))
