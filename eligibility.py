"""
Company eligibility checker.

The LLM must NEVER decide eligibility. This code decides; the LLM only
explains the result it returns.

Statuses returned:
  ELIGIBLE          - every criterion passed
  NOT_ELIGIBLE      - at least one criterion failed (see "failed")
  NEEDS_MORE_INFO   - nothing failed, but some details are missing (see "missing")
  COMPANY_NOT_FOUND - company is not in companies.json
  INVALID_INPUT     - a value is out of range or the wrong type
"""

import json
import re
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).with_name("companies.json")

# Normalised text -> canonical branch code.
_BRANCH_ALIASES = {
    "cse": "CSE", "cs": "CSE", "computerscience": "CSE",
    "computerscienceengineering": "CSE", "computerscienceandengineering": "CSE",
    "it": "IT", "informationtechnology": "IT",
    "ece": "ECE", "electronicsandcommunication": "ECE",
    "electronicscommunication": "ECE", "electronicsandcommunicationengineering": "ECE",
    "eee": "EEE", "electrical": "EEE", "electricalandelectronics": "EEE",
    "electricalandelectronicsengineering": "EEE",
    "aids": "AI&DS", "aianddatascience": "AI&DS",
    "artificialintelligenceanddatascience": "AI&DS",
    "me": "ME", "mechanical": "ME", "mechanicalengineering": "ME",
    "ce": "CE", "civil": "CE", "civilengineering": "CE",
}


def _norm(text):
    """Lowercase and keep only letters/digits: 'AI & DS' -> 'aids'."""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def normalize_branch(branch):
    if branch is None:
        return None
    key = _norm(branch)
    return _BRANCH_ALIASES.get(key, str(branch).strip().upper())


@lru_cache(maxsize=1)
def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def find_company(name):
    """Exact match on full name or alias (case/space/punctuation insensitive).
    No fuzzy matching on purpose: an unknown company must return None."""
    key = _norm(name or "")
    if not key:
        return None
    for company in load_data()["companies"]:
        keys = {_norm(company["name"])} | {_norm(a) for a in company.get("aliases", [])}
        if key in keys:
            return company
    return None


def _to_date(value):
    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _validate(cgpa, active_backlogs, tenth, twelfth, attendance):
    def bad_number(v):
        return isinstance(v, bool) or not isinstance(v, (int, float))

    if cgpa is not None and (bad_number(cgpa) or not 0 <= cgpa <= 10):
        return "cgpa must be a number between 0 and 10"
    if active_backlogs is not None and (
        isinstance(active_backlogs, bool)
        or not isinstance(active_backlogs, int)
        or active_backlogs < 0
    ):
        return "active_backlogs must be a whole number, 0 or more"
    for label, v in (("tenth_percent", tenth), ("twelfth_percent", twelfth),
                     ("attendance_percent", attendance)):
        if v is not None and (bad_number(v) or not 0 <= v <= 100):
            return f"{label} must be a number between 0 and 100"
    return None


def _check(criterion, required, actual, passed):
    # passed: True / False / None (None = student detail missing)
    return {"criterion": criterion, "required": required, "actual": actual, "passed": passed}


