import json


def generate_learning_plan(skill_gap_result):

    if not skill_gap_result or skill_gap_result.get("status") != "OK":
        return {
            "status": "ERROR",
            "message": "Invalid Skill Gap Analyzer result"
        }

    student = skill_gap_result.get("student")
    job = skill_gap_result.get("job", {})
    skill_gaps = skill_gap_result.get("skill_gaps", [])

    high_priority = []
    medium_priority = []

    for gap in skill_gaps:

        if gap.get("priority") == "High":
            high_priority.append(gap)

        elif gap.get("priority") == "Medium":
            medium_priority.append(gap)

    learning_plan = []

    # Required skills first
    for index, gap in enumerate(high_priority, start=1):

        skill = gap.get("skill")

        learning_plan.append({
            "step": index,
            "skill": skill,
            "priority": "High",
            "type": "Required",
            "action": "Learn concepts, practice coding and build a small example"
        })

    # Preferred skills after required skills
    start_step = len(learning_plan) + 1

    for index, gap in enumerate(medium_priority, start=start_step):

        skill = gap.get("skill")

        learning_plan.append({
            "step": index,
            "skill": skill,
            "priority": "Medium",
            "type": "Preferred",
            "action": "Learn after completing required skills"
        })

    return {
        "status": "OK",

        "student": student,

        "job": {
            "title": job.get("title"),
            "company": job.get("company")
        },

        "summary": {
            "total_skills_to_learn": len(learning_plan),
            "required_skills": len(high_priority),
            "preferred_skills": len(medium_priority)
        },

        "learning_plan": learning_plan
    }


if __name__ == "__main__":

    test_skill_gap_result = {
        "status": "OK",

        "student": "Gautam Singh",

        "job": {
            "title": "Java Developer Intern",
            "company": "Harsham Group"
        },

        "skill_gaps": [
            {
                "skill": "Collections",
                "priority": "High",
                "type": "Required"
            },
            {
                "skill": "Multithreading",
                "priority": "High",
                "type": "Required"
            },
            {
                "skill": "Exception Handling",
                "priority": "High",
                "type": "Required"
            },
            {
                "skill": "Spring Boot",
                "priority": "High",
                "type": "Required"
            },
            {
                "skill": "Spring MVC",
                "priority": "High",
                "type": "Required"
            },
            {
                "skill": "Hibernate",
                "priority": "High",
                "type": "Required"
            },
            {
                "skill": "JPA",
                "priority": "High",
                "type": "Required"
            },
            {
                "skill": "Database Design",
                "priority": "High",
                "type": "Required"
            },
            {
                "skill": "JUnit",
                "priority": "High",
                "type": "Required"
            },
            {
                "skill": "Mockito",
                "priority": "High",
                "type": "Required"
            },
            {
                "skill": "REST APIs",
                "priority": "Medium",
                "type": "Preferred"
            },
            {
                "skill": "Microservices",
                "priority": "Medium",
                "type": "Preferred"
            },
            {
                "skill": "Docker",
                "priority": "Medium",
                "type": "Preferred"
            },
            {
                "skill": "AWS",
                "priority": "Medium",
                "type": "Preferred"
            }
        ]
    }

    result = generate_learning_plan(test_skill_gap_result)

    print(json.dumps(result, indent=2))