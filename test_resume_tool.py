"""Run with:  python test_resume_tool.py
Checks that score_resume is registered and safe. No Azure needed."""

import tempfile
from pathlib import Path

import agent_tools
import resume_tools
from agent_tools import FUNCTION_TOOLS, run_tool

passed = 0


def check(name, condition):
    global passed
    assert condition, f"FAILED: {name}"
    passed += 1
    print(f"  ok  {name}")


GOOD_RESUME = """Rahul Sharma
rahul@example.com | +91 98765 43210 | linkedin.com/in/rahul | github.com/rahul
Education
B.Tech in Computer Science, 2023 - 2027, CGPA 8.4/10
Skills
Python, Java, SQL, Git, Docker, Azure, Flask, MySQL, Data Structures, OOP, REST API, Linux
Projects
- Built a Flask app used by 40 students with MySQL
- Reduced page load time by 35% using query optimization
- Designed a REST API with 12 endpoints and 20 automated tests
Experience
- Automated weekly reports in Python, saving 6 hours per week
- Fixed 25 bugs in a Spring Boot service with a team of 5
Certifications
Microsoft Azure Fundamentals
""" + ("Additional detail line about project work and learning outcomes. " * 20)

print("Registration")
names = [t.name for t in FUNCTION_TOOLS]
check("score_resume is registered", "score_resume" in names)
check("Tool takes no arguments (model cannot choose a file)",
      [t for t in FUNCTION_TOOLS if t.name == "score_resume"][0].parameters["properties"] == {})
check("Only one score_resume tool", names.count("score_resume") == 1)

print("Running the tool")
original = resume_tools.RESUME_PATH
try:
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "nothing.pdf"
        resume_tools.RESUME_PATH = missing
        check("No resume saved -> FILE_NOT_FOUND", run_tool("score_resume", {})["status"] == "FILE_NOT_FOUND")

        import docx
        d = docx.Document()
        for line in GOOD_RESUME.splitlines():
            d.add_paragraph(line)
        good = Path(tmp) / "resume.docx"
        d.save(good)
        resume_tools.RESUME_PATH = good
        r = run_tool("score_resume", {})
        check("Saved resume is scored", r["status"] == "OK" and 0 <= r["total_score"] <= 100)
        check("Result has the fields the agent needs",
              {"total_score", "grade", "categories", "improvements", "found"} <= set(r))
        r2 = run_tool("score_resume", {"path": "C:/Windows/system.ini", "resume": "other.pdf"})
        check("Arguments from the model are ignored (same file, same score)",
              r2["total_score"] == r["total_score"])
        check("Same resume -> same score every time", run_tool("score_resume", {})["total_score"] == r["total_score"])
finally:
    resume_tools.RESUME_PATH = original

print("Old tools still work")
check("check_eligibility still works", run_tool("check_eligibility", {"company_name": "TechNova"})["status"] == "ELIGIBLE")
check("Unknown tool -> ERROR", run_tool("hack", {})["status"] == "ERROR")

print(f"\nAll {passed} tests passed.")
