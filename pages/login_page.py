"""
Login page: URL, locators, and actions for portal login.
"""

from typing import Optional, Tuple

from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage


class LoginPage(BasePage):
    """Page object for the login page."""

    URL_PATH = "/login"

    # Comma-separated CSS selectors (first match is used). Adjust for your portal DOM.
    USERNAME_INPUT = "input[name='username'], #username, input[type='email']"
    PASSWORD_INPUT = "input[name='password'], #password"
    SUBMIT_BUTTON = "button[type='submit'], input[type='submit'], .login-button"

    def get_url(self) -> str:
        return f"{self.base_url}{self.URL_PATH}"

    def get_login_elements(self) -> Tuple[Optional[WebElement], Optional[WebElement], Optional[WebElement]]:
        """Return (username_element, password_element, submit_element). Any may be None if not found."""
        user_el = self._try_selectors(self.USERNAME_INPUT)
        pass_el = self._try_selectors(self.PASSWORD_INPUT)
        submit_el = self._try_selectors(self.SUBMIT_BUTTON)
        return user_el, pass_el, submit_el

    def login(self, username: str, password: str) -> None:
        """Fill credentials and click submit. Assumes elements are present."""
        user_el, pass_el, submit_el = self.get_login_elements()
        if user_el:
            user_el.clear()
            user_el.send_keys(username)
        if pass_el:
            pass_el.clear()
            pass_el.send_keys(password)
        if submit_el:
            submit_el.click()

    def wait_until_left_login(self) -> None:
        """Wait until URL no longer contains 'login' or page shows error."""
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(self.driver, self.timeout).until(
            lambda d: "login" not in d.current_url.lower() or "error" in d.page_source.lower()
        )

    def is_still_on_login_page(self) -> bool:
        """True if still on login URL and no error message visible."""
        return (
            "login" in self.driver.current_url.lower()
            and "error" not in self.driver.page_source.lower()
        )
