"""
Tool definitions + backend dispatcher for StudentCareerAgent.

Architecture
------------

1. Student Profile
   - Student data comes from STUDENT_PROFILE.
   - LLM calls get_student_profile for profile questions.

2. Eligibility
   - LLM provides company name only.
   - Backend uses STUDENT_PROFILE.

3. Resume Scoring
   - Backend receives logged-in user's email.
   - Backend selects that user's resume automatically.

4. JD Analysis
   - LLM provides JD text.
   - Backend calls jd_analyzer.py.

5. Resume-JD Matching

   JD text
       ↓
   JD Analyzer
       ↓
   Logged-in user's Resume
       ↓
   Resume-JD Matcher
       ↓
   Deterministic match result

6. Skill Gap Analysis

   JD text
       ↓
   Logged-in user's Resume
       ↓
   Resume-JD Matcher
       ↓
   Skill Gap Analyzer
       ↓
   Deterministic skill-gap result

IMPORTANT
---------

The LLM does NOT calculate:

- match percentage
- missing skills
- skill gaps
- learning resources

Those are calculated by backend code.

The LLM also does NOT provide a resume path.
The backend selects the resume using user_email.
"""

from azure.ai.projects.models import FunctionTool


# ============================================================================
# BACKEND IMPORTS
# ============================================================================

from eligibility import (
    check_eligibility,
    find_eligible_companies,
)

from resume_tools import (
    RESUME_TOOL,
    run_resume_tool,
)

from jd_analyzer import (
    ANALYZE_JD_TOOL,
    run_jd_tool,
)

from resume_jd_matcher import (
    match_resume_with_jd,
)

from skill_gap_analyzer import (
    analyze_skill_gaps,
)


# ============================================================================
# AZURE / AGENT CONFIGURATION
# ============================================================================

PROJECT_ENDPOINT = (
    "https://tenacious.services.ai.azure.com/api/projects/FutureHeros"
)

MODEL = "gpt-5-mini"

AGENT_NAME = "StudentCareerAgentTools"

KB_SOURCE_AGENT = "StudentCareerAgent"


# ============================================================================
# STUDENT PROFILE
# ============================================================================

STUDENT_PROFILE = {

    "name": "Gautam Singh",

    "cgpa": 8.79,

    "branch": "CSE",

    "active_backlogs": 0,

    "tenth_percent": 87,

    "twelfth_percent": 88.6,

    "has_backlog_history": False,

    "attendance_percent": 82,

    "skills": [
        "Java",
        "Python",
        "C++",
        "SQL",
        "Git",
        "GitHub",
        "Django",
        "OOP",
    ],

    "qualifications": [
        "B.Tech",
        "Computer Science",
    ],
}


# ============================================================================
# GET STUDENT PROFILE TOOL
# ============================================================================

GET_STUDENT_PROFILE_TOOL = FunctionTool(

    name="get_student_profile",

    description=(
        "Get the student's saved academic and placement profile. "
        "Use this tool whenever the student asks for their CGPA, branch, "
        "10th percentage, 12th percentage, active backlogs, attendance, "
        "skills, qualifications, or other saved profile information. "
        "The backend contains the student's profile. "
        "Always call this tool for profile-based questions."
    ),

    parameters={

        "type": "object",

        "properties": {},

        "required": [],

        "additionalProperties": False,
    },

    strict=True,
)


# ============================================================================
# CHECK ONE COMPANY ELIGIBILITY TOOL
# ============================================================================

CHECK_ELIGIBILITY_TOOL = FunctionTool(

    name="check_eligibility",

    description=(
        "Check whether the current student is eligible for ONE company "
        "using the student's saved profile. "
        "The backend evaluates CGPA, branch, backlogs, school percentages, "
        "attendance and other configured eligibility criteria. "
        "The model must not calculate eligibility itself."
    ),

    parameters={

        "type": "object",

        "properties": {

            "company_name": {

                "type": "string",

                "description": (
                    "Company name exactly as provided by the student."
                ),
            },
        },

        "required": [
            "company_name",
        ],

        "additionalProperties": False,
    },

    strict=True,
)


# ============================================================================
# FIND ALL ELIGIBLE COMPANIES TOOL
# ============================================================================

FIND_ELIGIBLE_COMPANIES_TOOL = FunctionTool(

    name="find_eligible_companies",

    description=(
        "Find companies for which the current student is eligible "
        "using the saved student profile. "
        "Use this when the student asks which companies they can apply to "
        "or asks about placement eligibility in general. "
        "The backend performs the eligibility checks."
    ),

    parameters={

        "type": "object",

        "properties": {},

        "required": [],

        "additionalProperties": False,
    },

    strict=True,
)


# ============================================================================
# MATCH RESUME WITH JD TOOL
# ============================================================================