def check_eligibility(
    company_name,
    cgpa=None,
    branch=None,
    active_backlogs=None,
    tenth_percent=None,
    twelfth_percent=None,
    has_backlog_history=None,
    attendance_percent=None,
    today=None,
):
    """Check one student against one company. Returns a plain dict."""
    company = find_company(company_name)
    if company is None:
        return {
            "status": "COMPANY_NOT_FOUND",
            "company": company_name,
            "message": "This company is not in the placement records.",
        }

    error = _validate(cgpa, active_backlogs, tenth_percent, twelfth_percent, attendance_percent)
    if error:
        return {"status": "INVALID_INPUT", "company": company["name"], "error": error}

    general = load_data()["general_rules"]
    checks = []

    # 1. CGPA (company minimum, but never below the college registration minimum)
    min_cgpa = max(company["min_cgpa"], general["min_cgpa_to_register"])
    checks.append(_check("CGPA", f">= {min_cgpa}", cgpa,
                         None if cgpa is None else cgpa >= min_cgpa))

    # 2. Branch
    student_branch = normalize_branch(branch)
    allowed = company["branches"]
    if allowed == "ALL":
        branch_ok = None if student_branch is None else True
        allowed_text = "All branches"
    else:
        branch_ok = None if student_branch is None else student_branch in allowed
        allowed_text = ", ".join(allowed)
    checks.append(_check("Branch", allowed_text, student_branch, branch_ok))

    # 3. Active backlogs
    max_bl = company["max_active_backlogs"]
    checks.append(_check("Active backlogs", f"<= {max_bl}", active_backlogs,
                         None if active_backlogs is None else active_backlogs <= max_bl))

    # 4. Backlog history (only for companies that reject any backlog history)
    if not company.get("backlog_history_allowed", True):
        checks.append(_check("Backlog history", "No backlog history allowed",
                             has_backlog_history,
                             None if has_backlog_history is None else not has_backlog_history))

    # 5. 10th and 12th marks
    min_marks = company["min_10th_12th_percent"]
    checks.append(_check("10th marks %", f">= {min_marks}", tenth_percent,
                         None if tenth_percent is None else tenth_percent >= min_marks))
    checks.append(_check("12th marks %", f">= {min_marks}", twelfth_percent,
                         None if twelfth_percent is None else twelfth_percent >= min_marks))

    # 6. Attendance: only checked if the student's value is given
    if attendance_percent is not None:
        min_att = general["min_attendance_percent"]
        checks.append(_check("Attendance %", f">= {min_att}", attendance_percent,
                             attendance_percent >= min_att))

    failed = [f"{c['criterion']}: needs {c['required']}, student has {c['actual']}"
              for c in checks if c["passed"] is False]
    missing = [c["criterion"] for c in checks if c["passed"] is None]

    if failed:
        status = "NOT_ELIGIBLE"
    elif missing:
        status = "NEEDS_MORE_INFO"
    else:
        status = "ELIGIBLE"

    notes = []
    if attendance_percent is None:
        notes.append(f"Attendance ({general['min_attendance_percent']}% required) was not verified.")
    deadline = _to_date(company["registration_deadline"])
    registration_open = _to_date(today) <= deadline
    if not registration_open:
        notes.append(f"Registration deadline ({deadline.isoformat()}) has passed.")
    notes.append("Final decision rests with the Placement Cell.")

    return {
        "status": status,
        "company": company["name"],
        "tier": company["tier"],
        "package_lpa": company["package_lpa"],
        "role": company["role"],
        "checks": checks,
        "failed": failed,
        "missing": missing,
        "registration_open": registration_open,
        "registration_deadline": company["registration_deadline"],
        "drive_date": company["drive_date"],
        "notes": notes,
    }


def find_eligible_companies(
    cgpa=None,
    branch=None,
    active_backlogs=None,
    tenth_percent=None,
    twelfth_percent=None,
    has_backlog_history=None,
    attendance_percent=None,
    today=None,
):
    """Run check_eligibility against every company and group the results."""
    result = {"eligible": [], "not_eligible": [], "needs_more_info": []}
    for company in load_data()["companies"]:
        r = check_eligibility(
            company["name"], cgpa, branch, active_backlogs, tenth_percent,
            twelfth_percent, has_backlog_history, attendance_percent, today,
        )
        if r["status"] == "INVALID_INPUT":
            return r
        summary = {
            "company": r["company"], "tier": r["tier"], "package_lpa": r["package_lpa"],
            "role": r["role"], "drive_date": r["drive_date"],
            "registration_open": r["registration_open"],
        }
        if r["status"] == "ELIGIBLE":
            result["eligible"].append(summary)
        elif r["status"] == "NOT_ELIGIBLE":
            result["not_eligible"].append({**summary, "failed": r["failed"]})
        else:
            result["needs_more_info"].append({**summary, "missing": r["missing"]})
    return result
