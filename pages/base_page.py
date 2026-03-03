"""
Base page: shared driver, timeout, and element-finding helpers.
"""

from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


class BasePage:
    """Base class for all page objects. Holds driver, base URL, and timeout."""

    def __init__(self, driver: webdriver.Chrome, base_url: str, timeout: int = 15):
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _find_element_css(self, css_selector: str, timeout: Optional[int] = None) -> Optional[WebElement]:
        """Find element by CSS selector with explicit wait. Returns None on timeout."""
        t = timeout if timeout is not None else self.timeout
        try:
            return WebDriverWait(self.driver, t).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )
        except TimeoutException:
            return None

    def _try_selectors(self, selectors: str, timeout: Optional[int] = None) -> Optional[WebElement]:
        """Try multiple CSS selectors (comma-separated); return first match."""
        t = timeout if timeout is not None else self.timeout
        for sel in (s.strip() for s in selectors.split(",")):
            el = self._find_element_css(sel, timeout=min(3, t))
            if el is not None:
                return el
        return None
