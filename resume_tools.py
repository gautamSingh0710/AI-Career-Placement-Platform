"""
User-specific resume tool for the Career Placement Platform.

Flow:

Logged-in user's email
        ↓
placement_agent/user_data/<safe_email>/resume.pdf
        ↓
Extract PDF text
        ↓
resume_analyzer.py
        ↓
resume_score_analyzer.py
        ↓
User-specific resume result

IMPORTANT:
The LLM never provides a resume path.

The backend receives user_email and decides which
resume belongs to that user.
"""

import re
from pathlib import Path

from azure.ai.projects.models import FunctionTool

from resume_analyzer import analyze_resume_text
from resume_score_analyzer import calculate_resume_score


# ============================================================
# PROJECT / USER RESUME DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# IMPORTANT:
#
# resume_tools.py is inside:
#
# placement_agent/
#
# Resume files are stored inside:
#
# placement_agent/
#     user_data/
#         <safe_email>/
#             resume.pdf
#
# Therefore:
#
# BASE_DIR / "user_data"
#
# is the correct location.

USERS_DIR = BASE_DIR / "placement_agent" / "user_data"


# ============================================================
# SAFE EMAIL → DIRECTORY NAME
# ============================================================

def safe_user_id(email: str):
    """
    Convert email into the SAME safe folder name
    used by backend/main.py.

    Example:

        gautam3023_beai24@chitkara.edu.in

    becomes:

        gautam3023_beai24_at_chitkara_edu_in
    """

    if not isinstance(email, str):
        return None

    email = email.strip().lower()

    if not email:
        return None

    # IMPORTANT:
    # This must match main.py exactly.

    safe_email = (
        email
        .replace("@", "_at_")
        .replace(".", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    # Extra protection against unexpected characters.

    safe_email = re.sub(
        r"[^a-zA-Z0-9_-]",
        "_",
        safe_email,
    )

    return safe_email


# ============================================================
# GET USER RESUME PATH
# ============================================================

def get_user_resume_path(user_email: str):
    """
    Return the resume path belonging to one user.

    Example:

        gautam3023_beai24@chitkara.edu.in

    becomes:

        placement_agent/
            user_data/
                gautam3023_beai24_at_chitkara_edu_in/
                    resume.pdf
    """

    user_id = safe_user_id(user_email)

    if not user_id:
        return None

    user_directory = USERS_DIR / user_id

    return user_directory / "resume.pdf"


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_resume_text(file_path):
    """
    Extract readable text from a PDF.
    """

    try:

        from pypdf import PdfReader

        reader = PdfReader(
            str(file_path)
        )

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:

                pages.append(
                    text
                )

        return "\n".join(pages)

    except Exception as exc:

        return {
            "status": "ERROR",

            "message": (
                "Could not read resume: "
                f"{type(exc).__name__}: {exc}"
            ),
        }


# ============================================================
# FUNCTION TOOL
# ============================================================

RESUME_TOOL = FunctionTool(

    name="score_resume",

    description=(
        "Analyze the currently logged-in student's saved resume "
        "and return a deterministic score out of 100. "
        "The backend automatically selects the resume belonging "
        "to the logged-in user's email. "
        "The model must not provide a resume path or filename. "
        "The result includes extracted student information, "
        "score breakdown and suggestions."
    ),

    parameters={
        "type": "object",

        "properties": {},

        "required": [],

        "additionalProperties": False,
    },

    strict=True,
)


# ============================================================
# RUN RESUME TOOL
# ============================================================

def run_resume_tool(user_email=None):
    """
    Analyze the resume belonging to the logged-in user.

    The backend decides which resume file belongs to the user.
    The LLM cannot choose the file.
    """

    # ========================================================
    # USER EMAIL REQUIRED
    # ========================================================

    if not user_email or not str(user_email).strip():

        return {
            "status": "USER_EMAIL_REQUIRED",

            "message": (
                "User email is required before analyzing a resume."
            ),
        }

    user_email = (
        str(user_email)
        .strip()
        .lower()
    )

    # ========================================================
    # USER RESUME PATH
    # ========================================================

    resume_path = get_user_resume_path(
        user_email
    )

    if resume_path is None:

        return {
            "status": "INVALID_USER",

            "message": "Invalid user email.",
        }

    # ========================================================
    # DEBUG INFORMATION
    # ========================================================

    print()
    print("========== RESUME TOOL ==========")
    print(
        f"User email : {user_email}"
    )
    print(
        f"Resume path: {resume_path}"
    )
    print(
        f"Exists     : {resume_path.exists()}"
    )
    print("=================================")
    print()

    # ========================================================
    # CHECK USER RESUME
    # ========================================================

    if not resume_path.exists():

        return {
            "status": "RESUME_NOT_FOUND",

            "message": (
                "No resume has been uploaded for this user yet."
            ),

            "user_email": user_email,

            "expected_path": str(
                resume_path
            ),
        }

    # ========================================================
    # EXTRACT PDF TEXT
    # ========================================================

    resume_text = extract_resume_text(
        resume_path
    )

    if isinstance(
        resume_text,
        dict,
    ):

        return resume_text

    if not isinstance(
        resume_text,
        str,
    ):

        return {
            "status": "ERROR",

            "message": (
                "Resume text extraction returned invalid data."
            ),

            "user_email": user_email,
        }

    if not resume_text.strip():

        return {
            "status": "NO_TEXT_FOUND",

            "message": (
                "No readable text was found in the uploaded resume."
            ),

            "user_email": user_email,
        }

    # ========================================================
    # ANALYZE RESUME
    # ========================================================

    try:

        resume_data = analyze_resume_text(
            resume_text
        )

    except Exception as exc:

        return {
            "status": "ERROR",

            "message": (
                "Resume analyzer failed: "
                f"{type(exc).__name__}: {exc}"
            ),

            "user_email": user_email,
        }

    if not isinstance(
        resume_data,
        dict,
    ):

        return {
            "status": "ERROR",

            "message": (
                "Resume analyzer returned invalid data."
            ),

            "user_email": user_email,
        }

    if resume_data.get("status") != "OK":

        return resume_data

    # ========================================================
    # CALCULATE RESUME SCORE
    # ========================================================

    try:

        score_data = calculate_resume_score(
            resume_data
        )

    except Exception as exc:

        return {
            "status": "ERROR",

            "message": (
                "Resume score analyzer failed: "
                f"{type(exc).__name__}: {exc}"
            ),

            "user_email": user_email,
        }

    if not isinstance(
        score_data,
        dict,
    ):

        return {
            "status": "ERROR",

            "message": (
                "Resume score analyzer returned invalid data."
            ),

            "user_email": user_email,
        }

    if score_data.get("status") != "OK":

        return score_data

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "status": "OK",

        "user_email": user_email,

        "student": resume_data.get(
            "student"
        ),

        "resume_score": {

            "score": score_data.get(
                "score"
            ),

            "max_score": score_data.get(
                "max_score"
            ),

            "breakdown": score_data.get(
                "breakdown"
            ),

            "suggestions": score_data.get(
                "suggestions"
            ),
        },
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    import json

    print(
        "=========================================="
    )

    print(
        "User-specific Resume Tool Test"
    )

    print(
        "=========================================="
    )

    email = input(
        "Enter user email: "
    ).strip()

    result = run_resume_tool(
        email
    )

    print()

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )