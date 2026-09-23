import json


def check_eligibility(matcher_result):
    """
    Determine whether a student satisfies the basic
    eligibility requirements of a job.

    Eligibility is based on:
    1. Qualification match
    2. Required skill coverage

    Match percentage is NOT used directly to decide eligibility.
    """

    # ========================================================
    # VALIDATE INPUT
    # ========================================================

    if not isinstance(matcher_result, dict):
        return {
            "status": "ERROR",
            "message": "matcher_result must be an object"
        }

    if matcher_result.get("status") != "OK":
        return {
            "status": "ERROR",
            "message": "Invalid Resume-JD Matcher result"
        }

    # ========================================================
    # GET DATA
    # ========================================================

    student = matcher_result.get("student")

    job = matcher_result.get(
        "job",
        {}
    )

    qualification = matcher_result.get(
        "qualification",
        {}
    )

    required_skills = matcher_result.get(
        "required_skills",
        {}
    )

    # ========================================================
    # QUALIFICATION CHECK
    # ========================================================

    qualification_status = qualification.get(
        "status"
    )

    qualification_matched = (
        qualification_status == "MATCHED"
        or qualification_status == "NOT_SPECIFIED"
    )

    # ========================================================
    # REQUIRED SKILL CHECK
    # ========================================================

    missing_required_skills = required_skills.get(
        "missing_skills",
        []
    )

    matched_required_skills = required_skills.get(
        "matched_skills",
        []
    )

    required_total = required_skills.get(
        "total",
        0
    )

    required_matched = required_skills.get(
        "matched",
        0
    )

    required_skills_complete = (
        len(missing_required_skills) == 0
    )

    # ========================================================
    # DETERMINE ELIGIBILITY
    # ========================================================

    eligible = (
        qualification_matched
        and required_skills_complete
    )

    # ========================================================
    # BUILD REASONS
    # ========================================================

    reasons = []

    if qualification_status == "MATCHED":

        reasons.append(
            "Qualification requirement is satisfied"
        )

    elif qualification_status == "NOT_SPECIFIED":

        reasons.append(
            "No qualification requirement was specified"
        )

    else:

        reasons.append(
            "Qualification requirement is not satisfied"
        )

    if required_skills_complete:

        reasons.append(
            "All required skills are matched"
        )

    else:

        reasons.append(
            "One or more required skills are missing"
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "status": "OK",

        "student": student,

        "job": {
            "title": job.get("title"),
            "company": job.get("company")
        },

        "eligible": eligible,

        "qualification": {

            "status": qualification_status,

            "matched": qualification.get(
                "matched",
                []
            ),

            "missing": qualification.get(
                "missing",
                []
            )
        },

        "required_skills": {

            "total": required_total,

            "matched": required_matched,

            "missing": missing_required_skills,

            "matched_skills": matched_required_skills
        },

        "reasons": reasons
    }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    test_result = {

        "status": "OK",

        "student": "Gautam Singh",

        "job": {

            "title": "Java Developer Intern",

            "company": "Harsham Group"
        },

        "qualification": {

            "status": "MATCHED",

            "matched": [
                "b tech",
                "computer science"
            ],

            "missing": []
        },

        "required_skills": {

            "total": 13,

            "matched": 3,

            "matched_skills": [
                "Java",
                "SQL",
                "OOP"
            ],

            "missing_skills": [
                "Spring Boot",
                "Spring MVC",
                "Hibernate",
                "JPA",
                "Database Design",
                "JUnit",
                "Mockito",
                "Collections",
                "Multithreading",
                "Exception Handling"
            ]
        }
    }

    result = check_eligibility(
        test_result
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )

