import re


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {
    "spring boot": "Spring Boot",
    "spring mvc": "Spring MVC",
    "object oriented programming": "OOP",
    "exception handling": "Exception Handling",
    "multithreading": "Multithreading",
    "database design": "Database Design",
    "rest apis": "REST APIs",
    "rest api": "REST APIs",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "artificial intelligence": "AI",
    "data analytics": "Data Analytics",
    "data analysis": "Data Analysis",
    "microservices": "Microservices",

    "javascript": "JavaScript",
    "js": "JavaScript",
    "python": "Python",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "sql": "SQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "html": "HTML",
    "css": "CSS",
    "react": "React",
    "django": "Django",
    "flask": "Flask",
    "hibernate": "Hibernate",
    "jpa": "JPA",
    "git": "Git",
    "github": "GitHub",
    "docker": "Docker",
    "aws": "AWS",
    "azure": "Azure",
    "ai": "AI",
    "oop": "OOP",
    "collections": "Collections",
    "junit": "JUnit",
    "mockito": "Mockito",
    "agile": "Agile",
    "scrum": "Scrum",
    
"numpy": "NumPy",
"pandas": "Pandas",
"scikit-learn": "Scikit-learn",
"sklearn": "Scikit-learn",
"firebase": "Firebase",
"firebase realtime database": "Firebase Realtime Database",
"data structures": "Data Structures",
"data structures & algorithms": "Data Structures & Algorithms",
"algorithms": "Algorithms",
"dbms": "DBMS",
"operating systems": "Operating Systems",
"computer networks": "Computer Networks",
}


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):
    if not text:
        return ""

    return re.sub(r"\s+", " ", text.lower()).strip()


# ============================================================
# CLEAN HEADING
# ============================================================

def clean_heading(line):
    return line.strip().lower().rstrip(":").strip()


# ============================================================
# CLEAN PDF BULLETS
# ============================================================

def clean_resume_line(line):
    """
    Removes common PDF bullet characters and extra whitespace.
    """

    line = line.strip()

    # Common bullet characters:
    # \uf0b7 = PDF/FontAwesome style bullet
    # \u2022 = •
    # \u25aa = ▪
    # \u25cf = ●
    # \u25e6 = ◦
    line = re.sub(
        r"^[\uf0b7\u2022\u25aa\u25cf\u25e6]+\s*",
        "",
        line
    )

    return line.strip()


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
        return None

    first_line = lines[0]

    if (
        len(first_line.split()) <= 5
        and not any(char.isdigit() for char in first_line)
        and "@" not in first_line
    ):
        return first_line

    return None


# ============================================================
# EXTRACT CONTACT INFORMATION
# ============================================================

def extract_contact(text):

    email = None
    phone = None
    linkedin = None
    github = None

    # --------------------------------------------------------
    # Email
    # --------------------------------------------------------

    email_match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    if email_match:
        email = email_match.group()

    # --------------------------------------------------------
    # Indian phone number
    # --------------------------------------------------------

    phone_match = re.search(
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        text
    )

    if phone_match:
        phone = phone_match.group()

    # --------------------------------------------------------
    # LinkedIn
    # --------------------------------------------------------

    linkedin_match = re.search(
        r"(https?://)?(www\.)?linkedin\.com/[A-Za-z0-9_./-]+",
        text,
        re.IGNORECASE
    )

    if linkedin_match:
        linkedin = linkedin_match.group()

    # --------------------------------------------------------
    # GitHub
    # --------------------------------------------------------

    github_match = re.search(
        r"(https?://)?(www\.)?github\.com/[A-Za-z0-9_./-]+",
        text,
        re.IGNORECASE
    )

    if github_match:
        github = github_match.group()

    return {
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github
    }


# ============================================================
# EXTRACT SKILLS
# ============================================================

def extract_skills(text):

    lines = [
        clean_resume_line(line)
        for line in text.splitlines()
        if clean_resume_line(line)
    ]

    skill_section_names = {
        "skills",
        "technical skills",
        "technical skill",
        "skills & technologies",
        "skills and technologies",
        "technologies",
        "technical expertise"
    }

    stop_sections = {
        "projects",
        "project",
        "academic projects",
        "personal projects",
        "experience",
        "work experience",
        "professional experience",
        "education",
        "certifications",
        "certification",
        "certificates",
        "certificate",
        "achievements",
        "achievement",
        "awards",
        "publications",
        "contact",
        "internship",
        "internships"
    }

    inside_skills = False
    skill_text = []

    for line in lines:

        heading = clean_heading(line)

        if heading in skill_section_names:
            inside_skills = True
            continue

        if inside_skills and heading in stop_sections:
            break

        if inside_skills:
            skill_text.append(line)

    if not skill_text:
        return []

    skills_text = " ".join(skill_text).lower()

    found_skills = []

    # Longer aliases first so that:
    # "Spring Boot" is checked before "Spring"
    aliases = sorted(
        SKILL_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for alias, canonical_skill in aliases:

        pattern = (
            r"(?<!\w)"
            + re.escape(alias)
            + r"(?!\w)"
        )

        if re.search(pattern, skills_text):
            found_skills.append(canonical_skill)

    if "Data Structures & Algorithms" in found_skills:
      found_skills = [
        skill for skill in found_skills
        if skill not in {"Data Structures", "Algorithms"}
    ]

    if "Firebase Realtime Database" in found_skills:
      found_skills = [
        skill for skill in found_skills
        if skill != "Firebase"
    ]

    return list(dict.fromkeys(found_skills))


# ============================================================
# EXTRACT QUALIFICATIONS
# ============================================================

def extract_qualifications(text):
    normalized_text = normalize_text(text)

    # Remove spaces around dots so:
    # "B . Tech", "B. Tech", "B.Tech" -> easier matching
    compact_text = re.sub(r"\s*\.\s*", ".", normalized_text)

    qualifications = []

    # --------------------------------------------------------
    # B.Tech
    # --------------------------------------------------------
    if (
        re.search(r"\bb\.?\s*tech\b", compact_text)
        or re.search(r"\bbtech\b", compact_text)
        or re.search(r"\bbachelor\s+of\s+technology\b", normalized_text)
    ):
        qualifications.append("B.Tech")

    # --------------------------------------------------------
    # B.E
    # Only explicit B.E / B.E. / B E / Bachelor of Engineering
    # --------------------------------------------------------
    if (
        re.search(r"\bb\.?\s*e\.?\b", compact_text)
        or re.search(r"\bbachelor\s+of\s+engineering\b", normalized_text)
    ):
        qualifications.append("B.E")

    # --------------------------------------------------------
    # M.Tech
    # --------------------------------------------------------
    if (
        re.search(r"\bm\.?\s*tech\b", compact_text)
        or re.search(r"\bmtech\b", compact_text)
        or re.search(r"\bmaster\s+of\s+technology\b", normalized_text)
    ):
        qualifications.append("M.Tech")

    # --------------------------------------------------------
    # MCA
    # --------------------------------------------------------
    if (
        re.search(r"\bmca\b", compact_text)
        or re.search(r"\bmaster\s+of\s+computer\s+applications\b", normalized_text)
    ):
        qualifications.append("MCA")

    # --------------------------------------------------------
    # Computer Science
    # --------------------------------------------------------
    if re.search(r"\bcomputer\s+science\b", normalized_text):
        qualifications.append("Computer Science")
    elif re.search(r"\bcse\b", normalized_text):
        qualifications.append("Computer Science")

    # --------------------------------------------------------
    # Information Technology
    # --------------------------------------------------------
    if re.search(r"\binformation\s+technology\b", normalized_text):
        qualifications.append("Information Technology")
    elif re.search(r"\binformation\s+tech\b", normalized_text):
        qualifications.append("Information Technology")

    return list(dict.fromkeys(qualifications))

# ============================================================
# GENERIC SECTION EXTRACTOR
# ============================================================

def extract_section(text, section_names, stop_sections):

    lines = [
        clean_resume_line(line)
        for line in text.splitlines()
        if clean_resume_line(line)
    ]

    section_data = []
    inside_section = False

    for line in lines:

        heading = clean_heading(line)

        if heading in section_names:
            inside_section = True
            continue

        if inside_section and heading in stop_sections:
            break

        if inside_section:
            section_data.append(line)

    return section_data


# ============================================================
# EXTRACT PROJECTS
# ============================================================

def extract_projects(text):

    lines = [
        clean_resume_line(line)
        for line in text.splitlines()
        if clean_resume_line(line)
    ]

    project_headings = {
        "projects",
        "project",
        "academic projects",
        "personal projects"
    }

    stop_sections = {
        "experience",
        "work experience",
        "professional experience",
        "education",
        "skills",
        "technical skills",
        "certifications",
        "certification",
        "certificates",
        "certificate",
        "achievements",
        "achievement",
        "contact",
        "internship",
        "internships",
        "awards",
        "publications"
    }

    inside_projects = False
    projects = []

    # --------------------------------------------------------
    # Words that normally indicate project descriptions
    # --------------------------------------------------------

    description_starts = (
        "developed ",
        "built ",
        "implemented ",
        "designed ",
        "performed ",
        "analyzed ",
        "enabled ",
        "added ",
        "created ",
        "used ",
        "worked ",
        "integrated ",
        "deployed ",
        "configured ",
        "managed ",
        "improved ",
        "applied ",
        "trained ",
        "utilized ",
        "implemented ",
    )

    for line in lines:

        heading = clean_heading(line)

        # Start project section
        if heading in project_headings:
            inside_projects = True
            continue

        # End project section
        if inside_projects and heading in stop_sections:
            break

        if not inside_projects:
            continue

        # Ignore obvious description lines
        lower_line = line.lower()

        if lower_line.startswith(description_starts):
            continue

        # Ignore lines that are clearly sentences
        if len(line.split()) > 12:
            continue

        # Ignore date-like lines
        if re.search(
            r"\b(20\d{2}|19\d{2})\b",
            line
        ):
            continue

        # Add project title
        projects.append(line)

    return list(dict.fromkeys(projects))


# ============================================================
# EXTRACT EXPERIENCE
# ============================================================

def extract_experience(text):

    return extract_section(
        text,

        {
            "experience",
            "work experience",
            "professional experience",
            "internship",
            "internships"
        },

        {
            "projects",
            "project",
            "education",
            "skills",
            "technical skills",
            "certifications",
            "certification",
            "certificate",
            "certificates",
            "achievements",
            "achievement",
            "contact",
            "awards",
            "publications"
        }
    )


# ============================================================
# EXTRACT CERTIFICATIONS
# ============================================================

def extract_certifications(text):

    lines = [
        clean_resume_line(line)
        for line in text.splitlines()
        if clean_resume_line(line)
    ]

    certification_headings = {
        "certifications",
        "certification",
        "certificates",
        "certificate"
    }

    stop_sections = {
        "projects",
        "project",
        "experience",
        "work experience",
        "professional experience",
        "education",
        "skills",
        "technical skills",
        "achievements",
        "achievement",
        "contact",
        "awards",
        "publications"
    }

    inside_certifications = False
    certifications = []

    for line in lines:

        heading = clean_heading(line)

        if heading in certification_headings:
            inside_certifications = True
            continue

        if inside_certifications and heading in stop_sections:
            break

        if not inside_certifications:
            continue

        certifications.append(line)

    return list(dict.fromkeys(certifications))


# ============================================================
# EXTRACT ACHIEVEMENTS
# ============================================================

def extract_achievements(text):

    return extract_section(
        text,

        {
            "achievements",
            "achievement",
            "accomplishments",
            "awards",
            "honors",
            "honours"
        },

        {
            "projects",
            "project",
            "experience",
            "work experience",
            "professional experience",
            "education",
            "skills",
            "technical skills",
            "certifications",
            "certification",
            "certificate",
            "certificates",
            "contact",
            "publications"
        }
    )


# ============================================================
# MAIN RESUME ANALYZER
# ============================================================

def analyze_resume_text(resume_text):

    if not resume_text or not resume_text.strip():

        return {
            "status": "ERROR",
            "message": "Resume text is empty"
        }

    name = extract_name(resume_text)

    contact = extract_contact(resume_text)

    skills = extract_skills(resume_text)

    qualifications = extract_qualifications(resume_text)

    projects = extract_projects(resume_text)

    experience = extract_experience(resume_text)

    certifications = extract_certifications(resume_text)

    achievements = extract_achievements(resume_text)

    return {
        "status": "OK",

        "student": {
            "name": name,
            "contact": contact,
            "skills": skills,
            "qualifications": qualifications,
            "projects": projects,
            "experience": experience,
            "certifications": certifications,
            "achievements": achievements
        }
    }


# ============================================================
# AGENT TOOL WRAPPER
# ============================================================

def run_resume_analyzer(args):

    if not isinstance(args, dict):
        return {
            "status": "ERROR",
            "message": "Invalid arguments"
        }

    resume_text = args.get("resume_text", "")

    return analyze_resume_text(resume_text)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    sample_resume = """
    GAUTAM SINGH

    Email: gautamsingh07102006@gmail.com
    Phone: +91 6284843115
    LinkedIn: https://www.linkedin.com/in/gautam-singh-864657328
    GitHub: https://github.com/gautamSingh0710

    B.Tech Computer Science Engineering
    Chitkara University

    Skills:
    Java, Python, C++, JavaScript, HTML, CSS, Django, Git, GitHub, OOP

    Projects:

    Smart Parking System
    Developed an IoT-based smart parking system using ESP32,
    Firebase Realtime Database, and a web dashboard.
    Implemented real-time parking slot monitoring.

    AI Crime Hotspot Detection
    Built a machine learning model using Python and Scikit-learn.
    Performed data preprocessing and visualization.

    Instagram Clone using Django
    Developed a social media web application using Django.
    Implemented user login functionality.

    VegBooking
    Developed an online vegetable booking platform using HTML,
    CSS, JavaScript, and Firebase Realtime Database.

    Certifications:

    Microsoft Certified: Azure Fundamentals (AZ-900)
    Microsoft Certified: Azure AI Fundamentals (AI-900)
    Microsoft Certified: Azure Data Fundamentals (DP-900)
    Infosys Springboard - Java Programming Fundamentals
    Data Structures & Algorithms Kick-Start

    Achievements:

    Participated in hackathon.
    Solved coding problems on LeetCode.

    Education:

    B.Tech CSE
    Chitkara University
    """

    import json

    result = run_resume_analyzer({
        "resume_text": sample_resume
    })

    print(json.dumps(result, indent=2))