"""
Pytest: API automation. Run from project root: pytest tests/test_api.py
"""

from pathlib import Path

from api_automation import run_api_tests
from reporter import format_console_report


def test_api_automation(request):
    """Run full API flow (auth -> GET device -> verify status)."""
    reports_dir = Path(__file__).resolve().parent.parent / "reports"
    report, success = run_api_tests(output_dir=reports_dir)
    request.node.user_properties.append(("cardiofocus_report", report))
    print(format_console_report(report))
    assert success, f"API automation failed: {report.error_summary or report.steps}"
