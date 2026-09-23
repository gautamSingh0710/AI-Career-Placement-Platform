"""Run with:  python test_eligibility.py
No extra libraries needed."""

import json

from eligibility import check_eligibility, find_eligible_companies

# A student who meets basic criteria; tests change one thing at a time.
GOOD = dict(cgpa=8.5, branch="CSE", active_backlogs=0,
            tenth_percent=80, twelfth_percent=80, has_backlog_history=False)
TODAY = "2026-09-20"

passed = 0


def check(name, condition):
    global passed
    assert condition, f"FAILED: {name}"
    passed += 1
    print(f"  ok  {name}")


def status(company, **overrides):
    args = {**GOOD, "today": TODAY, **overrides}
    return check_eligibility(company, **args)


print("Basic pass/fail")
check("TechNova: good student is ELIGIBLE", status("TechNova")["status"] == "ELIGIBLE")
check("TechNova: CGPA 6.9 fails", status("TechNova", cgpa=6.9)["status"] == "NOT_ELIGIBLE")
check("TechNova: CGPA 7.0 (boundary) passes", status("TechNova", cgpa=7.0)["status"] == "ELIGIBLE")
check("TechNova: ME branch fails", status("TechNova", branch="ME")["status"] == "NOT_ELIGIBLE")
check("TechNova: 1 active backlog fails", status("TechNova", active_backlogs=1)["status"] == "NOT_ELIGIBLE")
check("TechNova: 12th 59% fails", status("TechNova", twelfth_percent=59)["status"] == "NOT_ELIGIBLE")
check("CodeCraft: ME, CGPA 6.0, 1 backlog, 55% passes",
      status("CodeCraft", cgpa=6.0, branch="ME", active_backlogs=1,
             tenth_percent=55, twelfth_percent=55)["status"] == "ELIGIBLE")
check("CodeCraft: 2 backlogs fails", status("CodeCraft", active_backlogs=2)["status"] == "NOT_ELIGIBLE")

print("Backlog history (CloudPeak)")
check("CloudPeak: no history passes", status("CloudPeak")["status"] == "ELIGIBLE")
check("CloudPeak: cleared backlog history fails",
      status("CloudPeak", has_backlog_history=True)["status"] == "NOT_ELIGIBLE")
check("CloudPeak: unknown history -> NEEDS_MORE_INFO",
      status("CloudPeak", has_backlog_history=None)["status"] == "NEEDS_MORE_INFO")
check("TechNova: history does not matter",
      status("TechNova", has_backlog_history=True)["status"] == "ELIGIBLE")

print("Company name matching")
check("Infosys -> COMPANY_NOT_FOUND", status("Infosys")["status"] == "COMPANY_NOT_FOUND")
check("Empty name -> COMPANY_NOT_FOUND", status("")["status"] == "COMPANY_NOT_FOUND")
check("Full name works", status("TechNova Solutions")["company"] == "TechNova Solutions")
check("Messy spelling works", status("  TECHNOVA ")["company"] == "TechNova Solutions")
check("Partial 'Tech' does NOT match", status("Tech")["status"] == "COMPANY_NOT_FOUND")

print("Branch names")
check("'Computer Science' -> CSE", status("TechNova", branch="Computer Science")["status"] == "ELIGIBLE")
check("'AI & DS' matches DataBridge", status("DataBridge", branch="AI & DS")["status"] == "ELIGIBLE")

print("Missing / invalid input")
r = status("TechNova", tenth_percent=None, twelfth_percent=None)
check("Missing marks -> NEEDS_MORE_INFO", r["status"] == "NEEDS_MORE_INFO")
check("Missing list names 10th and 12th", r["missing"] == ["10th marks %", "12th marks %"])
check("Failure beats missing info",
      status("TechNova", cgpa=6.0, tenth_percent=None)["status"] == "NOT_ELIGIBLE")
check("CGPA 11 -> INVALID_INPUT", status("TechNova", cgpa=11)["status"] == "INVALID_INPUT")
check("Negative backlogs -> INVALID_INPUT", status("TechNova", active_backlogs=-1)["status"] == "INVALID_INPUT")
check("Text CGPA -> INVALID_INPUT", status("TechNova", cgpa="8.5")["status"] == "INVALID_INPUT")

print("Attendance and deadline")
check("Attendance 70% fails", status("TechNova", attendance_percent=70)["status"] == "NOT_ELIGIBLE")
check("Attendance 80% passes", status("TechNova", attendance_percent=80)["status"] == "ELIGIBLE")
check("Registration open on 20 Sep", status("TechNova")["registration_open"] is True)
check("Registration closed after 8 Oct",
      status("TechNova", today="2026-10-09")["registration_open"] is False)

print("find_eligible_companies")
res = find_eligible_companies(**GOOD, today=TODAY)
names = sorted(c["company"] for c in res["eligible"])
check("CSE student: 5 eligible companies", len(names) == 5)
check("GreenGrid (ECE/EEE only) is not eligible",
      [c["company"] for c in res["not_eligible"]] == ["GreenGrid Electronics"])

print(f"\nAll {passed} tests passed.")

print("\nSample output (what the agent will receive):")
print(json.dumps(status("TechNova", cgpa=6.9), indent=2))
