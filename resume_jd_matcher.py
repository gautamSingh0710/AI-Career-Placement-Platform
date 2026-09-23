"""
Resume-JD Matcher for StudentCareerAgent.

Purpose:
Compare structured Job Description requirements with
student resume/profile skills.

The matcher is deterministic.
It does NOT use an LLM to invent a match percentage.

Flow:

JD Analyzer
    ↓
Structured JD
    ↓
Student Resume/Profile
    ↓
Resume-JD Matcher
    ↓
Matched Skills
Missing Skills
Preferred Skills
Qualification Match
Match Percentage
"""

import re
import json


# ============================================================
# SKILL NORMALIZATION
# ============================================================

SKILL_NORMALIZATION = {

    # Programming Languages
    "java": "Java",
    "core java": "Java",

    "python": "Python",

    "c++": "C++",
    "cpp": "C++",

    "c#": "C#",

    "javascript": "JavaScript",
    "js": "JavaScript",

    "typescript": "TypeScript",
    "ts": "TypeScript",

    # Database / Web
    "sql": "SQL",

    "html": "HTML",
    "css": "CSS",

    # Java Frameworks
    "spring": "Spring",
    "spring framework": "Spring",

    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",

    "spring mvc": "Spring MVC",
    "springmvc": "Spring MVC",

    "hibernate": "Hibernate",
    "hibernate orm": "Hibernate",

    "jpa": "JPA",

    # Python Frameworks
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",

    # Frontend
    "react": "React",
    "reactjs": "React",

    "angular": "Angular",
    "angularjs": "Angular",

    "vue": "Vue",
    "vuejs": "Vue",

    # Backend
    "node.js": "Node.js",
    "nodejs": "Node.js",

    "express": "Express",
    "express.js": "Express",

    # APIs / Architecture
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful api": "REST APIs",
    "restful apis": "REST APIs",

    "microservices": "Microservices",
    "microservice": "Microservices",

    "graphql": "GraphQL",

    # Databases
    "mysql": "MySQL",

    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",

    "mongodb": "MongoDB",

    "nosql": "NoSQL",

    "database design": "Database Design",
    "database management": "Database Management",
    "dbms": "DBMS",

    # Version Control
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",

    # DevOps / Cloud
    "docker": "Docker",
    "kubernetes": "Kubernetes",

    "aws": "AWS",
    "azure": "Azure",
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",

    "linux": "Linux",

    # Testing
    "junit": "JUnit",
    "mockito": "Mockito",

    "unit testing": "Unit Testing",
    "integration testing": "Integration Testing",

    "selenium": "Selenium",

    # DSA
    "data structures": "Data Structures",
    "data structure": "Data Structures",

    "algorithms": "Algorithms",
    "algorithm": "Algorithms",

    "dsa": "DSA",

    # Programming Concepts
    "oop": "OOP",
    "object oriented programming": "OOP",
    "object-oriented programming": "OOP",

    "collections": "Collections",
    "java collections": "Collections",

    "multithreading": "Multithreading",
    "multi-threading": "Multithreading",
    "multi threading": "Multithreading",

    "exception handling": "Exception Handling",

    # Other Technical Skills
    "system design": "System Design",

    "debugging": "Debugging",

    # Methodologies
    "agile": "Agile",
    "scrum": "Scrum",

    # AI / ML
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",

    "artificial intelligence": "Artificial Intelligence",
    "ai": "Artificial Intelligence",

    "pandas": "Pandas",
    "numpy": "NumPy",

    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",

    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
}


# ============================================================
# NORMALIZE SKILL
# ============================================================

def normalize_skill(skill):
    """
    Convert different representations of the same skill
    into one canonical name.
    """

    if not isinstance(skill, str):
        return None

    cleaned = skill.strip().lower()

    cleaned = re.sub(r"\s+", " ", cleaned)

    return SKILL_NORMALIZATION.get(
        cleaned,
        skill.strip()
    )


# ============================================================
# NORMALIZE SKILL LIST
# ============================================================

def normalize_skill_list(skills):
    """
    Normalize and remove duplicate skills.
    """

    if not isinstance(skills, list):
        return []

    result = []

    for skill in skills:

        normalized = normalize_skill(skill)

        if normalized and normalized not in result:
            result.append(normalized)

    return result


# ============================================================
# REMOVE REDUNDANT SKILLS
# ============================================================