MATCH_RESUME_JD_TOOL = FunctionTool(

    name="match_resume_jd",

    description=(
        "Compare the currently logged-in student's actual saved resume "
        "against a complete Job Description. "
        "The backend automatically selects the resume belonging to the "
        "logged-in user's email. "
        "The backend analyzes the JD, reads the user's resume, and "
        "deterministically calculates the resume-JD match. "
        "Returns match percentage, match level, matched skills, "
        "missing skills, qualification match and skill gaps. "
        "The model must never calculate or invent the match percentage."
    ),

    parameters={

        "type": "object",

        "properties": {

            "jd_text": {

                "type": "string",

                "description": (
                    "The complete Job Description provided by the student."
                ),
            },
        },

        "required": [
            "jd_text",
        ],

        "additionalProperties": False,
    },

    strict=True,
)


# ============================================================================
# SKILL GAP TOOL
# ============================================================================

SKILL_GAP_TOOL = FunctionTool(

    name="analyze_skill_gaps",

    description=(
        "Analyze the currently logged-in student's actual saved resume "
        "against a complete Job Description. "
        "The backend automatically selects the resume belonging to the "
        "logged-in user's email. "
        "The backend deterministically identifies missing required and "
        "preferred skills and provides configured learning resources. "
        "The model must not invent missing skills or learning resources."
    ),

    parameters={

        "type": "object",

        "properties": {

            "jd_text": {

                "type": "string",

                "description": (
                    "The complete Job Description provided by the student."
                ),
            },
        },

        "required": [
            "jd_text",
        ],

        "additionalProperties": False,
    },

    strict=True,
)


# ============================================================================
# INITIAL FUNCTION TOOLS
# ============================================================================

FUNCTION_TOOLS = [

    GET_STUDENT_PROFILE_TOOL,

    CHECK_ELIGIBILITY_TOOL,

    FIND_ELIGIBLE_COMPANIES_TOOL,

    RESUME_TOOL,

    ANALYZE_JD_TOOL,

    MATCH_RESUME_JD_TOOL,

    SKILL_GAP_TOOL,
]


# ============================================================================
# PROFILE BACKEND
# ============================================================================

def get_student_profile():

    return {

        "status": "OK",

        "student": {

            "name": STUDENT_PROFILE["name"],

            "cgpa": STUDENT_PROFILE["cgpa"],

            "branch": STUDENT_PROFILE["branch"],

            "active_backlogs": (
                STUDENT_PROFILE["active_backlogs"]
            ),

            "tenth_percent": (
                STUDENT_PROFILE["tenth_percent"]
            ),

            "twelfth_percent": (
                STUDENT_PROFILE["twelfth_percent"]
            ),

            "has_backlog_history": (
                STUDENT_PROFILE["has_backlog_history"]
            ),

            "attendance_percent": (
                STUDENT_PROFILE["attendance_percent"]
            ),

            "skills": list(
                STUDENT_PROFILE["skills"]
            ),

            "qualifications": list(
                STUDENT_PROFILE["qualifications"]
            ),
        },
    }


# ============================================================================
# JD ANALYZER HELPER
# ============================================================================

def analyze_jd_backend(jd_text):

    if not isinstance(jd_text, str) or not jd_text.strip():

        return {

            "status": "INVALID_INPUT",

            "error": "jd_text is required",
        }

    try:

        result = run_jd_tool({

            "jd_text": jd_text,

        })

    except Exception as exc:

        return {

            "status": "ERROR",

            "error": (
                f"JD analyzer failed: "
                f"{type(exc).__name__}: {str(exc)}"
            ),
        }

    if not isinstance(result, dict):

        return {

            "status": "ERROR",

            "error": "JD analyzer returned invalid data",
        }

    return result


# ============================================================================
# RESUME-JD MATCH BACKEND
# ============================================================================

def run_match_resume_jd_tool(args, user_email=None):

    """
    Match the logged-in user's resume against a JD.

    user_email is supplied by the backend.
    The LLM never supplies a resume path.
    """

    # ------------------------------------------------------------------------
    # Validate arguments
    # ------------------------------------------------------------------------

    if not isinstance(args, dict):

        return {

            "status": "INVALID_INPUT",

            "error": "Arguments must be an object",
        }

    jd_text = args.get("jd_text")

    if not isinstance(jd_text, str) or not jd_text.strip():

        return {

            "status": "INVALID_INPUT",

            "error": "jd_text is required",
        }

    # ------------------------------------------------------------------------
    # Validate logged-in user
    # ------------------------------------------------------------------------

    if not user_email or not str(user_email).strip():

        return {

            "status": "USER_EMAIL_REQUIRED",

            "error": (
                "Logged-in user email is required "
                "for resume matching."
            ),
        }

    user_email = str(user_email).strip().lower()

    # ------------------------------------------------------------------------
    # STEP 1: Analyze JD
    # ------------------------------------------------------------------------

    jd_result = analyze_jd_backend(

        jd_text

    )

    if not isinstance(jd_result, dict):

        return {

            "status": "ERROR",

            "error": "JD analyzer returned invalid data",
        }

    if jd_result.get("status") != "OK":

        return jd_result

    # ------------------------------------------------------------------------
    # STEP 2: Read logged-in user's resume
    # ------------------------------------------------------------------------

    try:

        resume_result = run_resume_tool(

            user_email

        )

    except Exception as exc:

        return {

            "status": "ERROR",

            "error": (
                f"Resume analyzer failed: "
                f"{type(exc).__name__}: {str(exc)}"
            ),
        }

    if not isinstance(resume_result, dict):

        return {

            "status": "ERROR",

            "error": "Resume analyzer returned invalid data",
        }

    if resume_result.get("status") != "OK":

        return resume_result

    # ------------------------------------------------------------------------
    # STEP 3: Extract student data from user's resume
    # ------------------------------------------------------------------------

    resume_student = resume_result.get("student")

    if not isinstance(resume_student, dict):

        return {

            "status": "ERROR",

            "error": (
                "Student data could not be extracted from resume"
            ),
        }

    # ------------------------------------------------------------------------
    # STEP 4: Extract skills
    # ------------------------------------------------------------------------

    actual_skills = resume_student.get(

        "skills",

        [],

    )

    if not isinstance(actual_skills, list):

        actual_skills = []

    # ------------------------------------------------------------------------
    # STEP 5: Extract qualifications
    # ------------------------------------------------------------------------

    actual_qualifications = resume_student.get(

        "qualifications",

        [],

    )

    if not isinstance(actual_qualifications, list):

        actual_qualifications = []

    # ------------------------------------------------------------------------
    # STEP 6: Build matcher profile
    # ------------------------------------------------------------------------

    student_profile = {

        "name": resume_student.get(

            "name",

            "Student",

        ),

        "skills": actual_skills,

        "qualifications": actual_qualifications,
    }

    # ------------------------------------------------------------------------
    # STEP 7: Deterministic matching
    # ------------------------------------------------------------------------

    try:

        match_result = match_resume_with_jd(

            jd_result,

            student_profile,

        )

    except Exception as exc:

        return {

            "status": "ERROR",

            "error": (
                f"Resume-JD matcher failed: "
                f"{type(exc).__name__}: {str(exc)}"
            ),
        }

    # ------------------------------------------------------------------------
    # Validate matcher result
    # ------------------------------------------------------------------------

    if not isinstance(match_result, dict):

        return {

            "status": "ERROR",

            "error": (
                "Resume-JD matcher returned invalid data"
            ),
        }

    return match_result


# ============================================================================
# SKILL GAP BACKEND
# ============================================================================

def run_skill_gap_tool(args, user_email=None):

    """
    Analyze skill gaps using the logged-in user's resume.
    """

    # ------------------------------------------------------------------------
    # Validate arguments
    # ------------------------------------------------------------------------

    if not isinstance(args, dict):

        return {

            "status": "INVALID_INPUT",

            "error": "Arguments must be an object",
        }

    jd_text = args.get("jd_text")

    if not isinstance(jd_text, str) or not jd_text.strip():

        return {

            "status": "INVALID_INPUT",

            "error": "jd_text is required",
        }

    # ------------------------------------------------------------------------
    # Validate logged-in user
    # ------------------------------------------------------------------------

    if not user_email or not str(user_email).strip():

        return {

            "status": "USER_EMAIL_REQUIRED",

            "error": (
                "Logged-in user email is required "
                "for skill-gap analysis."
            ),
        }

    # ------------------------------------------------------------------------
    # STEP 1: Get user-specific resume-JD match
    # ------------------------------------------------------------------------

    match_result = run_match_resume_jd_tool(

        {
            "jd_text": jd_text,
        },

        user_email,

    )

    if not isinstance(match_result, dict):

        return {

            "status": "ERROR",

            "error": (
                "Resume-JD matcher returned invalid data"
            ),
        }

    if match_result.get("status") != "OK":

        return match_result

    # ------------------------------------------------------------------------
    # STEP 2: Analyze skill gaps
    # ------------------------------------------------------------------------

    try:

        skill_gap_result = analyze_skill_gaps(

            match_result,

        )

    except Exception as exc:

        return {

            "status": "ERROR",

            "error": (
                f"Skill gap analyzer failed: "
                f"{type(exc).__name__}: {str(exc)}"
            ),
        }

    # ------------------------------------------------------------------------
    # Validate result
    # ------------------------------------------------------------------------

    if not isinstance(skill_gap_result, dict):

        return {

            "status": "ERROR",

            "error": (
                "Skill gap analyzer returned invalid data"
            ),
        }

    return skill_gap_result


