import json

from learning_resources import get_learning_resources


def analyze_skill_gaps(matcher_result):

    if not matcher_result or matcher_result.get("status") != "OK":
        return {
            "status": "ERROR",
            "message": "Invalid Resume-JD Matcher result"
        }

    job = matcher_result.get("job", {})
    required = matcher_result.get("required_skills", {})
    preferred = matcher_result.get("preferred_skills", {})

    skill_gaps = []

    # Required skills
    for skill in required.get("missing_skills", []):

        skill_gaps.append({
            "skill": skill,
            "status": "Missing",
            "priority": "High",
            "type": "Required",
            "reason": "Required by the job description",
            "action": "Learn and practice before applying"
        })

    # Preferred skills
    for skill in preferred.get("missing_skills", []):

        skill_gaps.append({
            "skill": skill,
            "status": "Missing",
            "priority": "Medium",
            "type": "Preferred",
            "reason": "Listed as preferred / good to have",
            "action": "Learn after required skills"
        })

    matched_required = required.get("matched_skills", [])
    matched_preferred = preferred.get("matched_skills", [])

    # Get learning resources
    resource_result = get_learning_resources(skill_gaps)

    return {
        "status": "OK",

        "student": matcher_result.get("student"),

        "job": {
            "title": job.get("title"),
            "company": job.get("company")
        },

        "summary": {
            "total_gaps": len(skill_gaps),
            "high_priority": sum(
                1
                for gap in skill_gaps
                if gap["priority"] == "High"
            ),
            "medium_priority": sum(
                1
                for gap in skill_gaps
                if gap["priority"] == "Medium"
            )
        },

        "matched_skills": {
            "required": matched_required,
            "preferred": matched_preferred
        },

        "skill_gaps": skill_gaps,

        "learning_resources": resource_result.get(
            "resources",
            []
        )
    }


# Local test
if __name__ == "__main__":

    from resume_jd_matcher import match_resume_with_jd

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
            "Core Java",
            "Collections",
            "Multithreading",
            "Exception Handling",
            "OOP",
            "Spring Boot",
            "Spring MVC",
            "Hibernate",
            "JPA",
            "SQL",
            "Database Design",
            "JUnit",
            "Mockito"
        ],

        "preferred_skills": [
            "Microservices",
            "REST APIs",
            "GitHub",
            "Docker",
            "Git",
            "AWS"
        ]
    }

    student_profile = {

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

    # STEP 1
    matcher_result = match_resume_with_jd(
        jd_data,
        student_profile
    )

    # STEP 2
    result = analyze_skill_gaps(
        matcher_result
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )