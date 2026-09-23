import json

from jd_analyzer import run_jd_tool
from resume_jd_matcher import match_resume_with_jd
from skill_gap_analyzer import analyze_skill_gaps
from learning_resource_finder import build_learning_plan


# ============================================================
# STUDENT PROFILE
# ============================================================

STUDENT_PROFILE = {
    "name": "Gautam Singh",

    "skills": [
        "Java",
        "Python",
        "C++",
        "SQL",
        "Git",
        "GitHub",
        "Django",
        "OOP"
    ],

    "qualifications": [
        "B.Tech",
        "Computer Science"
    ]
}


# ============================================================
# JOB DESCRIPTION
# ============================================================

JD_TEXT = """
Java Developer Intern

Company: Harsham Group
Location: Hyderabad, Telangana
Duration: 6 months

Requirements:

B.Tech/B.E in Computer Science or related field.

Required Skills:
Core Java
Collections
Multithreading
Exception Handling
OOP
Spring Boot
Spring MVC
Hibernate
JPA
SQL
Database Design
JUnit
Mockito

Good to have:
REST APIs
Microservices
Git
GitHub
Docker
AWS
Agile

Responsibilities:
Develop Java applications.
Build REST APIs using Spring Boot.
Work with SQL databases.
Debug and test applications.
Collaborate with the development team.
"""


# ============================================================
# STEP 1 — JD ANALYZER
# ============================================================

def analyze_jd():

    result = run_jd_tool({
        "jd_text": JD_TEXT
    })

    if not isinstance(result, dict):
        return {
            "status": "ERROR",
            "message": "JD Analyzer returned invalid output"
        }

    if result.get("status") != "OK":
        return {
            "status": "ERROR",
            "stage": "JD Analyzer",
            "message": result
        }

    return result


# ============================================================
# STEP 2 — RESUME-JD MATCHER
# ============================================================

def match_resume(jd_result):

    result = match_resume_with_jd(
        jd_result,
        STUDENT_PROFILE
    )

    if not isinstance(result, dict):
        return {
            "status": "ERROR",
            "message": "Resume-JD Matcher returned invalid output"
        }

    if result.get("status") != "OK":
        return {
            "status": "ERROR",
            "stage": "Resume-JD Matcher",
            "message": result
        }

    return result


# ============================================================
# STEP 3 — SKILL GAP
# ============================================================

def analyze_gaps(matcher_result):

    result = analyze_skill_gaps(
        matcher_result
    )

    if not isinstance(result, dict):
        return {
            "status": "ERROR",
            "message": "Skill Gap Analyzer returned invalid output"
        }

    if result.get("status") != "OK":
        return {
            "status": "ERROR",
            "stage": "Skill Gap Analyzer",
            "message": result
        }

    return result


# ============================================================
# STEP 4 — LEARNING PLAN
# ============================================================

def create_learning_plan(skill_gap_result):

    result = build_learning_plan(
        skill_gap_result
    )

    if not isinstance(result, dict):
        return {
            "status": "ERROR",
            "message": "Learning Resource Finder returned invalid output"
        }

    if result.get("status") != "OK":
        return {
            "status": "ERROR",
            "stage": "Learning Resource Finder",
            "message": result
        }

    return result


# ============================================================
# COMPLETE PIPELINE
# ============================================================

def run_placement_pipeline():

    # --------------------------------------------------------
    # 1. JD Analyzer
    # --------------------------------------------------------

    print("\n[1/4] Running JD Analyzer...")

    jd_result = analyze_jd()

    if jd_result.get("status") != "OK":
        return jd_result

    print("JD Analyzer: OK")


    # --------------------------------------------------------
    # 2. Resume-JD Matcher
    # --------------------------------------------------------

    print("\n[2/4] Running Resume-JD Matcher...")

    matcher_result = match_resume(
        jd_result
    )

    if matcher_result.get("status") != "OK":
        return matcher_result

    print("Resume-JD Matcher: OK")


    # --------------------------------------------------------
    # 3. Skill Gap Analyzer
    # --------------------------------------------------------

    print("\n[3/4] Running Skill Gap Analyzer...")

    skill_gap_result = analyze_gaps(
        matcher_result
    )

    if skill_gap_result.get("status") != "OK":
        return skill_gap_result

    print("Skill Gap Analyzer: OK")


    # --------------------------------------------------------
    # 4. Learning Resource Finder
    # --------------------------------------------------------

    print("\n[4/4] Building Learning Plan...")

    learning_result = create_learning_plan(
        skill_gap_result
    )

    if learning_result.get("status") != "OK":
        return learning_result

    print("Learning Resource Finder: OK")


    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    final_report = {

        "status": "OK",

        "student": STUDENT_PROFILE.get(
            "name"
        ),

        "job": matcher_result.get(
            "job"
        ),

        "match": matcher_result.get(
            "match"
        ),

        "qualification": matcher_result.get(
            "qualification"
        ),

        "matched_skills": {
            "required": matcher_result
                .get("required_skills", {})
                .get("matched_skills", []),

            "preferred": matcher_result
                .get("preferred_skills", {})
                .get("matched_skills", [])
        },

        "skill_gaps": skill_gap_result.get(
            "skill_gaps",
            []
        ),

        "learning_plan": learning_result.get(
            "learning_plan",
            []
        )
    }

    return final_report


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    result = run_placement_pipeline()

    print("\n")
    print("=" * 70)
    print("FINAL PLACEMENT ADVISOR REPORT")
    print("=" * 70)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )