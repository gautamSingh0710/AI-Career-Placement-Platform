import sys
import json
import re
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


# ============================================================
# PROJECT PATHS
# ============================================================

# Project structure:
#
# 3023_gautam_2016/
# └── placement_agent/
#     ├── backend/
#     │   └── main.py
#     │
#     └── placement_agent/
#         ├── agent_tools.py
#         ├── chat.py
#         ├── resume_tools.py
#         ├── resume_parser.py
#         └── user_data/
#

BACKEND_DIR = Path(__file__).resolve().parent

APP_ROOT = BACKEND_DIR.parent

PLACEMENT_AGENT_DIR = APP_ROOT / "placement_agent"


# ============================================================
# PYTHON PATH
# ============================================================

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

if str(PLACEMENT_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(PLACEMENT_AGENT_DIR))


# ============================================================
# PROJECT IMPORTS
# ============================================================

from agent_tools import (
    AGENT_NAME,
    PROJECT_ENDPOINT,
)

from chat import run_turn
from resume_tools import run_resume_tool


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="AI Career Placement Platform",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# AZURE FOUNDRY CLIENT
# ============================================================

try:

    print()
    print("Connecting to Azure AI Project...")
    print(f"Project endpoint: {PROJECT_ENDPOINT}")

    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    openai = project.get_openai_client()

    print("Azure AI Project connected.")
    print()

except Exception as error:

    print()
    print("========== AZURE CLIENT ERROR ==========")
    print(type(error).__name__)
    print(str(error))
    print("========================================")
    print()

    raise


# ============================================================
# USER DATA DIRECTORY
# ============================================================

USER_DATA_DIR = (
    PLACEMENT_AGENT_DIR
    / "user_data"
)

USER_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# PROFILE FILE
# ============================================================

PROFILE_FILENAME = "profile.json"


# ============================================================
# IN-MEMORY CACHE
# ============================================================

user_profiles = {}


# ============================================================
# AZURE CONVERSATIONS
# ============================================================

conversations = {}


# ============================================================
# EMAIL NORMALIZATION
# ============================================================

def normalize_email(email: str) -> str:

    if email is None:
        return ""

    return str(email).strip().lower()


# ============================================================
# EMAIL -> SAFE FOLDER
# ============================================================

def email_to_folder_name(email: str) -> str:

    email = normalize_email(email)

    if not email:
        raise ValueError(
            "User email is required."
        )

    safe_email = (
        email
        .replace("@", "_at_")
        .replace(".", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    return safe_email


# ============================================================
# USER DIRECTORY
# ============================================================

def get_user_directory(email: str) -> Path:

    email = normalize_email(email)

    if not email:
        raise ValueError(
            "User email is required."
        )

    safe_email = email_to_folder_name(
        email
    )

    user_directory = (
        USER_DATA_DIR
        / safe_email
    )

    user_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return user_directory


# ============================================================
# USER PROFILE PATH
# ============================================================

def get_user_profile_path(email: str) -> Path:

    return (
        get_user_directory(email)
        / PROFILE_FILENAME
    )


# ============================================================
# USER RESUME PATH
# ============================================================

def get_user_resume_path(email: str) -> Path:

    return (
        get_user_directory(email)
        / "resume.pdf"
    )


# ============================================================
# DEFAULT PROFILE
# ============================================================

def create_default_profile(email: str):

    email = normalize_email(email)

    return {

        # ----------------------------------------------------
        # BASIC
        # ----------------------------------------------------

        "name": "",

        "email": email,

        "degree": "",

        "branch": "",

        "skills": [],

        # ----------------------------------------------------
        # ACADEMIC
        # ----------------------------------------------------

        "cgpa": "-",

        "tenth_percentage": "-",

        "twelfth_percentage": "-",

        "backlogs": "-",

        "active_backlogs": "-",

        "attendance": "-",

        # ----------------------------------------------------
        # RESUME
        # ----------------------------------------------------

        "resume_uploaded": False,

        "resume_filename": None,

        "resume_updated": False,

        "resume_score": "-",

        # ----------------------------------------------------
        # PLACEMENT
        # ----------------------------------------------------

        "eligible_companies": "-",

        # ----------------------------------------------------
        # PROFILE STATE
        # ----------------------------------------------------

        "profile_updated": False,
    }


# ============================================================
# LOAD PROFILE FROM DISK
# ============================================================

def load_profile_from_disk(email: str):

    email = normalize_email(email)

    if not email:
        raise ValueError(
            "User email is required."
        )

    profile_path = get_user_profile_path(
        email
    )

    if not profile_path.exists():
        return None

    try:

        data = json.loads(
            profile_path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(data, dict):
            return None

        return data

    except Exception as error:

        print()
        print("========== PROFILE LOAD ERROR ==========")
        print(type(error).__name__)
        print(str(error))
        print("========================================")
        print()

        return None


# ============================================================
# SAVE PROFILE TO DISK
# ============================================================

def save_profile_to_disk(profile: dict):

    email = normalize_email(
        profile.get("email", "")
    )

    if not email:
        return

    try:

        profile_path = get_user_profile_path(
            email
        )

        profile_path.write_text(
            json.dumps(
                profile,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    except Exception as error:

        print()
        print("========== PROFILE SAVE ERROR ==========")
        print(type(error).__name__)
        print(str(error))
        print("========================================")
        print()


# ============================================================
# PERSIST RESUME ANALYSIS SCORE
# ============================================================

def persist_resume_analysis_score(
    email: str,
    score,
):

    email = normalize_email(email)

    if not email:
        raise ValueError(
            "User email is required."
        )

    profile = get_or_create_profile(email)

    if score is not None:
        profile["resume_score"] = score

    profile["resume_updated"] = True
    profile["profile_updated"] = True

    save_profile_to_disk(profile)
    user_profiles[email] = profile

    return profile


# ============================================================
# GET OR CREATE PROFILE
# ============================================================
#
# IMPORTANT:
# Do NOT blindly trust the in-memory cache.
#
# Every request loads the latest profile from disk.
#
# This prevents:
#
# User A -> logout
# User B -> login
# User A old values -> accidentally shown
#
# ============================================================

def get_or_create_profile(email: str):

    email = normalize_email(email)

    if not email:
        raise ValueError(
            "User email is required."
        )

    saved_profile = load_profile_from_disk(
        email
    )

    profile = create_default_profile(
        email
    )

    if saved_profile:

        profile.update(
            saved_profile
        )

    profile["email"] = email

    user_profiles[email] = profile

    return profile


# ============================================================
# UPDATE PROFILE FIELD
# ============================================================

def update_profile_field(
    email: str,
    key: str,
    value,
):

    profile = get_or_create_profile(
        email
    )

    if value is not None:
        profile[key] = value

    profile["profile_updated"] = True

    save_profile_to_disk(
        profile
    )

    user_profiles[
        normalize_email(email)
    ] = profile

    return profile


# ============================================================
# EXTRACT RESUME TEXT
# ============================================================

def extract_resume_text(
    resume_path: Path,
) -> str:

    if not resume_path.exists():
        return ""

    try:

        from pypdf import PdfReader

        reader = PdfReader(
            str(resume_path)
        )

        pages = []

        for page in reader.pages:

            try:

                text = (
                    page.extract_text()
                    or ""
                )

                pages.append(text)

            except Exception:
                continue

        return "\n".join(
            pages
        )

    except Exception as error:

        print()
        print("========== PDF TEXT ERROR ==========")
        print(type(error).__name__)
        print(str(error))
        print("====================================")
        print()

        return ""


# ============================================================
# EXTRACT CGPA FROM PDF
# ============================================================

def extract_cgpa_from_pdf(
    resume_path: Path,
):

    text = extract_resume_text(
        resume_path
    )

    if not text.strip():
        return None

    patterns = [

        r"\bCGPA\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)"
        r"\s*(?:/10)?",

        r"\bC\.G\.P\.A\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)"
        r"\s*(?:/10)?",

        r"\bCumulative\s+Grade\s+Point"
        r"\s+Average\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            try:

                value = float(
                    match.group(1)
                )

                if 0 <= value <= 10:
                    return value

            except Exception:
                pass

    return None


# ============================================================
# GENERIC NUMBER EXTRACTION
# ============================================================

def extract_number(
    text: str,
    patterns,
):

    if not text:
        return None

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            try:
                return match.group(1)

            except Exception:
                continue

    return None


# ============================================================
# EXTRACT PERCENTAGE
# ============================================================

def clean_percentage(
    value,
):

    if value is None:
        return None

    try:

        number = float(
            value
        )

        if 0 <= number <= 100:

            if number.is_integer():
                return int(number)

            return number

    except Exception:
        pass

    return None


# ============================================================
# EXTRACT PROFILE FROM RESUME PDF
# ============================================================
#
# IMPORTANT:
#
# PDF is the authoritative source for:
#
# CGPA
# Name
# Degree
# Branch
# Skills
# 10th
# 12th
#
# Agent response is NOT used to overwrite these fields.
#
# ============================================================

def extract_profile_from_resume_pdf(
    resume_path: Path,
):

    text = extract_resume_text(
        resume_path
    )

    if not text.strip():
        return {}

    profile = {}

    # ========================================================
    # CGPA
    # ========================================================

    cgpa = extract_cgpa_from_pdf(
        resume_path
    )

    if cgpa is not None:

        profile["cgpa"] = cgpa

    else:

        # Very important:
        # If the new PDF has no CGPA,
        # do NOT keep old CGPA.
        profile["cgpa"] = "-"

    # ========================================================
    # 10TH
    # ========================================================

    tenth_patterns = [

        r"\b10th\b[^\n]{0,100}?"
        r"(\d+(?:\.\d+)?)\s*%",

        r"\bX\b[^\n]{0,100}?"
        r"(\d+(?:\.\d+)?)\s*%",

        r"\bSSC\b[^\n]{0,100}?"
        r"(\d+(?:\.\d+)?)\s*%",
    ]

    tenth = extract_number(
        text,
        tenth_patterns,
    )

    tenth = clean_percentage(
        tenth
    )

    if tenth is not None:
        profile[
            "tenth_percentage"
        ] = tenth

    else:
        profile[
            "tenth_percentage"
        ] = "-"

    # ========================================================
    # 12TH
    # ========================================================

    twelfth_patterns = [

        r"\b12th\b[^\n]{0,100}?"
        r"(\d+(?:\.\d+)?)\s*%",

        r"\bXII\b[^\n]{0,100}?"
        r"(\d+(?:\.\d+)?)\s*%",

        r"\bHSC\b[^\n]{0,100}?"
        r"(\d+(?:\.\d+)?)\s*%",
    ]

    twelfth = extract_number(
        text,
        twelfth_patterns,
    )

    twelfth = clean_percentage(
        twelfth
    )

    if twelfth is not None:

        profile[
            "twelfth_percentage"
        ] = twelfth

    else:

        profile[
            "twelfth_percentage"
        ] = "-"

    # ========================================================
    # DEGREE
    # ========================================================

    degree_patterns = [

        r"\bB\.?\s*Tech\.?\b",

        r"\bBachelor\s+of\s+Technology\b",

        r"\bB\.?\s*E\.?\b",

        r"\bBachelor\s+of\s+Engineering\b",
    ]

    degree = None

    for pattern in degree_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            degree = (
                match.group(0)
                .strip()
            )

            break

    if degree:

        degree = re.sub(
            r"\s+",
            " ",
            degree,
        )

        profile[
            "degree"
        ] = degree

    else:

        profile[
            "degree"
        ] = ""

    # ========================================================
    # BRANCH
    # ========================================================

    branch = ""

    branch_patterns = [

        (
            r"Computer\s+Science\s*"
            r"(?:&|and)\s*Engineering",
            "Computer Science & Engineering",
        ),

        (
            r"Information\s+Technology",
            "Information Technology",
        ),

        (
            r"Artificial\s+Intelligence\s*"
            r"(?:&|and)\s*Data\s+Science",
            "Artificial Intelligence & Data Science",
        ),

        (
            r"Electronics\s*"
            r"(?:&|and)\s*Communication\s*"
            r"Engineering",
            "Electronics & Communication Engineering",
        ),

        (
            r"Electrical\s+Engineering",
            "Electrical Engineering",
        ),

        (
            r"Mechanical\s+Engineering",
            "Mechanical Engineering",
        ),

        (
            r"Civil\s+Engineering",
            "Civil Engineering",
        ),
    ]

    for pattern, value in branch_patterns:

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):

            branch = value
            break

    if not branch:

        branch_match = re.search(
            r"\bbranch\s*[:\-]\s*([^\n]+)",
            text,
            re.IGNORECASE,
        )

        if branch_match:

            branch = (
                branch_match.group(1)
                .strip()
            )

    profile[
        "branch"
    ] = branch

    # ========================================================
    # NAME
    # ========================================================

    lines = []

    for raw_line in text.splitlines():

        line = re.sub(
            r"\s+",
            " ",
            raw_line,
        ).strip()

        if line:
            lines.append(line)

    ignored = {

        "resume",

        "curriculum vitae",

        "cv",

        "profile",

        "education",

        "experience",

        "skills",

        "technical skills",

        "projects",

        "certifications",

        "contact",

        "objective",

        "summary",
    }

    for line in lines[:25]:

        clean = line.strip()

        if not clean:
            continue

        lower = clean.lower()

        if lower in ignored:
            continue

        if "@" in clean:
            continue

        if re.search(
            r"\b(phone|mobile|email|linkedin|github)\b",
            clean,
            re.IGNORECASE,
        ):
            continue

        if re.search(
            r"\d{5,}",
            clean,
        ):
            continue

        if len(clean) < 3:
            continue

        if len(clean) > 60:
            continue

        if re.fullmatch(
            r"[A-Za-z .'\-]+",
            clean,
        ):

            # Don't accidentally pick
            # degree/college/section headings.
            if not re.search(
                r"\b(B\.?Tech|B\.?E\.?|"
                r"Engineering|College|"
                r"University|School)\b",
                clean,
                re.IGNORECASE,
            ):

                profile[
                    "name"
                ] = clean

                break

    if "name" not in profile:

        profile["name"] = ""

    # ========================================================
    # SKILLS
    # ========================================================

    known_skills = [

        "Java",

        "Python",

        "C++",

        "C",

        "SQL",

        "JavaScript",

        "TypeScript",

        "HTML",

        "CSS",

        "React",

        "Django",

        "Flask",

        "Spring Boot",

        "MongoDB",

        "MySQL",

        "Firebase",

        "Git",

        "GitHub",

        "Azure",

        "AWS",

        "Machine Learning",

        "Deep Learning",

        "Data Structures",

        "Algorithms",

        "Data Analytics",

        "Power BI",

        "Excel",

        "Node.js",

        "Express",

        "REST API",

        "FastAPI",

    ]

    detected_skills = []

    for skill in known_skills:

        if re.search(
            re.escape(skill),
            text,
            re.IGNORECASE,
        ):

            if skill not in detected_skills:

                detected_skills.append(
                    skill
                )

    profile[
        "skills"
    ] = detected_skills

    return profile


# ============================================================
# EXTRACT PROFILE VALUES FROM AGENT RESPONSE
# ============================================================
#
# This function is kept for compatibility.
#
# IMPORTANT:
# Chat responses must NOT update CGPA/profile automatically.
#
# It can still be used later for explicit profile tools.
#
# ============================================================

def extract_profile_values_from_text(
    text: str,
):

    if not text:
        return {}

    values = {}

    # Active backlog only.
    # We intentionally do NOT extract CGPA here.

    backlogs = extract_number(
        text,
        [
            r"active\s+backlogs?\s*[:\-]?\s*(\d+)",
            r"backlogs?\s*[:\-]?\s*(\d+)",
        ],
    )

    if backlogs is not None:

        values[
            "active_backlogs"
        ] = str(backlogs)

    # Attendance can be extracted
    # only when explicitly mentioned.

    attendance = extract_number(
        text,
        [
            r"attendance\s*[:\-]?\s*"
            r"(\d+(?:\.\d+)?)\s*%",

            r"attendance\s+is\s*"
            r"(\d+(?:\.\d+)?)\s*%",
        ],
    )

    if attendance is not None:

        attendance_value = clean_percentage(
            attendance
        )

        if attendance_value is not None:

            values[
                "attendance"
            ] = attendance_value

    # Resume score can be extracted
    # only if explicitly returned.

    resume_score = extract_number(
        text,
        [
            r"resume\s+score\s*[:\-]?\s*"
            r"(\d+(?:\.\d+)?)",

            r"score\s*[:\-]?\s*"
            r"(\d+(?:\.\d+)?)\s*/\s*100",
        ],
    )

    if resume_score is not None:

        try:

            score = float(
                resume_score
            )

            if 0 <= score <= 100:

                if score.is_integer():
                    score = int(score)

                values[
                    "resume_score"
                ] = score

        except Exception:
            pass

    return values


# ============================================================
# REFRESH PROFILE FROM RESUME
# ============================================================
#
# THIS IS THE MAIN FIX.
#
# The uploaded PDF is authoritative.
#
# Agent cannot overwrite CGPA.
# Agent cannot overwrite name/branch/degree/skills.
#
# ============================================================

def refresh_profile_from_agent(
    email: str,
):

    email = normalize_email(email)

    if not email:
        raise ValueError(
            "User email is required."
        )

    profile = get_or_create_profile(
        email
    )

    resume_path = get_user_resume_path(
        email
    )

    if not resume_path.exists():

        profile[
            "resume_uploaded"
        ] = False

        profile[
            "resume_updated"
        ] = False

        save_profile_to_disk(
            profile
        )

        return profile

    # --------------------------------------------------------
    # READ PDF DIRECTLY
    # --------------------------------------------------------

    extracted = (
        extract_profile_from_resume_pdf(
            resume_path
        )
    )

    # --------------------------------------------------------
    # PDF VALUES ARE AUTHORITATIVE
    # --------------------------------------------------------

    resume_fields = [

        "name",

        "cgpa",

        "degree",

        "branch",

        "skills",

        "tenth_percentage",

        "twelfth_percentage",
    ]

    for key in resume_fields:

        if key in extracted:

            profile[key] = (
                extracted[key]
            )

    # --------------------------------------------------------
    # RESUME STATE
    # --------------------------------------------------------

    profile[
        "resume_uploaded"
    ] = True

    profile[
        "resume_updated"
    ] = True

    # Don't modify eligible_companies here.
    #
    # Eligibility should change only when
    # eligibility calculation is explicitly run.

    profile[
        "profile_updated"
    ] = True

    save_profile_to_disk(
        profile
    )

    user_profiles[
        email
    ] = profile

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    print()
    print("========== PDF PROFILE REFRESH ==========")
    print(f"User: {email}")
    print(f"Resume: {resume_path}")
    print(
        f"Name: {profile.get('name')}"
    )
    print(
        f"CGPA: {profile.get('cgpa')}"
    )
    print(
        f"Degree: {profile.get('degree')}"
    )
    print(
        f"Branch: {profile.get('branch')}"
    )
    print(
        f"10th: {profile.get('tenth_percentage')}"
    )
    print(
        f"12th: {profile.get('twelfth_percentage')}"
    )
    print(
        f"Skills: {profile.get('skills')}"
    )
    print("==========================================")
    print()

    return profile


# ============================================================
# USER CONVERSATION
# ============================================================

def get_user_conversation(
    email: str,
):

    email = normalize_email(email)

    if not email:
        raise ValueError(
            "User email is required."
        )

    if email not in conversations:

        print(
            f"Creating Azure conversation for: {email}"
        )

        conversations[
            email
        ] = openai.conversations.create()

    return conversations[
        email
    ]


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):

    email: str

    message: str


class ResumeAnalyzeRequest(BaseModel):

    email: str


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "status": "OK",

        "message":
            "AI Career Placement Backend "
            "is running",

        "agent":
            AGENT_NAME,
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "agent":
            AGENT_NAME,

        "azure_project":
            "connected",
    }


# ============================================================
# GET PROFILE
# ============================================================
#
# Every time frontend asks for profile:
#
# 1. Load correct user's profile
# 2. Check that user's resume
# 3. Re-read latest PDF
#
# This prevents stale profile values.
#
# ============================================================

@app.get("/profile")
def get_profile(
    email: str,
):

    email = normalize_email(email)

    if not email:

        return {

            "status": "ERROR",

            "message":
                "User email is required",
        }

    try:

        profile = get_or_create_profile(
            email
        )

        resume_path = (
            get_user_resume_path(
                email
            )
        )

        if resume_path.exists():

            profile = (
                refresh_profile_from_agent(
                    email
                )
            )

        else:

            profile[
                "resume_uploaded"
            ] = False

            profile[
                "resume_updated"
            ] = False

            profile[
                "resume_filename"
            ] = None

            save_profile_to_disk(
                profile
            )

        return {

            "status": "OK",

            "profile": profile,
        }

    except Exception as error:

        return {

            "status": "ERROR",

            "message": str(error),
        }


# ============================================================
# UPDATE PROFILE
# ============================================================

@app.post("/profile")
def update_profile(
    email: str = Form(...),
    name: str = Form(""),
    cgpa: str = Form("-"),
    backlogs: str = Form("-"),
):

    email = normalize_email(email)

    if not email:

        return {

            "status": "ERROR",

            "message":
                "User email is required",
        }

    try:

        profile = get_or_create_profile(
            email
        )

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        if name.strip():

            profile[
                "name"
            ] = name.strip()

        # ----------------------------------------------------
        # CGPA
        # ----------------------------------------------------
        #
        # Manual profile update is allowed,
        # but when a resume is uploaded, PDF becomes
        # authoritative again.
        #
        # ----------------------------------------------------

        if (
            cgpa.strip()
            and cgpa.strip() != "-"
        ):

            try:

                cgpa_value = float(
                    cgpa.strip()
                )

                if 0 <= cgpa_value <= 10:

                    profile[
                        "cgpa"
                    ] = cgpa_value

            except Exception:
                pass

        # ----------------------------------------------------
        # BACKLOGS
        # ----------------------------------------------------

        if (
            backlogs.strip()
            and backlogs.strip() != "-"
        ):

            profile[
                "backlogs"
            ] = backlogs.strip()

            profile[
                "active_backlogs"
            ] = backlogs.strip()

        profile[
            "profile_updated"
        ] = True

        save_profile_to_disk(
            profile
        )

        user_profiles[
            email
        ] = profile

        return {

            "status": "OK",

            "profile": profile,
        }

    except Exception as error:

        return {

            "status": "ERROR",

            "message": str(error),
        }


# ============================================================
# REFRESH PROFILE ENDPOINT
# ============================================================

@app.post("/profile/refresh")
def refresh_profile(
    email: str = Form(...),
):

    email = normalize_email(email)

    if not email:

        return {

            "status": "ERROR",

            "message":
                "User email is required",
        }

    try:

        profile = (
            refresh_profile_from_agent(
                email
            )
        )

        return {

            "status": "OK",

            "profile": profile,
        }

    except Exception as error:

        return {

            "status": "ERROR",

            "message": str(error),
        }


# ============================================================
# INTERNAL RESUME SAVE
# ============================================================

async def save_resume(
    email: str,
    file: UploadFile,
):

    email = normalize_email(
        email
    )

    if not email:

        return {

            "status": "ERROR",

            "message":
                "User email is required",
        }

    # --------------------------------------------------------
    # FILE NAME
    # --------------------------------------------------------

    if not file.filename:

        return {

            "status": "ERROR",

            "message":
                "Resume file is required",
        }

    original_filename = (
        file.filename.strip()
    )

    filename_lower = (
        original_filename.lower()
    )

    # --------------------------------------------------------
    # PDF CHECK
    # --------------------------------------------------------

    if not filename_lower.endswith(
        ".pdf"
    ):

        return {

            "status": "ERROR",

            "message":
                "Only PDF resumes are allowed",
        }

    # --------------------------------------------------------
    # SIZE LIMIT
    # --------------------------------------------------------

    MAX_FILE_SIZE = (
        10 * 1024 * 1024
    )

    # --------------------------------------------------------
    # USER DIRECTORY
    # --------------------------------------------------------

    try:

        user_directory = (
            get_user_directory(
                email
            )
        )

        resume_path = (
            user_directory
            / "resume.pdf"
        )

    except Exception as error:

        return {

            "status": "ERROR",

            "message": str(error),
        }

    # --------------------------------------------------------
    # READ FILE
    # --------------------------------------------------------

    try:

        file_content = (
            await file.read()
        )

    except Exception as error:

        return {

            "status": "ERROR",

            "message":
                "Could not read uploaded resume: "
                f"{str(error)}",
        }

    # --------------------------------------------------------
    # EMPTY FILE
    # --------------------------------------------------------

    if not file_content:

        return {

            "status": "ERROR",

            "message":
                "Uploaded resume is empty",
        }

    # --------------------------------------------------------
    # SIZE CHECK
    # --------------------------------------------------------

    if len(file_content) > MAX_FILE_SIZE:

        return {

            "status": "ERROR",

            "message":
                "Resume size must be below 10 MB",
        }

    # --------------------------------------------------------
    # BASIC PDF SIGNATURE CHECK
    # --------------------------------------------------------

    if not file_content.startswith(
        b"%PDF"
    ):

        return {

            "status": "ERROR",

            "message":
                "Uploaded file is not a valid PDF",
        }

    # --------------------------------------------------------
    # SAVE RESUME
    # --------------------------------------------------------

    try:

        resume_path.write_bytes(
            file_content
        )

    except Exception as error:

        return {

            "status": "ERROR",

            "message":
                "Could not save resume: "
                f"{str(error)}",
        }

    # ========================================================
    # VERY IMPORTANT
    # ========================================================
    #
    # New resume means old resume-derived values must NOT
    # survive.
    #
    # Otherwise:
    #
    # Old PDF -> CGPA 8.79
    # New PDF -> no CGPA
    #
    # Dashboard must show "-"
    #
    # ========================================================

    profile = get_or_create_profile(
        email
    )

    # Reset resume-derived fields.

    profile[
        "name"
    ] = ""

    profile[
        "cgpa"
    ] = "-"

    profile[
        "degree"
    ] = ""

    profile[
        "branch"
    ] = ""

    profile[
        "skills"
    ] = []

    profile[
        "tenth_percentage"
    ] = "-"

    profile[
        "twelfth_percentage"
    ] = "-"

    # --------------------------------------------------------
    # Resume score belongs to the resume.
    # New resume => old score should not remain.
    # User can press "Analyze My Resume" again.
    # --------------------------------------------------------

    profile[
        "resume_score"
    ] = "-"

    # --------------------------------------------------------
    # Eligibility is NOT automatically changed here.
    #
    # It should update when Eligibility is explicitly run.
    # --------------------------------------------------------

    profile[
        "eligible_companies"
    ] = "-"

    # --------------------------------------------------------
    # Resume state
    # --------------------------------------------------------

    profile[
        "resume_uploaded"
    ] = True

    profile[
        "resume_filename"
    ] = original_filename

    profile[
        "resume_updated"
    ] = True

    profile[
        "profile_updated"
    ] = True

    save_profile_to_disk(
        profile
    )

    # ========================================================
    # READ NEW PDF
    # ========================================================

    profile = (
        refresh_profile_from_agent(
            email
        )
    )

    # Keep actual uploaded filename.

    profile[
        "resume_uploaded"
    ] = True

    profile[
        "resume_filename"
    ] = original_filename

    profile[
        "resume_updated"
    ] = True

    save_profile_to_disk(
        profile
    )

    user_profiles[
        email
    ] = profile

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    print()
    print("========== RESUME UPLOADED ==========")
    print(f"User: {email}")
    print(
        f"Original file: {original_filename}"
    )
    print(
        f"Saved path: {resume_path}"
    )
    print(
        f"Size: {len(file_content)} bytes"
    )
    print(
        f"CGPA: {profile.get('cgpa')}"
    )
    print(
        f"Name: {profile.get('name')}"
    )
    print(
        f"Branch: {profile.get('branch')}"
    )
    print(
        f"Degree: {profile.get('degree')}"
    )
    print(
        f"10th: {profile.get('tenth_percentage')}"
    )
    print(
        f"12th: {profile.get('twelfth_percentage')}"
    )
    print(
        f"Skills: {profile.get('skills')}"
    )
    print("=====================================")
    print()

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "status": "OK",

        "message":
            "Resume uploaded successfully",

        "email": email,

        "filename":
            original_filename,

        "saved_filename":
            "resume.pdf",

        "resume_path":
            str(resume_path),

        "size":
            len(file_content),

        "resume_uploaded":
            True,

        "profile":
            profile,
    }


# ============================================================
# PRIMARY RESUME UPLOAD
# ============================================================

@app.post("/resume/upload")
async def upload_resume_primary(
    email: str = Form(...),
    file: UploadFile = File(...),
):

    return await save_resume(
        email,
        file,
    )


# ============================================================
# LEGACY RESUME UPLOAD
# ============================================================

@app.post("/upload-resume")
async def upload_resume_legacy(
    email: str = Form(...),
    file: UploadFile = File(...),
):

    return await save_resume(
        email,
        file,
    )


# ============================================================
# RESUME STATUS
# ============================================================

@app.get("/resume-status")
def resume_status(
    email: str,
):

    email = normalize_email(
        email
    )

    if not email:

        return {

            "status": "ERROR",

            "message":
                "User email is required",
        }

    try:

        resume_path = (
            get_user_resume_path(
                email
            )
        )

        exists = (
            resume_path.exists()
        )

        profile = (
            get_or_create_profile(
                email
            )
        )

        profile[
            "resume_uploaded"
        ] = exists

        if exists:

            profile[
                "resume_updated"
            ] = True

            if not profile.get(
                "resume_filename"
            ):

                profile[
                    "resume_filename"
                ] = "resume.pdf"

        else:

            profile[
                "resume_updated"
            ] = False

            profile[
                "resume_filename"
            ] = None

        save_profile_to_disk(
            profile
        )

        return {

            "status": "OK",

            "email": email,

            "resume_uploaded":
                exists,

            "filename":
                profile.get(
                    "resume_filename"
                )
                if exists
                else None,

            "resume_path":
                str(resume_path),

            "profile":
                profile,
        }

    except Exception as error:

        return {

            "status": "ERROR",

            "message": str(error),
        }


# ============================================================
# RESUME ANALYZE
# ============================================================

@app.post("/resume/analyze")
def analyze_resume_endpoint(
    request: ResumeAnalyzeRequest,
):

    email = normalize_email(request.email)

    if not email:

        return {
            "status": "ERROR",
            "message": "User email is required",
        }

    try:

        result = run_resume_tool(email)

        if not isinstance(result, dict):
            return {
                "status": "ERROR",
                "message": "Resume analysis returned invalid data",
            }

        if result.get("status") != "OK":
            return {
                "status": "ERROR",
                "message": result.get("message") or result.get("error") or "Resume analysis failed",
                "details": result,
            }

        score = result.get("resume_score", {}).get("score")

        if score is not None:
            profile = persist_resume_analysis_score(email, score)
        else:
            profile = get_or_create_profile(email)

        profile["resume_uploaded"] = True
        save_profile_to_disk(profile)
        user_profiles[email] = profile

        return {
            "status": "OK",
            "email": email,
            "resume_score": score,
            "analysis": result,
            "profile": profile,
            "response": (
                f"Resume analysis complete. "
                f"Your current score is {score}/100."
                if score is not None
                else "Resume analysis complete."
            ),
        }

    except Exception as error:

        return {
            "status": "ERROR",
            "message": str(error),
        }


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
):

    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    email = normalize_email(
        request.email
    )

    if not email:

        return {

            "status": "ERROR",

            "message":
                "User email is required",

            "response":
                "Please login first.",
        }

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    message = (
        request.message.strip()
    )

    if not message:

        return {

            "status": "ERROR",

            "message":
                "Message is required",

            "response":
                "Please enter a message.",
        }

    # --------------------------------------------------------
    # USER DIRECTORY
    # --------------------------------------------------------

    try:

        get_user_directory(
            email
        )

    except Exception as error:

        return {

            "status": "ERROR",

            "message": str(error),

            "response":
                "Could not load user profile.",
        }

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    try:

        profile = (
            get_or_create_profile(
                email
            )
        )

    except Exception as error:

        return {

            "status": "ERROR",

            "message": str(error),

            "response":
                "Could not load user profile.",
        }

    # --------------------------------------------------------
    # CONVERSATION
    # --------------------------------------------------------

    try:

        conversation = (
            get_user_conversation(
                email
            )
        )

    except Exception as error:

        return {

            "status": "ERROR",

            "message": str(error),

            "response":
                "Could not create conversation: "
                f"{str(error)}",
        }

    # --------------------------------------------------------
    # RUN AZURE AGENT
    # --------------------------------------------------------

    try:

        answer = run_turn(
            openai,
            conversation.id,
            message,
            email,
        )

        # ====================================================
        # IMPORTANT
        # ====================================================
        #
        # DO NOT parse the Agent answer and write CGPA
        # into profile.
        #
        # Otherwise agent may say 8.79 while PDF says 8.72.
        #
        # PDF remains authoritative.
        #
        # ====================================================

        return {

            "status": "OK",

            "email": email,

            "message": message,

            "response": answer,

            "profile": profile,
        }

    except Exception as error:

        print()
        print(
            "========== AGENT ERROR =========="
        )
        print(
            type(error).__name__
        )
        print(
            str(error)
        )
        print(
            "================================="
        )
        print()

        return {

            "status": "ERROR",

            "message": str(error),

            "response":
                f"Error: {str(error)}",
        }


# ============================================================
# DEBUG USER
# ============================================================

@app.get("/debug/user")
def debug_user(
    email: str,
):

    email = normalize_email(
        email
    )

    if not email:

        return {

            "status": "ERROR",

            "message":
                "User email is required",
        }

    try:

        user_directory = (
            get_user_directory(
                email
            )
        )

        resume_path = (
            get_user_resume_path(
                email
            )
        )

        profile_path = (
            get_user_profile_path(
                email
            )
        )

        profile = (
            get_or_create_profile(
                email
            )
        )

        return {

            "status": "OK",

            "email": email,

            "app_root":
                str(APP_ROOT),

            "placement_agent_dir":
                str(
                    PLACEMENT_AGENT_DIR
                ),

            "user_data_dir":
                str(
                    USER_DATA_DIR
                ),

            "user_directory":
                str(
                    user_directory
                ),

            "resume_path":
                str(
                    resume_path
                ),

            "profile_path":
                str(
                    profile_path
                ),

            "resume_exists":
                resume_path.exists(),

            "resume_size":
                (
                    resume_path.stat().st_size
                    if resume_path.exists()
                    else 0
                ),

            "profile_exists":
                profile_path.exists(),

            "profile":
                profile,
        }

    except Exception as error:

        return {

            "status": "ERROR",

            "message": str(error),
        }


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():

    print()
    print(
        "=============================================="
    )
    print(
        " AI CAREER PLACEMENT PLATFORM"
    )
    print(
        " Backend started successfully"
    )
    print(
        "=============================================="
    )

    print(
        f"Agent: {AGENT_NAME}"
    )

    print(
        f"Project endpoint: {PROJECT_ENDPOINT}"
    )

    print(
        f"User data: {USER_DATA_DIR}"
    )

    print(
        "=============================================="
    )

    print()