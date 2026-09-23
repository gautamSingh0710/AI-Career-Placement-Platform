import json

from resume_parser import parse_resume
from resume_jd_matcher import match_resume_with_jd
from skill_gap_analyzer import analyze_skill_gaps
from learning_plan_generator import generate_learning_plan
from eligibility_checker import check_eligibility


def run_placement_agent():

    # ========================================================
    # STEP 1: READ RESUME
    # ========================================================

    resume_result = parse_resume("resume.pdf")

    if resume_result.get("status") != "OK":
        return resume_result

    student_profile = resume_result.get("student_profile")

    if not student_profile:
        return {
            "status": "ERROR",
            "message": "Student profile could not be extracted from resume"
        }

    # ========================================================
    # STEP 2: STRUCTURED JOB DESCRIPTION
    # ========================================================

    jd_data = {

        "status": "OK",

        "job_title": "Java Developer Intern",

        "company": "Harsham Group",

        "location": "Hyderabad, Telangana",

        "experience": "Entry-level / Internship",

        "qualifications": [
            "B.Tech",
            "B.E",
            "Computer Science"
        ],

        "required_skills": [
            "Java",
            "SQL",
            "Spring Boot",
            "Spring MVC",
            "Spring",
            "Hibernate",
            "JPA",
            "Database Design",
            "JUnit",
            "Mockito",
            "OOP",
            "Collections",
            "Multithreading",
            "Exception Handling"
        ],

        "preferred_skills": [
            "REST APIs",
            "Microservices",
            "Git",
            "GitHub",
            "Docker",
            "AWS",
            "Agile"
        ]
    }

    # ========================================================
    # STEP 3: RESUME + JD MATCHING
    # ========================================================

    matcher_result = match_resume_with_jd(
        jd_data,
        student_profile
    )

    if matcher_result.get("status") != "OK":
        return matcher_result

    # ========================================================
    # STEP 4: ELIGIBILITY CHECK
    # ========================================================

    eligibility_result = check_eligibility(
        matcher_result
    )

    if eligibility_result.get("status") != "OK":
        return eligibility_result

    # ========================================================
    # STEP 5: SKILL GAP ANALYSIS
    # ========================================================

    gap_result = analyze_skill_gaps(
        matcher_result
    )

    if gap_result.get("status") != "OK":
        return gap_result

    # ========================================================
    # STEP 6: LEARNING PLAN
    # ========================================================

    learning_result = generate_learning_plan(
        gap_result
    )

    if learning_result.get("status") != "OK":
        return learning_result

    # ========================================================
    # STEP 7: FINAL AGENT RESULT
    # ========================================================

    return {

        "status": "OK",

        "student_profile": {

            "name": student_profile.get("name"),

            "email": student_profile.get("email"),

            "phone": student_profile.get("phone"),

            "skills": student_profile.get("skills"),

            "qualifications": student_profile.get("qualifications"),

            "projects": student_profile.get("projects")
        },

        "job": matcher_result.get("job"),

        "match": matcher_result.get("match"),

        "eligibility": eligibility_result,

        "qualification": matcher_result.get("qualification"),

        "matched_skills": gap_result.get("matched_skills"),

        "skill_gaps": gap_result.get("skill_gaps"),

        "learning_resources": gap_result.get("learning_resources"),

        "learning_plan": learning_result.get("learning_plan")
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    result = run_placement_agent()

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )