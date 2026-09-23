"""
JD Matching and Skill Gap tools.

These tools compare a student's saved resume skills
against skills explicitly mentioned in a Job Description.

The calculation is deterministic.
The AI agent does not invent match percentages.
"""

import re

from azure.ai.projects.models import FunctionTool

from resume_tools import run_resume_tool


# ---------------------------------------------------------------------------
# SKILL CATALOG
# ---------------------------------------------------------------------------

SKILL_ALIASES = {
    "java": ["java"],
    "python": ["python"],
    "c++": ["c++", "cpp"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],

    "html": ["html", "html5"],
    "css": ["css", "css3"],

    "sql": ["sql"],
    "mysql": ["mysql"],
    "postgresql": ["postgresql", "postgres"],
    "mongodb": ["mongodb", "mongo db"],

    "dsa": [
        "data structures",
        "data structures and algorithms",
        "dsa",
        "algorithms",
    ],

    "oop": [
        "object oriented programming",
        "object-oriented programming",
        "oop",
    ],

    "spring boot": ["spring boot"],
    "spring": ["spring framework", "spring"],
    "django": ["django"],
    "flask": ["flask"],
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node js"],
    "express": ["express.js", "expressjs", "express js"],

    "git": ["git"],
    "github": ["github"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],

    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud"],

    "firebase": ["firebase", "firebase realtime database"],

    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": [
        "scikit-learn",
        "scikit learn",
        "sklearn",
    ],

    "machine learning": [
        "machine learning",
        "machine-learning",
    ],

    "deep learning": [
        "deep learning",
    ],

    "rest api": [
        "rest api",
        "restful api",
        "rest apis",
    ],

    "api": [
        "api",
        "apis",
    ],

    "linux": ["linux"],
    "cicd": [
        "ci/cd",
        "ci cd",
        "continuous integration",
        "continuous deployment",
    ],

    "communication": [
        "communication skills",
        "communication",
    ],

    "problem solving": [
        "problem solving",
        "problem-solving",
    ],
}


# ---------------------------------------------------------------------------
# LEARNING LINKS
# ---------------------------------------------------------------------------

LEARNING_LINKS = {
    "java": [
        {
            "title": "Java Programming - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=eIrMbAQSU34",
            "type": "YouTube",
        }
    ],

    "python": [
        {
            "title": "Python Full Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
            "type": "YouTube",
        }
    ],

    "c++": [
        {
            "title": "C++ Full Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=vLnPwxZdW4Y",
            "type": "YouTube",
        }
    ],

    "dsa": [
        {
            "title": "Data Structures and Algorithms - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=8hly31xKli0",
            "type": "YouTube",
        }
    ],

    "sql": [
        {
            "title": "SQL Tutorial - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=HXV3zeQKqGY",
            "type": "YouTube",
        }
    ],

    "javascript": [
        {
            "title": "JavaScript Full Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=PkZNo7MFNFg",
            "type": "YouTube",
        }
    ],

    "react": [
        {
            "title": "React Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=bMknfKXIFA8",
            "type": "YouTube",
        }
    ],

    "django": [
        {
            "title": "Django Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=F5mRW0jo-U4",
            "type": "YouTube",
        }
    ],

    "spring boot": [
        {
            "title": "Spring Boot Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=9SGDpanrc8U",
            "type": "YouTube",
        }
    ],

    "git": [
        {
            "title": "Git and GitHub Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=RGOj5yH7evk",
            "type": "YouTube",
        }
    ],

    "docker": [
        {
            "title": "Docker Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=3c-iBn73dDE",
            "type": "YouTube",
        }
    ],

    "aws": [
        {
            "title": "AWS Certified Cloud Practitioner - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=SOTamWNgDKc",
            "type": "YouTube",
        }
    ],

    "azure": [
        {
            "title": "Microsoft Learn - Azure",
            "url": "https://learn.microsoft.com/training/azure/",
            "type": "Microsoft Learn",
        }
    ],

    "pandas": [
        {
            "title": "Pandas Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=vmEHCJofslg",
            "type": "YouTube",
        }
    ],

    "numpy": [
        {
            "title": "NumPy Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=QUT1VHiLmmI",
            "type": "YouTube",
        }
    ],

    "machine learning": [
        {
            "title": "Machine Learning Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=NWONeJKn6kc",
            "type": "YouTube",
        }
    ],

    "mongodb": [
        {
            "title": "MongoDB Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=ofme2o29ngU",
            "type": "YouTube",
        }
    ],

    "rest api": [
        {
            "title": "REST API Tutorial - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=qbLc5a9jdXo",
            "type": "YouTube",
        }
    ],

    "linux": [
        {
            "title": "Linux Course - freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=sWbUDq4S6Y8",
            "type": "YouTube",
        }
    ],
}


# ---------------------------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------------------------

def normalize_text(text):
    if not isinstance(text, str):
        return ""

    text = text.lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")

    return text


def contains_skill(text, aliases):
    """
    Check whether one of the skill aliases occurs in the text.
    """

    text = normalize_text(text)

    for alias in aliases:
        alias = normalize_text(alias)

        if not alias:
            continue

        # For short terms such as "c++", "sql", "git", etc.
        # word boundaries are not always reliable, so use
        # controlled substring matching.
        if alias in text:
            return True

    return False


# ---------------------------------------------------------------------------
# EXTRACT SKILLS FROM JD
# ---------------------------------------------------------------------------

