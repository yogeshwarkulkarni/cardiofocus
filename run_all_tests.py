"""
Integrated test workflow: runs both UI and API automation, then reports combined results.
Optional email notification. Use config (.env) for credentials and test data.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import config
from reporter import TestRunReport, format_console_report, write_report_file, send_report_email
from ui_automation import run_ui_tests
from api_automation import run_api_tests


def _run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def run_integrated_tests(
    run_ui: bool = True,
    run_api: bool = True,
    output_dir: Optional[Path] = None,
) -> Tuple[TestRunReport, bool]:
    """
    Run UI and/or API tests and produce a single combined report.
    Returns (combined_report, overall_success).
    """
    output_dir = output_dir or Path(__file__).resolve().parent / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = _run_id()
    combined = TestRunReport(
        run_id=run_id,
        started_at=datetime.utcnow().isoformat() + "Z",
        test_name="Integrated (UI + API)",
    )
    all_passed = True

    if run_ui:
        ui_report, ui_ok = run_ui_tests()
        all_passed = all_passed and ui_ok
        combined.add_step("UI test suite", ui_ok, f"UI: {'PASS' if ui_ok else 'FAIL'} ({ui_report.passed_count()}/{ui_report.total_count()} steps)")
        for s in ui_report.steps:
            combined.add_step(f"  UI: {s.step_name}", s.passed, s.message, s.details)

    if run_api:
        api_report, api_ok = run_api_tests(output_dir=output_dir)
        all_passed = all_passed and api_ok
        combined.add_step("API test suite", api_ok, f"API: {'PASS' if api_ok else 'FAIL'} ({api_report.passed_count()}/{api_report.total_count()} steps)")
        for s in api_report.steps:
            combined.add_step(f"  API: {s.step_name}", s.passed, s.message, s.details)

    combined.set_finished(all_passed, None if all_passed else "One or more suites failed")
    return combined, all_passed


def main() -> int:
    report, success = run_integrated_tests(run_ui=True, run_api=True)
    print(format_console_report(report))
    reports_dir = Path(__file__).resolve().parent / "reports"
    report_path = write_report_file(report, output_dir=reports_dir)
    print(f"Report written to: {report_path}")

    if config.REPORT_EMAIL_ENABLED and config.REPORT_EMAIL_TO and config.REPORT_EMAIL_FROM:
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