# ============================================================================
# MAIN TOOL DISPATCHER
# ============================================================================

def run_tool(name, args=None, user_email=None):

    """
    Main backend dispatcher.

    user_email:
        Email of the currently logged-in user.

    The backend uses this email only where user-specific resume
    data is required.

    Eligibility and the existing student profile remain unchanged.
    """

    try:

        # ====================================================================
        # GET STUDENT PROFILE
        # ====================================================================

        if name == "get_student_profile":

            return get_student_profile()


        # ====================================================================
        # CHECK ONE COMPANY
        # ====================================================================

        if name == "check_eligibility":

            if not isinstance(args, dict):

                return {

                    "status": "INVALID_INPUT",

                    "error": "Arguments must be an object",
                }

            company = args.get(

                "company_name"

            )

            if (
                not isinstance(company, str)
                or not company.strip()
            ):

                return {

                    "status": "INVALID_INPUT",

                    "error": "company_name is required",
                }

            return check_eligibility(

                company,

                cgpa=STUDENT_PROFILE["cgpa"],

                branch=STUDENT_PROFILE["branch"],

                active_backlogs=STUDENT_PROFILE[
                    "active_backlogs"
                ],

                tenth_percent=STUDENT_PROFILE[
                    "tenth_percent"
                ],

                twelfth_percent=STUDENT_PROFILE[
                    "twelfth_percent"
                ],

                has_backlog_history=STUDENT_PROFILE[
                    "has_backlog_history"
                ],

                attendance_percent=STUDENT_PROFILE[
                    "attendance_percent"
                ],
            )


        # ====================================================================
        # FIND ALL ELIGIBLE COMPANIES
        # ====================================================================

        if name == "find_eligible_companies":

            return find_eligible_companies(

                cgpa=STUDENT_PROFILE["cgpa"],

                branch=STUDENT_PROFILE["branch"],

                active_backlogs=STUDENT_PROFILE[
                    "active_backlogs"
                ],

                tenth_percent=STUDENT_PROFILE[
                    "tenth_percent"
                ],

                twelfth_percent=STUDENT_PROFILE[
                    "twelfth_percent"
                ],

                has_backlog_history=STUDENT_PROFILE[
                    "has_backlog_history"
                ],

                attendance_percent=STUDENT_PROFILE[
                    "attendance_percent"
                ],
            )


        # ====================================================================
        # SCORE USER'S RESUME
        # ====================================================================

        if name == "score_resume":

            return run_resume_tool(

                user_email

            )


        # ====================================================================
        # ANALYZE JD
        # ====================================================================

        if name == "analyze_jd":

            if not isinstance(args, dict):

                return {

                    "status": "INVALID_INPUT",

                    "error": "Arguments must be an object",
                }

            jd_text = args.get(

                "jd_text"

            )

            return analyze_jd_backend(

                jd_text

            )


        # ====================================================================
        # MATCH USER RESUME WITH JD
        # ====================================================================

        if name == "match_resume_jd":

            return run_match_resume_jd_tool(

                args,

                user_email,

            )


        # ====================================================================
        # USER-SPECIFIC SKILL GAP ANALYSIS
        # ====================================================================

        if name == "analyze_skill_gaps":

            return run_skill_gap_tool(

                args,

                user_email,

            )


        # ====================================================================
        # OPTIONAL LEGACY TOOLS
        # ====================================================================

        if name in {

            "match_jd",

            "skill_gap_analysis",

        }:

            return {

                "status": "ERROR",

                "error": (
                    f"Legacy tool '{name}' is not handled by "
                    "jd_analyzer.py. Use the dedicated "
                    "match_resume_jd or analyze_skill_gaps tool."
                ),
            }


        # ====================================================================
        # UNKNOWN TOOL
        # ====================================================================

        return {

            "status": "ERROR",

            "error": f"Unknown tool: {name}",
        }


    except Exception as exc:

        return {

            "status": "ERROR",

            "error": (
                f"Tool failed: "
                f"{type(exc).__name__}: "
                f"{str(exc)}"
            ),
        }


# ============================================================================
# OPTIONAL JD TOOLS
# ============================================================================

try:

    from jd_tools import JD_FUNCTION_TOOLS

except ImportError:

    JD_FUNCTION_TOOLS = []


# ============================================================================
# ADD OPTIONAL JD TOOLS WITHOUT DUPLICATES
# ============================================================================

existing_names = {

    getattr(

        existing,

        "name",

        None,

    )

    for existing in FUNCTION_TOOLS

}


for tool in JD_FUNCTION_TOOLS:

    tool_name = getattr(

        tool,

        "name",

        None,

    )

    if (

        tool_name

        and tool_name not in existing_names

    ):

        FUNCTION_TOOLS.append(

            tool

        )

        existing_names.add(

            tool_name

        )