def remove_redundant_skills(skills):
    """
    Remove generic skills when a more specific skill
    already represents the same requirement.

    Example:

        Spring Boot + Spring

    becomes:

        Spring Boot
    """

    skills = normalize_skill_list(skills)

    skill_set = set(skills)

    redundant = set()

    # Spring Boot already implies generic Spring framework
    if "Spring Boot" in skill_set and "Spring" in skill_set:
        redundant.add("Spring")

    # Spring MVC is kept separately because a JD may
    # explicitly require it.

    return [
        skill
        for skill in skills
        if skill not in redundant
    ]


# ============================================================
# QUALIFICATION NORMALIZATION
# ============================================================

def normalize_qualification(value):
    """
    Normalize qualification text.

    Examples:

        B.Tech -> b tech
        B.Tech. -> b tech
        BTech -> b tech
        B.Tech CSE -> b tech cse
        B.Tech in Computer Science -> b tech in computer science
        B.E. -> b e
        B.E CSE -> b e cse
        Bachelor of Technology -> bachelor of technology
    """

    if not isinstance(value, str):
        return ""

    value = value.lower().strip()

    # --------------------------------------------------------
    # Common degree spellings
    # --------------------------------------------------------

    value = value.replace("b.tech.", "b tech")
    value = value.replace("b.tech", "b tech")
    value = value.replace("btech", "b tech")

    value = value.replace("b.e.", "b e")
    value = value.replace("b.e", "b e")

    value = value.replace("m.c.a.", "mca")
    value = value.replace("m.c.a", "mca")

    # --------------------------------------------------------
    # Punctuation
    # --------------------------------------------------------

    value = value.replace(".", "")
    value = value.replace(",", " ")
    value = value.replace("-", " ")

    # --------------------------------------------------------
    # Normalize whitespace
    # --------------------------------------------------------

    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ============================================================
# DEGREE CATEGORY
# ============================================================

def get_degree_category(value):
    """
    Identify the degree even when specialization is included.

    Examples:

        B.Tech
        B.Tech CSE
        B.Tech Computer Science
        B.Tech in Computer Science

    -> BACHELOR_TECH
    """

    value = normalize_qualification(value)

    # --------------------------------------------------------
    # B.Tech / Bachelor of Technology
    # --------------------------------------------------------

    if (
        value == "b tech"
        or value.startswith("b tech ")
        or value.startswith("bachelor of technology")
        or value.startswith("bachelor technology")
    ):
        return "BACHELOR_TECH"

    # --------------------------------------------------------
    # B.E / Bachelor of Engineering
    # --------------------------------------------------------

    if (
        value == "b e"
        or value.startswith("b e ")
        or value.startswith("bachelor of engineering")
        or value.startswith("bachelor engineering")
    ):
        return "BACHELOR_ENGINEERING"

    # --------------------------------------------------------
    # MCA
    # --------------------------------------------------------

    if (
        value == "mca"
        or value.startswith("mca ")
        or value.startswith("master of computer applications")
    ):
        return "MCA"

    return "OTHER"


# ============================================================
# DEGREE EQUIVALENCE
# ============================================================

def are_degrees_equivalent(
    student_degree,
    jd_degree
):
    """
    Determine whether student's degree satisfies
    the JD degree requirement.

    B.Tech and B.E are treated as equivalent
    engineering bachelor's degrees.

    MCA is NOT treated as equivalent to B.Tech/B.E.
    """

    # Exact match
    if student_degree == jd_degree:
        return True

    # B.Tech <-> B.E equivalence
    engineering_degrees = {
        "BACHELOR_TECH",
        "BACHELOR_ENGINEERING"
    }

    if (
        student_degree in engineering_degrees
        and jd_degree in engineering_degrees
    ):
        return True

    return False


# ============================================================
# QUALIFICATION MATCH
# ============================================================

def check_qualification_match(
    jd_qualifications,
    student_qualifications
):
    """
    Compare JD qualifications with student qualifications.

    Degree alternatives:

        B.Tech / B.E

    are treated as equivalent.

    MCA remains a separate degree.

    Example:

        JD:
            B.Tech

        Student:
            B.E

        Result:
            MATCHED
    """

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not isinstance(jd_qualifications, list):
        jd_qualifications = []

    if not isinstance(student_qualifications, list):
        student_qualifications = []

    # --------------------------------------------------------
    # No qualification requirement
    # --------------------------------------------------------

    if not jd_qualifications:

        return {
            "status": "NOT_SPECIFIED",
            "matched": [],
            "missing": [],
            "match_percentage": 100
        }

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    jd_normalized = []

    for qualification in jd_qualifications:

        normalized = normalize_qualification(
            qualification
        )

        if normalized and normalized not in jd_normalized:
            jd_normalized.append(normalized)

    student_normalized = []

    for qualification in student_qualifications:

        normalized = normalize_qualification(
            qualification
        )

        if normalized and normalized not in student_normalized:
            student_normalized.append(normalized)

    matched = []
    missing = []

    # --------------------------------------------------------
    # Find degree categories
    # --------------------------------------------------------

    jd_degree_items = []

    for qualification in jd_normalized:

        category = get_degree_category(
            qualification
        )

        if category != "OTHER":

            jd_degree_items.append({
                "qualification": qualification,
                "category": category
            })

    student_degree_items = []

    for qualification in student_normalized:

        category = get_degree_category(
            qualification
        )

        if category != "OTHER":

            student_degree_items.append({
                "qualification": qualification,
                "category": category
            })

    # --------------------------------------------------------
    # Degree requirement
    # --------------------------------------------------------

    degree_requirement_present = bool(
        jd_degree_items
    )

    degree_matched = False
    matched_jd_degree = None

    if degree_requirement_present:

        for jd_degree_item in jd_degree_items:

            jd_category = jd_degree_item["category"]

            for student_degree_item in student_degree_items:

                student_category = (
                    student_degree_item["category"]
                )

                if are_degrees_equivalent(
                    student_category,
                    jd_category
                ):

                    degree_matched = True

                    matched_jd_degree = (
                        jd_degree_item["qualification"]
                    )

                    break

            if degree_matched:
                break

    # --------------------------------------------------------
    # Add degree result
    #
    # IMPORTANT:
    #
    # All degree alternatives are ONE logical
    # requirement.
    #
    # Therefore:
    #
    # JD = B.Tech + B.E
    #
    # does NOT become two requirements.
    # --------------------------------------------------------

    if degree_requirement_present:

        if degree_matched:

            matched.append(
                matched_jd_degree
            )

        else:

            # Only one logical degree requirement
            # is missing.
            missing.append(
                jd_degree_items[0]["qualification"]
            )

    # --------------------------------------------------------
    # Check remaining non-degree qualifications
    # --------------------------------------------------------

    for jd_qualification in jd_normalized:

        jd_value = normalize_qualification(
            jd_qualification
        )

        if not jd_value:
            continue

        # Degree requirements already handled above.
        if get_degree_category(jd_value) != "OTHER":
            continue

        found = False

        for student_value in student_normalized:

            # ------------------------------------------------
            # Exact match
            # ------------------------------------------------

            if jd_value == student_value:

                found = True
                break

            # ------------------------------------------------
            # Computer Science / CSE
            # ------------------------------------------------

            if (
                "computer science" in jd_value
                and (
                    "computer science" in student_value
                    or student_value == "cse"
                )
            ):

                found = True
                break

            # ------------------------------------------------
            # Information Technology / IT
            # ------------------------------------------------

            if (
                "information technology" in jd_value
                and (
                    "information technology" in student_value
                    or student_value == "it"
                )
            ):

                found = True
                break

        if found:

            matched.append(
                jd_qualification
            )

        else:

            missing.append(
                jd_qualification
            )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    matched = list(
        dict.fromkeys(matched)
    )

    missing = list(
        dict.fromkeys(missing)
    )

    # --------------------------------------------------------
    # Remove anything accidentally present in both
    # --------------------------------------------------------

    matched_set = set(matched)

    missing = [
        item
        for item in missing
        if item not in matched_set
    ]

    # --------------------------------------------------------
    # Percentage
    #
    # Degree alternatives count as ONE requirement.
    # --------------------------------------------------------

    total_requirements = (
        len(matched)
        + len(missing)
    )

    if total_requirements == 0:

        percentage = 100

    else:

        percentage = round(
            len(matched)
            / total_requirements
            * 100
        )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if not missing:

        status = "MATCHED"

    elif matched:

        status = "PARTIAL_MATCH"

    else:

        status = "NOT_MATCHED"

    return {
        "status": status,
        "matched": matched,
        "missing": missing,
        "match_percentage": percentage
    }


# ============================================================
# SKILL COMPARISON
# ============================================================

def compare_skills(
    required_skills,
    preferred_skills,
    student_skills
):
    """
    Compare JD skills against student skills.

    Required skills and preferred skills are kept separate.
    """

    required_skills = remove_redundant_skills(
        required_skills
    )

    preferred_skills = remove_redundant_skills(
        preferred_skills
    )

    student_skills = normalize_skill_list(
        student_skills
    )

    # --------------------------------------------------------
    # Required skills
    # --------------------------------------------------------

    matched_required = []
    missing_required = []

    for skill in required_skills:

        if skill in student_skills:

            matched_required.append(skill)

        else:

            missing_required.append(skill)

    # --------------------------------------------------------
    # Preferred skills
    # --------------------------------------------------------

    matched_preferred = []
    missing_preferred = []

    for skill in preferred_skills:

        if skill in student_skills:

            matched_preferred.append(skill)

        else:

            missing_preferred.append(skill)

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    return {

        "matched_required_skills":
            matched_required,

        "missing_required_skills":
            missing_required,

        "matched_preferred_skills":
            matched_preferred,

        "missing_preferred_skills":
            missing_preferred,

        "required_total":
            len(required_skills),

        "required_matched":
            len(matched_required),

        "preferred_total":
            len(preferred_skills),

        "preferred_matched":
            len(matched_preferred)
    }


# ============================================================
# MATCH PERCENTAGE
# ============================================================

def calculate_match_percentage(
    required_total,
    required_matched,
    preferred_total,
    preferred_matched
):
    """
    Calculate deterministic match percentage.

    Required skills = 80%
    Preferred skills = 20%

    If only one section exists,
    that section receives 100% weight.
    """

    required_score = None
    preferred_score = None

    # --------------------------------------------------------
    # Required score
    # --------------------------------------------------------

    if required_total > 0:

        required_score = (
            required_matched
            / required_total
        )

    # --------------------------------------------------------
    # Preferred score
    # --------------------------------------------------------

    if preferred_total > 0:

        preferred_score = (
            preferred_matched
            / preferred_total
        )

    # --------------------------------------------------------
    # Only required skills
    # --------------------------------------------------------

    if (
        required_score is not None
        and preferred_score is None
    ):

        return round(
            required_score * 100
        )

    # --------------------------------------------------------
    # Only preferred skills
    # --------------------------------------------------------

    if (
        required_score is None
        and preferred_score is not None
    ):

        return round(
            preferred_score * 100
        )

    # --------------------------------------------------------
    # Nothing exists
    # --------------------------------------------------------

    if (
        required_score is None
        and preferred_score is None
    ):

        return 0

    # --------------------------------------------------------
    # Both exist
    # --------------------------------------------------------

    score = (
        required_score * 0.80
        + preferred_score * 0.20
    )

    return round(
        score * 100
    )


# ============================================================
# MATCH LEVEL
# ============================================================

def get_match_level(match_percentage):
    """
    Convert numeric skill coverage percentage
    into a descriptive category.
    """

    if match_percentage >= 80:
        return "Strong Match"

    if match_percentage >= 60:
        return "Moderate Match"

    if match_percentage >= 40:
        return "Partial Match"

    return "Low Match"


# ============================================================
# SKILL GAP PRIORITY
# ============================================================

def get_skill_priority(
    skill,
    required_skills,
    preferred_skills
):
    """
    Required skills = High priority.
    Preferred skills = Medium priority.
    """

    if skill in required_skills:

        return "High"

    if skill in preferred_skills:

        return "Medium"

    return "Low"


# ============================================================
# BUILD SKILL GAPS
# ============================================================

def build_skill_gaps(
    missing_required_skills,
    missing_preferred_skills,
    required_skills,
    preferred_skills
):
    """
    Create structured skill-gap information.

    This output can later be consumed by
    the Skill Gap Analyzer.
    """

    gaps = []

    # --------------------------------------------------------
    # Required gaps
    # --------------------------------------------------------

    for skill in missing_required_skills:

        gaps.append({

            "skill": skill,

            "status": "Missing",

            "priority": get_skill_priority(
                skill,
                required_skills,
                preferred_skills
            ),

            "type": "Required",

            "reason":
                "Required by the job description"
        })

    # --------------------------------------------------------
    # Preferred gaps
    # --------------------------------------------------------

    for skill in missing_preferred_skills:

        gaps.append({

            "skill": skill,

            "status": "Missing",

            "priority": get_skill_priority(
                skill,
                required_skills,
                preferred_skills
            ),

            "type": "Preferred",

            "reason":
                "Listed as preferred / good to have"
        })

    return gaps


# ============================================================
# MAIN MATCHER
# ============================================================

def match_resume_with_jd(
    jd_data,
    student_profile
):
    """
    Compare structured JD data with student profile.

    Expected JD:

    {
        "job_title": "...",
        "company": "...",
        "required_skills": [...],
        "preferred_skills": [...],
        "qualifications": [...]
    }

    Expected student profile:

    {
        "name": "...",
        "skills": [...],
        "qualifications": [...]
    }
    """

    # ========================================================
    # VALIDATE INPUT
    # ========================================================

    if not isinstance(jd_data, dict):

        return {
            "status": "INVALID_INPUT",
            "error":
                "jd_data must be an object"
        }

    if not isinstance(student_profile, dict):

        return {
            "status": "INVALID_INPUT",
            "error":
                "student_profile must be an object"
        }

    # ========================================================
    # EXTRACT JD
    # ========================================================

    job_title = jd_data.get(
        "job_title"
    )

    company = jd_data.get(
        "company"
    )

    required_skills = jd_data.get(
        "required_skills",
        []
    )

    preferred_skills = jd_data.get(
        "preferred_skills",
        []
    )

    jd_qualifications = jd_data.get(
        "qualifications",
        []
    )

    # ========================================================
    # EXTRACT STUDENT
    # ========================================================

    student_name = student_profile.get(
        "name"
    )

    student_skills = student_profile.get(
        "skills",
        []
    )

    student_qualifications = student_profile.get(
        "qualifications",
        []
    )

    # ========================================================
    # COMPARE SKILLS
    # ========================================================

    skill_result = compare_skills(
        required_skills,
        preferred_skills,
        student_skills
    )

    # ========================================================
    # QUALIFICATION MATCH
    # ========================================================

    qualification_result = (
        check_qualification_match(
            jd_qualifications,
            student_qualifications
        )
    )

    # ========================================================
    # MATCH PERCENTAGE
    # ========================================================

    match_percentage = (
        calculate_match_percentage(
            skill_result["required_total"],
            skill_result["required_matched"],
            skill_result["preferred_total"],
            skill_result["preferred_matched"]
        )
    )

    match_level = get_match_level(
        match_percentage
    )

    # ========================================================
    # NORMALIZED SKILLS
    # ========================================================

    normalized_required = (
        remove_redundant_skills(
            required_skills
        )
    )

    normalized_preferred = (
        remove_redundant_skills(
            preferred_skills
        )
    )

    # ========================================================
    # SKILL GAPS
    # ========================================================

    skill_gaps = build_skill_gaps(

        skill_result[
            "missing_required_skills"
        ],

        skill_result[
            "missing_preferred_skills"
        ],

        normalized_required,

        normalized_preferred
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "status": "OK",

        "student": student_name,

        "job": {

            "title": job_title,

            "company": company
        },

        "match": {

            "percentage":
                match_percentage,

            "level":
                match_level
        },

        "required_skills": {

            "total":
                skill_result[
                    "required_total"
                ],

            "matched":
                skill_result[
                    "required_matched"
                ],

            "matched_skills":
                skill_result[
                    "matched_required_skills"
                ],

            "missing_skills":
                skill_result[
                    "missing_required_skills"
                ]
        },

        "preferred_skills": {

            "total":
                skill_result[
                    "preferred_total"
                ],

            "matched":
                skill_result[
                    "preferred_matched"
                ],

            "matched_skills":
                skill_result[
                    "matched_preferred_skills"
                ],

            "missing_skills":
                skill_result[
                    "missing_preferred_skills"
                ]
        },

        "qualification":
            qualification_result,

        "skill_gaps":
            skill_gaps
    }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # SAMPLE JD ANALYZER OUTPUT
    # ========================================================

    jd_data = {

        "status": "OK",

        "job_title":
            "Java Developer Intern",

        "company":
            "Harsham Group",

        "location":
            "Hyderabad, Telangana",

        "experience":
            "Entry-level / Internship",

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
    # SAMPLE STUDENT PROFILE
    # ========================================================

    student_profile = {

        "name":
            "Gautam Singh",

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

            "B.E",
            "Computer Science"
        ]
    }

    # ========================================================
    # RUN MATCHER
    # ========================================================

    result = match_resume_with_jd(
        jd_data,
        student_profile
    )

    # ========================================================
    # PRINT RESULT
    # ========================================================

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )