import re
import json
from pathlib import Path
from pypdf import PdfReader


# ============================================================
# SKILL KEYWORDS
# ============================================================

SKILL_KEYWORDS = {

    # Programming
    "Java": [
        "java",
        "core java"
    ],

    "Python": [
        "python"
    ],

    "C++": [
        "c++",
        "cpp"
    ],

    "C#": [
        "c#"
    ],

    "JavaScript": [
        "javascript",
        "java script"
    ],

    "TypeScript": [
        "typescript"
    ],

    # Database
    "SQL": [
        "sql",
        "structured query language"
    ],

    "MySQL": [
        "mysql"
    ],

    "PostgreSQL": [
        "postgresql",
        "postgres"
    ],

    "MongoDB": [
        "mongodb"
    ],

    # Java Frameworks
    "Spring Boot": [
        "spring boot",
        "springboot"
    ],

    "Spring MVC": [
        "spring mvc",
        "springmvc"
    ],

    "Spring": [
        "spring framework"
    ],

    "Hibernate": [
        "hibernate"
    ],

    "JPA": [
        "jpa",
        "jakarta persistence"
    ],

    # Python Frameworks
    "Django": [
        "django"
    ],

    "Flask": [
        "flask"
    ],

    "FastAPI": [
        "fastapi"
    ],

    # Frontend
    "React": [
        "react",
        "reactjs"
    ],

    "Angular": [
        "angular",
        "angularjs"
    ],

    "HTML": [
        "html"
    ],

    "CSS": [
        "css"
    ],

    # Backend
    "Node.js": [
        "node.js",
        "nodejs"
    ],

    "Express": [
        "express",
        "express.js"
    ],

    "REST APIs": [
        "rest api",
        "rest apis",
        "restful api",
        "restful apis"
    ],

    # Tools
    "Git": [
        "git"
    ],

    "GitHub": [
        "github"
    ],

    "Docker": [
        "docker"
    ],

    "Kubernetes": [
        "kubernetes"
    ],

    # Cloud
    "AWS": [
        "aws",
        "amazon web services"
    ],

    "Azure": [
        "azure"
    ],

    "Google Cloud": [
        "google cloud",
        "gcp"
    ],

    # Concepts
    "OOP": [
        "oop",
        "object oriented programming",
        "object-oriented programming"
    ],

    "Collections": [
        "collections",
        "java collections"
    ],

    "Multithreading": [
        "multithreading",
        "multi-threading",
        "multi threading"
    ],

    "Exception Handling": [
        "exception handling"
    ],

    "Data Structures": [
        "data structures",
        "data structure"
    ],

    "Algorithms": [
        "algorithms",
        "algorithm"
    ],

    "DSA": [
        "dsa"
    ],

    # Testing
    "JUnit": [
        "junit"
    ],

    "Mockito": [
        "mockito"
    ],

    # AI / ML
    "Machine Learning": [
        "machine learning"
    ],

    "Deep Learning": [
        "deep learning"
    ],

    "Artificial Intelligence": [
        "artificial intelligence"
    ],

    "Pandas": [
        "pandas"
    ],

    "NumPy": [
        "numpy"
    ],

    "Scikit-learn": [
        "scikit-learn",
        "sklearn"
    ]
}


# ============================================================
# READ PDF
# ============================================================

def extract_text_from_pdf(pdf_path):

    path = Path(pdf_path)

    if not path.exists():
        return {
            "status": "ERROR",
            "message": f"Resume file not found: {pdf_path}"
        }

    if path.suffix.lower() != ".pdf":
        return {
            "status": "ERROR",
            "message": "Resume must be a PDF file"
        }

    try:
        reader = PdfReader(str(path))

        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        text = "\n".join(pages)

        if not text.strip():
            return {
                "status": "ERROR",
                "message": "No readable text found in resume PDF"
            }

        return {
            "status": "OK",
            "text": text
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):

    text = text.replace("\u2022", " ")
    text = text.replace("", " ")

    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(r"[ \t]+", " ", text)

    return text


# ============================================================
# EXTRACT NAME
# ============================================================

def extract_name(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return "Unknown"

    for line in lines[:10]:

        cleaned = re.sub(
            r"[^A-Za-z ]",
            "",
            line
        ).strip()

        words = cleaned.split()

        if (
            2 <= len(words) <= 5
            and not any(
                keyword in line.lower()
                for keyword in [
                    "resume",
                    "curriculum",
                    "email",
                    "phone",
                    "linkedin",
                    "github",
                    "education"
                ]
            )
        ):
            return " ".join(words)

    return "Unknown"


# ============================================================
# EXTRACT EMAIL
# ============================================================

def extract_email(text):

    pattern = (
        r"[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    match = re.search(pattern, text)

    if match:
        return match.group(0)

    return None


# ============================================================
# EXTRACT PHONE
# ============================================================

def extract_phone(text):

    patterns = [
        r"\+91[\s-]?[6-9]\d{9}",
        r"\b[6-9]\d{9}\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(0)

    return None


# ============================================================
# EXTRACT SKILLS
# ============================================================

def extract_skills(text):

    text_lower = normalize_text(text).lower()

    found_skills = []

    for skill, keywords in SKILL_KEYWORDS.items():

        for keyword in keywords:

            keyword_lower = keyword.lower()

            if keyword_lower == "java":

                pattern = r"(?<![a-z0-9])java(?![a-z0-9])"

            elif keyword_lower == "git":

                pattern = r"(?<![a-z0-9])git(?!hub)(?![a-z0-9])"

            elif keyword_lower == "sql":

                pattern = r"(?<![a-z0-9])sql(?![a-z0-9])"

            elif keyword_lower == "react":

                pattern = r"(?<![a-z0-9])react(?![a-z0-9])"

            else:

                pattern = (
                    r"(?<!\w)"
                    + re.escape(keyword_lower)
                    + r"(?!\w)"
                )

            if re.search(
                pattern,
                text_lower
            ):
                found_skills.append(skill)
                break

    return found_skills


# ============================================================
# EXTRACT QUALIFICATIONS
# ============================================================

def extract_qualifications(text):

    text_lower = normalize_text(text).lower()

    qualifications = []

    # B.Tech
    if (
        re.search(r"\bb\.?\s*tech\b", text_lower)
        or re.search(r"\bbtech\b", text_lower)
        or re.search(
            r"\bbachelor\s+of\s+technology\b",
            text_lower
        )
    ):
        qualifications.append("B.Tech")

    # B.E.
    if (
        re.search(r"\bb\.?\s*e\.?\b", text_lower)
        or re.search(
            r"\bbachelor\s+of\s+engineering\b",
            text_lower
        )
    ):
        qualifications.append("B.E")

    # MCA
    if re.search(r"\bmca\b", text_lower):
        qualifications.append("MCA")

    # Computer Science
    if (
        re.search(
            r"\bcomputer\s+science\b",
            text_lower
        )
        or re.search(r"\bcse\b", text_lower)
    ):
        qualifications.append("Computer Science")

    return list(dict.fromkeys(qualifications))


# ============================================================
# EXTRACT PROJECTS
# ============================================================

def extract_projects(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    projects = []

    project_section = False

    stop_sections = [
        "education",
        "experience",
        "skills",
        "technical skills",
        "certification",
        "certifications",
        "achievements",
        "languages",
        "coursework",
        "references"
    ]

    bullet_pattern = re.compile(
        r"^[•\-\*]"
    )

    for line in lines:

        lower = line.lower().strip()

        if (
            lower in [
                "projects",
                "project",
                "academic projects",
                "academic project"
            ]
            or lower.startswith("projects:")
            or lower.startswith("academic projects:")
        ):
            project_section = True
            continue

        if not project_section:
            continue

        if any(
            lower == section
            or lower.startswith(section + ":")
            for section in stop_sections
        ):
            break

        if bullet_pattern.match(line):
            continue

        if len(line) > 100:
            continue

        if line.endswith("."):
            continue

        if not re.search(
            r"[A-Za-z]",
            line
        ):
            continue

        projects.append(line)

    projects = list(
        dict.fromkeys(projects)
    )

    return projects[:10]


# ============================================================
# BUILD STUDENT PROFILE
# ============================================================

def parse_resume(pdf_path):

    pdf_result = extract_text_from_pdf(
        pdf_path
    )

    if pdf_result.get("status") != "OK":
        return pdf_result

    text = pdf_result["text"]

    text = normalize_text(text)

    name = extract_name(text)

    email = extract_email(text)

    phone = extract_phone(text)

    skills = extract_skills(text)

    qualifications = extract_qualifications(
        text
    )

    projects = extract_projects(text)

    return {
        "status": "OK",
        "student_profile": {
            "name": name,
            "email": email,
            "phone": phone,
            "skills": skills,
            "qualifications": qualifications,
            "projects": projects
        }
    }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    resume_path = "resume.pdf"

    result = parse_resume(
        resume_path
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )