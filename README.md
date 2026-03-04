# CardioFocus Device Portal – Automation Suite

Automation scripts for validating core functionality of the CardioFocus device management web portal: **UI automation** (Selenium), **API automation** (REST), **test reporting**, and optional **integrated workflow** with email notification.

---

## Deliverables

| Deliverable | File | Description |
|-------------|------|-------------|
| UI automation | `ui_automation.py`, `pages/` | Selenium + **Page Object Model**: login, device list, search, status verification |
| API automation | `api_automation.py` | REST: auth, GET device by ID, status verification |
| Test reporting | `reporter.py`, **pytest-html** | Console, JSON/text files, HTML report; optional email |
| Pytest tests | `tests/test_ui.py`, `tests/test_api.py` | Pytest entry points for UI and API (pytest-html report) |
| Integrated workflow | `run_all_tests.py` | Runs UI + API in one flow, single report |
| Config | `config.py`, `.env.example` | Central config; credentials via env / `.env` |

---

## Requirements

- **Python**: 3.9 or 3.10+ recommended  
- **Chrome**: Installed for Selenium (ChromeDriver is managed via `webdriver-manager`)  
- **Dependencies**: See `requirements.txt`

---

## Setup

### 1. Clone or extract the project

```bash
cd cardiofocus-automation
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure credentials and test data

Copy the example env file and edit with your values (never commit `.env`):

```bash
cp .env.example .env
# Edit .env: set PORTAL_USERNAME, PORTAL_PASSWORD, and optionally API_* and TEST_*
```

Required for **UI tests**: `PORTAL_USERNAME`, `PORTAL_PASSWORD`.  
Required for **API tests**: either `API_AUTH_TOKEN` or `API_BASIC_USER` + `API_BASIC_PASSWORD`.  
Optional: `TEST_DEVICE_ID`, `EXPECTED_DEVICE_STATUS` (defaults: `DEV-001`, `Active`).

---

## Running the tests

- **UI only**  
  ```bash
  python ui_automation.py
  ```

- **API only**  
  ```bash
  python api_automation.py
  ```

- **Integrated (UI + API)**  
  ```bash
  python run_all_tests.py
  ```

- **With pytest (pytest-html report)**  
  ```bash
  pytest
  ```
  Runs all tests in `tests/` and writes **`reports/report.html`**. Open it in a browser for pass/fail and details. To run only API or only UI:
  ```bash
  pytest tests/test_api.py
  pytest tests/test_ui.py
  ```

Exit code: `0` = all validations passed, `1` = one or more failed.

Reports: `reports/report_<run_id>.txt`, `reports/report_<run_id>.json` (script runs); **`reports/report.html`** (pytest-html when using pytest).

---

## Test reporting

- **Console**: Pass/fail per step with a short summary.  
- **Files**:  
  - `reports/report_<run_id>.txt` – human-readable (script runs).  
  - `reports/report_<run_id>.json` – machine-readable (script runs). 
  - **`reports/report.html`** – pytest-html report when you run `pytest` (open in browser).  Sample report : [report.html](https://github.com/user-attachments/files/25748442/report.html)
- **Email** (optional): Set `REPORT_EMAIL_ENABLED=true`, `REPORT_EMAIL_TO`, `REPORT_EMAIL_FROM`, and SMTP settings in `.env`; the scripts will send the same report by email when enabled.

---

## Assumptions and design decisions

### Assumptions

1. **Portal URL**: `https://portal.cardiofocus.com` (overridable via `PORTAL_BASE_URL` / `API_BASE_URL`).  
2. **Login**: Form with username + password and a submit button; exact selectors may need to be updated for the real portal (see `pages/login_page.py`).  
3. **Device management**: A page at `/devices` with search and a list/table of devices; device ID and status are visible in the DOM.  
4. **REST API**:  
   - `GET /api/devices/{device_id}` returns JSON with at least a `status` field.  
   - Auth: Bearer token (header `Authorization: Bearer <token>`) or HTTP Basic.  
5. **Sensitive data**: Credentials and API keys come only from environment variables or `.env`, not from code or repo.

### Design decisions

1. **Config**: Single `config.py` reading from `os.environ` and optional `.env` so that credentials stay out of code and can differ per environment.  
2. **UI**:  
   - Explicit waits (and a short implicit wait) to avoid flakiness.  
   - Multiple candidate CSS selectors per element so small DOM changes don’t break runs; **Page Object Model**: selectors and actions live in `pages/login_page.py` and `pages/devices_page.py` for easy tuning.  
   - Clear error handling for “login failed” and “device not found / status not found,” with distinct report steps.  
3. **API**:  
   - `requests.Session` for auth and connection reuse.  
   - Timeouts and handling for connection/HTTP errors so failures are reported, not crashes.  
4. **Reporting**:  
   - One report type (`TestRunReport`) with step-level pass/fail and optional details.  
   - Same format for console, file, and email to keep behavior consistent.  
5. **Scalability**:  
   - No hardcoded credentials; config and env support multiple environments.  
   - Reporting and test logic are separated so adding new steps or outputs is straightforward.

---

## Optional: API test against a mock server

If you don’t have a live portal API, you can run a minimal mock that serves `GET /api/devices/{id}` with a JSON body including `status`:

```bash
python mock_api_server.py
# In another terminal: set API_BASE_URL=http://127.0.0.1:8000 (leave API auth unset) and run api_automation.py
```

See `mock_api_server.py` for the exact response shape. No extra dependencies (stdlib only).

---

## Optional: Email notification

In `.env`:

```env
REPORT_EMAIL_ENABLED=true
REPORT_EMAIL_TO=team@example.com
REPORT_EMAIL_FROM=automation@example.com
REPORT_EMAIL_SMTP_HOST=smtp.example.com
REPORT_EMAIL_SMTP_PORT=587
```

When enabled, each run (UI, API, or integrated) will attempt to send the report by email after writing the files. No extra packages are required (uses the standard library).

---

## File layout

```
cardiofocus-automation/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── pytest.ini              # Pytest options (--html=reports/report.html)
├── config.py               # Configuration from env / .env
├── reporter.py             # Test reporting (console, file, email)
├── pages/                  # Page Object Model (base_page, login_page, devices_page)
├── ui_automation.py        # Selenium UI automation (uses pages/)
├── api_automation.py       # REST API automation
├── run_all_tests.py        # Integrated UI + API workflow (entry point)
├── mock_api_server.py      # Optional local mock for API (stdlib only)
├── tests/
│   ├── __init__.py
│   ├── test_ui.py          # Pytest: UI test
│   └── test_api.py         # Pytest: API test
└── reports/                # report_*.txt, report_*.json; report.html (pytest-html)
```

---

## Updating for your real portal

1. **UI**: In `pages/login_page.py` and `pages/devices_page.py`, update the CSS selector constants to match your login form, device list, and search controls.  
2. **URLs**: Set `PORTAL_BASE_URL` and `API_BASE_URL` in `.env` if different from `https://portal.cardiofocus.com`.  
3. **API auth**: If your API uses a different auth scheme (e.g. custom header), adjust `get_api_session()` in `api_automation.py` and set the corresponding env vars.

After that, run `ui_automation.py`, `api_automation.py`, or `run_all_tests.py` as above and check `reports/` and the console for pass/fail and any errors.