def extract_jd_skills(jd_text):
    """
    Extract skills from the JD using the controlled skill catalog.
    """

    found = []

    for canonical_skill, aliases in SKILL_ALIASES.items():

        if contains_skill(jd_text, aliases):
            found.append(canonical_skill)

    return sorted(found)


# ---------------------------------------------------------------------------
# GET SAVED RESUME SKILLS
# ---------------------------------------------------------------------------

def get_resume_skills():
    """
    Get skills from the saved resume tool.
    """

    result = run_resume_tool()

    if not isinstance(result, dict):
        return []

    student = result.get("student", {})

    if not isinstance(student, dict):
        return []

    skills = student.get("skills", [])

    if not isinstance(skills, list):
        return []

    return [str(skill).strip() for skill in skills if str(skill).strip()]


# ---------------------------------------------------------------------------
# NORMALIZE RESUME SKILL
# ---------------------------------------------------------------------------

def resume_has_skill(resume_skills, canonical_skill):
    """
    Determine whether the resume contains the canonical skill.
    """

    aliases = SKILL_ALIASES.get(
        canonical_skill,
        [canonical_skill],
    )

    for resume_skill in resume_skills:

        if contains_skill(
            resume_skill,
            aliases,
        ):
            return True

    return False


# ---------------------------------------------------------------------------
# MATCH JD
# ---------------------------------------------------------------------------

def match_jd(jd_text):
    """
    Compare JD skills with saved resume skills.
    """

    if not isinstance(jd_text, str) or not jd_text.strip():
        return {
            "status": "INVALID_INPUT",
            "error": "jd_text is required",
        }

    jd_text = jd_text.strip()

    required_skills = extract_jd_skills(jd_text)

    if not required_skills:
        return {
            "status": "NO_SKILLS_FOUND",
            "message": (
                "No skills from the supported skill catalog "
                "were found in the JD."
            ),
            "required_skills": [],
            "matched_skills": [],
            "missing_skills": [],
            "match_percentage": None,
        }

    resume_skills = get_resume_skills()

    matched = []
    missing = []

    for skill in required_skills:

        if resume_has_skill(
            resume_skills,
            skill,
        ):
            matched.append(skill)
        else:
            missing.append(skill)

    percentage = round(
        (len(matched) / len(required_skills)) * 100,
        2,
    )

    return {
        "status": "OK",
        "required_skills": required_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": percentage,
        "resume_skills": resume_skills,
    }


# ---------------------------------------------------------------------------
# SKILL GAP ANALYSIS
# ---------------------------------------------------------------------------

def skill_gap_analysis(jd_text):
    """
    Return missing skills and curated learning resources.
    """

    result = match_jd(jd_text)

    if result.get("status") != "OK":
        return result

    missing = result["missing_skills"]

    learning = {}

    for skill in missing:

        links = LEARNING_LINKS.get(
            skill,
            [],
        )

        learning[skill] = links

    return {
        "status": "OK",
        "match_percentage": result["match_percentage"],
        "required_skills": result["required_skills"],
        "matched_skills": result["matched_skills"],
        "missing_skills": missing,
        "learning_resources": learning,
    }


# ---------------------------------------------------------------------------
# FUNCTION TOOL: JD MATCH
# ---------------------------------------------------------------------------

MATCH_JD_TOOL = FunctionTool(
    name="match_jd",
    description=(
        "Compare a student's saved resume skills against skills found "
        "in a provided Job Description. Returns required skills, matched "
        "skills, missing skills and an exact match percentage. "
        "The percentage is calculated by the tool and must not be invented "
        "or changed by the agent."
    ),
    parameters={
        "type": "object",
        "properties": {
            "jd_text": {
                "type": "string",
                "description": "The complete Job Description.",
            }
        },
        "required": ["jd_text"],
        "additionalProperties": False,
    },
    strict=True,
)


# ---------------------------------------------------------------------------
# FUNCTION TOOL: SKILL GAPS
# ---------------------------------------------------------------------------

SKILL_GAP_TOOL = FunctionTool(
    name="skill_gap_analysis",
    description=(
        "Analyze the skills missing from a Job Description compared "
        "with the student's saved resume. Returns missing skills and "
        "curated learning resources. Do not invent learning URLs."
    ),
    parameters={
        "type": "object",
        "properties": {
            "jd_text": {
                "type": "string",
                "description": "The complete Job Description.",
            }
        },
        "required": ["jd_text"],
        "additionalProperties": False,
    },
    strict=True,
)


# ---------------------------------------------------------------------------
# TOOL LIST
# ---------------------------------------------------------------------------

JD_FUNCTION_TOOLS = [
    MATCH_JD_TOOL,
    SKILL_GAP_TOOL,
]


# ---------------------------------------------------------------------------
# DISPATCHER
# ---------------------------------------------------------------------------

def run_jd_tool(name, args):
    """
    Run JD-related tools.
    Always return a dictionary.
    """

    try:

        if name == "match_jd":

            jd_text = args.get("jd_text")

            return match_jd(jd_text)

        if name == "skill_gap_analysis":

            jd_text = args.get("jd_text")

            return skill_gap_analysis(jd_text)

        return {
            "status": "ERROR",
            "error": f"Unknown JD tool: {name}",
        }

    except Exception as exc:

        return {
            "status": "ERROR",
            "error": f"Tool failed: {type(exc).__name__}: {exc}",
        }