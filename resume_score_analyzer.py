# ============================================================
# RESUME SCORE ANALYZER
# ============================================================

def calculate_resume_score(resume_data):

    if not resume_data or resume_data.get("status") != "OK":
        return {
            "status": "ERROR",
            "message": "Invalid resume data"
        }

    student = resume_data.get("student", {})

    name = student.get("name")
    contact = student.get("contact", {})
    skills = student.get("skills", [])
    qualifications = student.get("qualifications", [])
    projects = student.get("projects", [])
    experience = student.get("experience", [])
    certifications = student.get("certifications", [])
    achievements = student.get("achievements", [])

    score = 0
    breakdown = {}
    suggestions = []

    # ========================================================
    # 1. NAME — 5 POINTS
    # ========================================================

    if name:
        breakdown["name"] = 5
        score += 5
    else:
        breakdown["name"] = 0
        suggestions.append("Add your full name.")

    # ========================================================
    # 2. CONTACT — 5 POINTS
    # ========================================================

    contact_score = 0

    if contact.get("email"):
        contact_score += 2

    if contact.get("phone"):
        contact_score += 1

    if contact.get("linkedin"):
        contact_score += 1

    if contact.get("github"):
        contact_score += 1

    breakdown["contact"] = contact_score
    score += contact_score

    if not contact.get("email"):
        suggestions.append("Add a professional email address.")

    if not contact.get("phone"):
        suggestions.append("Add your phone number.")

    if not contact.get("linkedin"):
        suggestions.append("Add your LinkedIn profile.")

    if not contact.get("github"):
        suggestions.append("Add your GitHub profile.")

    # ========================================================
    # 3. SKILLS — 20 POINTS
    # ========================================================

    skill_count = len(skills)

    if skill_count >= 8:
        skill_score = 20

    elif skill_count >= 5:
        skill_score = 16

    elif skill_count >= 3:
        skill_score = 12

    elif skill_count >= 1:
        skill_score = 8

    else:
        skill_score = 0
        suggestions.append("Add relevant technical skills.")

    breakdown["skills"] = skill_score
    score += skill_score

    # ========================================================
    # 4. EDUCATION — 15 POINTS
    # ========================================================

    if qualifications:
        breakdown["education"] = 15
        score += 15

    else:
        breakdown["education"] = 0
        suggestions.append("Add your educational qualification.")

    # ========================================================
    # 5. PROJECTS — 20 POINTS
    # ========================================================

    project_count = len(projects)

    if project_count >= 3:
        project_score = 20

    elif project_count == 2:
        project_score = 15

    elif project_count == 1:
        project_score = 8

    else:
        project_score = 0
        suggestions.append(
            "Add relevant projects with detailed descriptions."
        )

    breakdown["projects"] = project_score
    score += project_score

    # ========================================================
    # 6. EXPERIENCE — 15 POINTS
    # ========================================================

    if experience:
        breakdown["experience"] = 15
        score += 15

    else:
        breakdown["experience"] = 0
        suggestions.append(
            "Add internship or work experience if applicable."
        )

    # ========================================================
    # 7. CERTIFICATIONS — 5 POINTS
    # ========================================================

    certification_count = len(certifications)

    if certification_count >= 2:
        certification_score = 5

    elif certification_count == 1:
        certification_score = 3

    else:
        certification_score = 0
        suggestions.append(
            "Add relevant certifications if you have any."
        )

    breakdown["certifications"] = certification_score
    score += certification_score

    # ========================================================
    # 8. ACHIEVEMENTS — 15 POINTS
    # ========================================================

    achievement_count = len(achievements)

    if achievement_count >= 2:
        achievement_score = 15

    elif achievement_count == 1:
        achievement_score = 8

    else:
        achievement_score = 0
        suggestions.append(
            "Add relevant achievements, hackathons, "
            "competitive programming, or awards."
        )

    breakdown["achievements"] = achievement_score
    score += achievement_score

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {
        "status": "OK",
        "score": score,
        "max_score": 100,
        "breakdown": breakdown,
        "suggestions": suggestions
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    sample_resume_data = {

        "status": "OK",

        "student": {

            "name": "Gautam Singh",

            "contact": {
                "email": "gautam@example.com",
                "phone": "9876543210",
                "linkedin": "linkedin.com/in/gautamsingh",
                "github": "github.com/gautamsingh"
            },

            "skills": [
                "Java",
                "Python",
                "C++",
                "SQL",
                "Django",
                "Git",
                "GitHub",
                "Azure",
                "AI",
                "OOP"
            ],

            "qualifications": [
                "B.Tech",
                "Computer Science"
            ],

            "projects": [
                "Smart Parking System",
                "AI Crime Hotspot Detection",
                "Instagram Clone using Django"
            ],

            "experience": [
                "Software Developer Intern",
                "ABC Technologies",
                "June 2026 - July 2026",
                "Worked on Java and SQL based applications."
            ],

            "certifications": [
                "Google AI Essentials",
                "Microsoft Azure Fundamentals"
            ],

            "achievements": [
                "Participated in hackathon",
                "Solved coding problems on LeetCode"
            ]
        }
    }

    result = calculate_resume_score(sample_resume_data)

    import json

    print(json.dumps(result, indent=2))