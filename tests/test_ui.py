"""
Pytest: UI automation. Run from project root: pytest tests/test_ui.py
"""

from ui_automation import run_ui_tests
from reporter import format_console_report


def test_ui_automation(request):
    """Run full UI flow (login -> devices -> search -> verify status)."""
    report, success = run_ui_tests()
    request.node.user_properties.append(("cardiofocus_report", report))
    print(format_console_report(report))
    assert success, f"UI automation failed: {report.error_summary or report.steps}"
