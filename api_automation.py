"""
API Automation for CardioFocus Device Portal.
Authenticates with the REST API, retrieves device details by ID,
and verifies the status field. Handles and reports API errors.
"""

import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests

import config
from reporter import TestRunReport, format_console_report, write_report_file
from pathlib import Path


def _run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def get_api_session(
    base_url: str,
    token: Optional[str] = None,
    basic_user: Optional[str] = None,
    basic_password: Optional[str] = None,
) -> requests.Session:
    """
    Create a requests Session with authentication.
    Uses Bearer token if API_AUTH_TOKEN is set; otherwise Basic auth if credentials provided.
    """
    session = requests.Session()
    base = base_url.rstrip("/")
    session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    elif basic_user and basic_password:
        session.auth = (basic_user, basic_password)
    return session


def fetch_device(
    session: requests.Session,
    base_url: str,
    device_id: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
    """
    GET /api/devices/{device_id}. Returns (json_data, error_message, status_code).
    """
    url = f"{base_url.rstrip('/')}/api/devices/{device_id}"
    try:
        resp = session.get(url, timeout=30)
        try:
            data = resp.json() if resp.content else None
        except ValueError:
            data = None
        if not resp.ok:
            err = data.get("message", data.get("error", resp.text)) if isinstance(data, dict) else resp.text
            return None, err or f"HTTP {resp.status_code}", resp.status_code
        return data, None, resp.status_code
    except requests.exceptions.Timeout:
        return None, "Request timed out", 0
    except requests.exceptions.ConnectionError as e:
        return None, f"Connection error: {e}", 0
    except requests.exceptions.RequestException as e:
        return None, str(e), 0


def run_api_tests(
    base_url: str = None,
    device_id: str = None,
    expected_status: str = None,
    token: str = None,
    basic_user: str = None,
    basic_password: str = None,
    output_dir: Optional[Path] = None,
) -> Tuple[TestRunReport, bool]:
    """
    Execute API test flow. Returns (report, success).
    """
    base_url = base_url or config.API_BASE_URL
    device_id = device_id or config.DEFAULT_DEVICE_ID
    expected_status = expected_status or config.EXPECTED_DEVICE_STATUS
    token = token or config.API_AUTH_TOKEN
    basic_user = basic_user or config.API_BASIC_USER
    basic_password = basic_password or config.API_BASIC_PASSWORD

    report = TestRunReport(
        run_id=_run_id(),
        started_at=datetime.utcnow().isoformat() + "Z",
        test_name="API Automation",
    )

    # Step 1: Authentication setup (optional for local mock; required for real portal)
    session = get_api_session(base_url, token=token, basic_user=basic_user, basic_password=basic_password)
    if token or (basic_user and basic_password):
        report.add_step("API authentication", True, "Session created with configured auth")
    else:
        report.add_step("API authentication", True, "No auth configured – proceeding without authentication (e.g. local mock)")

    # Step 2: Retrieve device details
    data, err, status_code = fetch_device(session, base_url, device_id)
    if err is not None:
        report.add_step(
            "Retrieve device details",
            False,
            f"API request failed: {err}",
            details=f"HTTP {status_code}" if status_code else None,
        )
        report.set_finished(False, err)
        return report, False

    api_url = f"{base_url.rstrip('/')}/api/devices/{device_id}"
    response_details = json.dumps(data, indent=2) if isinstance(data, dict) else str(data)[:500]
    report.add_step(
        "Retrieve device details",
        True,
        f"API URL: {api_url} | GET returned 200",
        details=response_details,
    )

    # Step 3: Verify status field
    if not isinstance(data, dict):
        report.add_step("Verify device status (API)", False, "Response body is not a JSON object", details=str(data)[:200])
        report.set_finished(False, "Invalid response shape")
        return report, False

    actual_status = data.get("status")
    if actual_status is None:
        report.add_step(
            "Verify device status (API)",
            False,
            "Response has no 'status' field",
            details=f"Keys: {list(data.keys())}",
        )
        report.set_finished(False, "Missing status field")
        return report, False

    if str(actual_status) != str(expected_status):
        report.add_step(
            "Verify device status (API)",
            False,
            f"Status mismatch: expected '{expected_status}', got '{actual_status}'",
            details=str(actual_status),
        )
        report.set_finished(False, "Status mismatch")
        return report, False

    report.add_step(
        "Verify device status (API)",
        True,
        f"Status '{actual_status}' matches expected '{expected_status}'",
    )
    report.set_finished(True, None)
    return report, True


def main() -> int:
    """Entry point for standalone API test run."""
    report, success = run_api_tests(output_dir=Path(__file__).resolve().parent / "reports")
    print(format_console_report(report))
    report_path = write_report_file(report, output_dir=Path(__file__).resolve().parent / "reports")
    print(f"Report written to: {report_path}")

    if config.REPORT_EMAIL_ENABLED and config.REPORT_EMAIL_TO and config.REPORT_EMAIL_FROM:
        from reporter import send_report_email
        if send_report_email(
            report,
            config.REPORT_EMAIL_TO,
            config.REPORT_EMAIL_FROM,
            config.REPORT_EMAIL_SMTP_HOST,
            config.REPORT_EMAIL_SMTP_PORT,
        ):
            print("Report email sent.")
        else:
            print("Report email failed to send.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
