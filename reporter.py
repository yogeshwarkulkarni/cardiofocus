"""
Test result reporting for CardioFocus automation.
Provides structured console output and optional file/email reporting.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Optional email - only used if config enables it
try:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    HAS_EMAIL = True
except ImportError:
    HAS_EMAIL = False


@dataclass
class StepResult:
    """Result of a single validation step."""
    step_name: str
    passed: bool
    message: str
    details: Optional[str] = None


@dataclass
class TestRunReport:
    """Report for a full test run."""
    run_id: str
    started_at: str
    finished_at: Optional[str] = None
    test_name: str = ""
    steps: List[StepResult] = field(default_factory=list)
    overall_passed: bool = False
    error_summary: Optional[str] = None

    def add_step(self, step_name: str, passed: bool, message: str, details: Optional[str] = None) -> None:
        self.steps.append(StepResult(step_name=step_name, passed=passed, message=message, details=details))

    def set_finished(self, overall_passed: bool, error_summary: Optional[str] = None) -> None:
        self.finished_at = datetime.utcnow().isoformat() + "Z"
        self.overall_passed = overall_passed
        self.error_summary = error_summary

    def passed_count(self) -> int:
        return sum(1 for s in self.steps if s.passed)

    def total_count(self) -> int:
        return len(self.steps)


def format_console_report(report: TestRunReport) -> str:
    """Format report for console output."""
    lines = [
        "",
        "=" * 60,
        f"  CardioFocus Automation - Test Report",
        f"  Run ID: {report.run_id}",
        f"  Test: {report.test_name}",
        f"  Started: {report.started_at}",
        f"  Finished: {report.finished_at or 'N/A'}",
        "=" * 60,
        "",
    ]
    for i, step in enumerate(report.steps, 1):
        status = "PASS" if step.passed else "FAIL"
        symbol = "[+]" if step.passed else "[x]"
        lines.append(f"  {symbol} Step {i}: {step.step_name}")
        lines.append(f"      Status: {status}")
        lines.append(f"      {step.message}")
        if step.details:
            lines.append(f"      Details: {step.details}")
        lines.append("")
    lines.extend([
        "-" * 60,
        f"  Result: {report.passed_count()}/{report.total_count()} steps passed",
        f"  Overall: {'PASS' if report.overall_passed else 'FAIL'}",
        "-" * 60,
    ])
    if report.error_summary:
        lines.append(f"  Error summary: {report.error_summary}")
    lines.append("")
    return "\n".join(lines)


def format_report_html(report: TestRunReport) -> str:
    """Format report as HTML for pytest-html extra section (each step with message/details)."""
    import html
    rows = []
    for i, step in enumerate(report.steps, 1):
        status = "PASS" if step.passed else "FAIL"
        status_color = "#28a745" if step.passed else "#dc3545"
        msg = html.escape(step.message)
        details = ""
        if step.details:
            details = f'<div class="step-details"><pre>{html.escape(str(step.details))}</pre></div>'
        rows.append(
            f'<tr><td>{i}</td><td><strong>{html.escape(step.step_name)}</strong></td>'
            f'<td style="color:{status_color};font-weight:bold">{status}</td>'
            f'<td>{msg}</td><td>{details}</td></tr>'
        )
    table_rows = "\n".join(rows)
    overall = "PASS" if report.overall_passed else "FAIL"
    overall_color = "#28a745" if report.overall_passed else "#dc3545"
    return f"""
<div class="cardiofocus-report" style="margin:1em 0;font-family:sans-serif">
  <div style="margin-bottom:0.5em"><strong>Run ID:</strong> {html.escape(report.run_id)} &nbsp;|&nbsp;
    <strong>Test:</strong> {html.escape(report.test_name)} &nbsp;|&nbsp;
    <strong>Result:</strong> <span style="color:{overall_color};font-weight:bold">{overall}</span>
    ({report.passed_count()}/{report.total_count()} steps)
  </div>
  <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%">
    <thead><tr style="background:#f0f0f0">
      <th>#</th><th>Step</th><th>Status</th><th>Message (e.g. API URL / endpoint)</th><th>Details (e.g. API response)</th>
    </tr></thead>
    <tbody>{table_rows}</tbody>
  </table>
</div>
"""


def write_report_file(report: TestRunReport, output_dir: Optional[Path] = None) -> Path:
    """Write JSON and text report files. Returns path to text report."""
    output_dir = output_dir or Path(".")
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / f"report_{report.run_id}"
    json_path = base.with_suffix(".json")
    txt_path = base.with_suffix(".txt")
    with open(json_path, "w") as f:
        json.dump(asdict(report), f, indent=2)
    with open(txt_path, "w") as f:
        f.write(format_console_report(report))
    return txt_path


def send_report_email(report: TestRunReport, to_addr: str, from_addr: str, smtp_host: str, smtp_port: int) -> bool:
    """Send report via email. Returns True if sent successfully."""
    if not HAS_EMAIL:
        return False
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"CardioFocus Test Report: {'PASS' if report.overall_passed else 'FAIL'} - {report.run_id}"
        msg["From"] = from_addr
        msg["To"] = to_addr
        body = format_console_report(report)
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.send_message(msg)
        return True
    except Exception:
        return False
