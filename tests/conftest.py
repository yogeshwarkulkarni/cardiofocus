"""
Pytest hooks: inject CardioFocus step report (API URL, response, etc.) into pytest-html report.
"""

import pytest
from reporter import format_report_html


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        for name, value in getattr(item, "user_properties", []):
            if name == "cardiofocus_report" and value is not None:
                extra = getattr(report, "extras", None) or getattr(report, "extra", [])
                try:
                    pytest_html = item.config.pluginmanager.getplugin("html")
                    if pytest_html is not None:
                        html_content = format_report_html(value)
                        extra.append(pytest_html.extras.html(html_content))
                except Exception:
                    pass
                if hasattr(report, "extras"):
                    report.extras = extra
                else:
                    report.extra = extra
                break
