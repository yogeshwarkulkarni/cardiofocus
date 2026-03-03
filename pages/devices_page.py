"""
Devices page: device list, search, and status. Adjust selectors for your portal DOM.
"""

from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage


class DevicesPage(BasePage):
    """Page object for the device management / devices list page."""

    URL_PATH = "/devices"

    DEVICE_SEARCH_INPUT = "input[placeholder*='Search'], input[name='search'], #device-search"
    DEVICE_SEARCH_BUTTON = ".search-btn, button[type='submit'], input[type='submit']"
    DEVICE_ROW = "tr[data-device-id], table tbody tr"
    DEVICE_STATUS_CELL = "td[data-status], .device-status, .status"

    # Fallback for table without status class: wait for results
    RESULTS_SELECTOR = "table tbody tr, .device-list .device, [data-device-id]"

    def get_url(self) -> str:
        return f"{self.base_url}{self.URL_PATH}"

    def open(self) -> None:
        """Navigate to the devices page."""
        self.driver.get(self.get_url())
        if "device" in self.get_url():
            WebDriverWait(self.driver, self.timeout).until(
                EC.url_contains("device")
            )

    def get_search_input(self) -> Optional[WebElement]:
        return self._try_selectors(self.DEVICE_SEARCH_INPUT)

    def get_search_button(self) -> Optional[WebElement]:
        return self._try_selectors(self.DEVICE_SEARCH_BUTTON)

    def search_device(self, device_id: str) -> None:
        """Type device_id in search and submit (button click or Enter)."""
        search_el = self.get_search_input()
        if not search_el:
            return
        search_el.clear()
        search_el.send_keys(device_id)
        search_btn = self.get_search_button()
        if search_btn:
            search_btn.click()
        else:
            search_el.send_keys(Keys.RETURN)
        WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, self.RESULTS_SELECTOR))
        )

    def get_device_status_for(self, device_id: str) -> Optional[str]:
        """
        Find the row containing device_id and return the status text, or None if not found.
        Tries explicit status cell first, then second table cell as fallback.
        """
        rows = self.driver.find_elements(By.CSS_SELECTOR, self.DEVICE_ROW)
        for row in rows:
            if device_id in row.text:
                status_candidates = row.find_elements(By.CSS_SELECTOR, self.DEVICE_STATUS_CELL)
                if status_candidates:
                    return status_candidates[0].text.strip()
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    return cells[1].text.strip()
        return None
