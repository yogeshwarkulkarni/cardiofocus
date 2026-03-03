"""
UI Automation for CardioFocus Device Portal.
Uses Selenium to log in, navigate to device management, search for a device,
and verify displayed status. Includes explicit waits and error handling.
"""

import sys
import warnings

# Suppress urllib3/OpenSSL warning on macOS (Python built against LibreSSL)
warnings.filterwarnings("ignore", message=".*OpenSSL 1.1.1.*", category=UserWarning)

from datetime import datetime
from typing import Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

import config
from reporter import StepResult, TestRunReport, format_console_report, write_report_file


# Selectors for the portal (adjust for actual portal DOM - see README)
SELECTORS = {
    "login_url_path": "/login",
    "username_input": "input[name='username'], #username, input[type='email']",
    "password_input": "input[name='password'], #password",
    "login_submit": "button[type='submit'], input[type='submit'], .login-button",
    "device_management_link": "a[href*='device'], a[href*='devices'], nav a:contains('Devices')",
    "device_management_url_path": "/devices",
    "device_search_input": "input[placeholder*='Search'], input[name='search'], #device-search",
    "device_search_button": "button:contains('Search'), .search-btn, button[type='submit']",
    "device_status_cell": "td[data-status], .device-status, .status",
    "device_row": "tr[data-device-id], table tbody tr",
}


def _run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def _find_element(driver: webdriver.Chrome, by: By, value: str, timeout: int) -> Optional[WebElement]:
    """Find element with explicit wait. Returns None on timeout."""
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        return None


def _find_element_css(driver: webdriver.Chrome, css_selector: str, timeout: int) -> Optional[WebElement]:
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
    except TimeoutException:
        return None


def _try_selectors(driver: webdriver.Chrome, selectors: str, timeout: int) -> Optional[WebElement]:
    """Try multiple CSS selectors (comma-separated); return first match."""
    for sel in (s.strip() for s in selectors.split(",")):
        el = _find_element_css(driver, sel, timeout=min(3, timeout))
        if el is not None:
            return el
    return None


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
    Execute UI test flow. Returns (report, success).
    Parameters default to config module values.
    """
    base_url = base_url or config.PORTAL_BASE_URL
    username = username or config.PORTAL_USERNAME
    password = password or config.PORTAL_PASSWORD
    device_id = device_id or config.DEFAULT_DEVICE_ID
    expected_status = expected_status or config.EXPECTED_DEVICE_STATUS
    headless = headless if headless is not None else config.BROWSER_HEADLESS
    timeout = config.EXPLICIT_WAIT_TIMEOUT_SECONDS

    report = TestRunReport(run_id=_run_id(), started_at=datetime.utcnow().isoformat() + "Z", test_name="UI Automation")
    driver: Optional[webdriver.Chrome] = None

    try:
        # Step 1: Navigate to login page
        login_url = f"{base_url.rstrip('/')}{SELECTORS['login_url_path']}"
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
            report.add_step("Login credentials", False, "Username or password not configured (set PORTAL_USERNAME, PORTAL_PASSWORD)")
            report.set_finished(False, "Missing credentials")
            return report, False

        # Step 2: Log in
        user_el = _try_selectors(driver, SELECTORS["username_input"], timeout)
        pass_el = _try_selectors(driver, SELECTORS["password_input"], timeout)
        submit_el = _try_selectors(driver, SELECTORS["login_submit"], timeout)

        if not user_el or not pass_el or not submit_el:
            report.add_step(
                "Login",
                False,
                "Login failed: could not find username, password, or submit elements. Check selectors for this portal.",
                f"user_el={user_el is not None}, pass_el={pass_el is not None}, submit_el={submit_el is not None}",
            )
            report.set_finished(False, "Login elements not found")
            return report, False

        user_el.clear()
        user_el.send_keys(username)
        pass_el.clear()
        pass_el.send_keys(password)
        submit_el.click()

        # Wait for navigation (either to dashboard or error)
        WebDriverWait(driver, timeout).until(
            lambda d: "login" not in d.current_url.lower() or "error" in d.page_source.lower()
        )

        if "login" in driver.current_url.lower() and "error" not in driver.page_source.lower():
            # Still on login - might be wrong credentials
            report.add_step("Login", False, "Login failed: remained on login page (check credentials)")
            report.set_finished(False, "Login failure")
            return report, False

        report.add_step("Login", True, "Submitted credentials and left login page")

        # Step 3: Navigate to device management
        devices_url = f"{base_url.rstrip('/')}{SELECTORS['device_management_url_path']}"
        driver.get(devices_url)
        WebDriverWait(driver, timeout).until(EC.url_contains("device") if "device" in devices_url else lambda d: True)
        report.add_step("Navigate to device management", True, f"Loaded {devices_url}")

        # Step 4: Search for device by ID
        search_el = _try_selectors(driver, SELECTORS["device_search_input"], timeout)
        if not search_el:
            report.add_step(
                "Search for device",
                False,
                "Device search input not found.",
            )
            report.set_finished(False, "Search UI not found")
            return report, False

        search_el.clear()
        search_el.send_keys(device_id)
        search_btn = _try_selectors(driver, SELECTORS["device_search_button"], timeout)
        if search_btn:
            search_btn.click()
        else:
            from selenium.webdriver.common.keys import Keys
            search_el.send_keys(Keys.RETURN)
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr, .device-list .device, [data-device-id]")))
        report.add_step("Search for device", True, f"Searched for device ID: {device_id}")

        # Step 5: Verify device status on page
        try:
            # Try to find row containing device_id and then status
            rows = driver.find_elements(By.CSS_SELECTOR, SELECTORS["device_row"])
            status_el = None
            for row in rows:
                if device_id in row.text:
                    status_candidates = row.find_elements(By.CSS_SELECTOR, SELECTORS["device_status_cell"])
                    if status_candidates:
                        status_el = status_candidates[0]
                        break
                    # Fallback: first cell after device ID might be status in many tables
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        status_el = cells[1]
                        break
            if status_el is None:
                report.add_step(
                    "Verify device status (UI)",
                    False,
                    f"Device '{device_id}' not found in list or status element not located.",
                )
                report.set_finished(False, "Device not found or status not visible")
                return report, False

            actual_status = status_el.text.strip()
            if actual_status != expected_status:
                report.add_step(
                    "Verify device status (UI)",
                    False,
                    f"Status mismatch: expected '{expected_status}', got '{actual_status}'",
                    details=actual_status,
                )
                report.set_finished(False, "Status mismatch")
                return report, False

            report.add_step("Verify device status (UI)", True, f"Displayed status '{actual_status}' matches expected '{expected_status}'")
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

    # Optional email
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
