"""
UI Automation for CardioFocus Device Portal.
Uses Page Object Model (pages/) and Selenium: login -> device list -> search -> verify status.
"""

import sys
import warnings

warnings.filterwarnings("ignore", message=".*OpenSSL 1.1.1.*", category=UserWarning)

from datetime import datetime
from typing import Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

import config
from reporter import TestRunReport, format_console_report, write_report_file
from pages.login_page import LoginPage
from pages.devices_page import DevicesPage


def _run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def run_ui_tests(
    base_url: str = None,
    username: str = None,
    password: str = None,
    device_id: str = None,
    expected_status: str = None,
    headless: bool = None,
    output_dir: Optional[str] = None,
) -> Tuple[TestRunReport, bool]:
    """
    Execute UI test flow using Page Objects. Returns (report, success).
    """
    base_url = base_url or config.PORTAL_BASE_URL
    username = username or config.PORTAL_USERNAME
    password = password or config.PORTAL_PASSWORD
    device_id = device_id or config.DEFAULT_DEVICE_ID
    expected_status = expected_status or config.EXPECTED_DEVICE_STATUS
    headless = headless if headless is not None else config.BROWSER_HEADLESS
    timeout = config.EXPLICIT_WAIT_TIMEOUT_SECONDS

    report = TestRunReport(
        run_id=_run_id(),
        started_at=datetime.utcnow().isoformat() + "Z",
        test_name="UI Automation",
    )
    driver: Optional[webdriver.Chrome] = None

    try:
        # --- Step 1: Navigate to login page ---
        login_url = f"{base_url.rstrip('/')}{LoginPage.URL_PATH}"
        try:
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.implicitly_wait(config.IMPLICIT_WAIT_SECONDS)
            driver.get(login_url)
            report.add_step("Navigate to login page", True, f"Loaded {login_url}")
        except WebDriverException as e:
            report.add_step("Navigate to login page", False, "Browser failed to start or load URL", str(e))
            report.set_finished(False, "Browser/startup error")
            return report, False

        if not username or not password:
            report.add_step(
                "Login credentials",
                False,
                "Username or password not configured (set PORTAL_USERNAME, PORTAL_PASSWORD)",
            )
            report.set_finished(False, "Missing credentials")
            return report, False

        # --- Step 2: Log in (Page Object) ---
        login_page = LoginPage(driver, base_url, timeout)
        user_el, pass_el, submit_el = login_page.get_login_elements()

        if not user_el or not pass_el or not submit_el:
            report.add_step(
                "Login",
                False,
                "Login failed: could not find username, password, or submit elements. Check selectors in pages/login_page.py.",
                f"user_el={user_el is not None}, pass_el={pass_el is not None}, submit_el={submit_el is not None}",
            )
            report.set_finished(False, "Login elements not found")
            return report, False

        login_page.login(username, password)
        login_page.wait_until_left_login()

        if login_page.is_still_on_login_page():
            report.add_step("Login", False, "Login failed: remained on login page (check credentials)")
            report.set_finished(False, "Login failure")
            return report, False

        report.add_step("Login", True, "Submitted credentials and left login page")

        # --- Step 3: Navigate to device management (Page Object) ---
        devices_page = DevicesPage(driver, base_url, timeout)
        devices_page.open()
        report.add_step("Navigate to device management", True, f"Loaded {devices_page.get_url()}")

        # --- Step 4: Search for device (Page Object) ---
        search_el = devices_page.get_search_input()
        if not search_el:
            report.add_step("Search for device", False, "Device search input not found.")
            report.set_finished(False, "Search UI not found")
            return report, False

        devices_page.search_device(device_id)
        report.add_step("Search for device", True, f"Searched for device ID: {device_id}")

        # --- Step 5: Verify device status (Page Object) ---
        try:
            actual_status = devices_page.get_device_status_for(device_id)
            if actual_status is None:
                report.add_step(
                    "Verify device status (UI)",
                    False,
                    f"Device '{device_id}' not found in list or status element not located.",
                )
                report.set_finished(False, "Device not found or status not visible")
                return report, False

            if actual_status != expected_status:
                report.add_step(
                    "Verify device status (UI)",
                    False,
                    f"Status mismatch: expected '{expected_status}', got '{actual_status}'",
                    details=actual_status,
                )
                report.set_finished(False, "Status mismatch")
                return report, False

            report.add_step(
                "Verify device status (UI)",
                True,
                f"Displayed status '{actual_status}' matches expected '{expected_status}'",
            )
        except NoSuchElementException as e:
            report.add_step("Verify device status (UI)", False, "Could not find device or status element", str(e))
            report.set_finished(False, "Element not found")
            return report, False

        report.set_finished(True, None)
        return report, True

    except Exception as e:
        report.add_step("Unexpected error", False, str(type(e).__name__), str(e))
        report.set_finished(False, str(e))
        return report, False

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def main() -> int:
    """Entry point for standalone UI test run."""
    from pathlib import Path
    report, success = run_ui_tests()
    print(format_console_report(report))
    reports_dir = Path(__file__).resolve().parent / "reports"
    report_path = write_report_file(report, output_dir=reports_dir)
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
