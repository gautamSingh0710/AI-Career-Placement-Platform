"""
Talk to the Azure AI Agent.

Used by:
    1. Terminal
    2. FastAPI backend

Each user gets a separate conversation.

User-specific resume flow:

Logged-in user email
        ↓
run_turn(..., user_email)
        ↓
run_tool(tool_name, args, user_email)
        ↓
agent_tools.py
        ↓
resume_tools.py
        ↓
users/<user_id>/resume.pdf
"""

import json

from openai.types.responses.response_input_param import FunctionCallOutput

from agent_tools import AGENT_NAME, run_tool


# ============================================================
# SAFETY LIMIT
# ============================================================

MAX_TOOL_ROUNDS = 5


# ============================================================
# SAFE VALUE READER
# ============================================================

def get_value(item, key, default=None):
    """
    Safely read a value from:
    - Azure/OpenAI SDK objects
    - dictionaries
    """

    if isinstance(item, dict):
        return item.get(key, default)

    return getattr(item, key, default)


# ============================================================
# RUN ONE AGENT TURN
# ============================================================

def run_turn(
    openai,
    conversation_id,
    user_text,
    user_email=None,
):
    """
    Sends one user message to the Azure AI Agent.

    Parameters:
        openai:
            Azure AI OpenAI client.

        conversation_id:
            Conversation ID for this user.

        user_text:
            User's message.

        user_email:
            Email of the currently logged-in user.

    Returns:
        Final text response from the agent.
    """

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not user_text or not user_text.strip():

        return "Please enter a message."

    user_text = user_text.strip()

    # --------------------------------------------------------
    # NORMALIZE USER EMAIL
    # --------------------------------------------------------

    if user_email:

        user_email = str(
            user_email
        ).strip().lower()

    # --------------------------------------------------------
    # AGENT REFERENCE
    # --------------------------------------------------------

    agent_ref = {

        "agent_reference": {

            "name": AGENT_NAME,

            "type": "agent_reference",
        }
    }

    # --------------------------------------------------------
    # USER CONTEXT
    # --------------------------------------------------------

    if user_email:

        input_text = (

            f"{user_text}\n\n"

            f"CURRENT LOGGED-IN USER EMAIL: "
            f"{user_email}\n"

            "Use this email as the user identifier when "
            "calling user-specific backend tools. "
            "Do not ask the user to provide a resume path."
        )

    else:

        input_text = user_text

    # --------------------------------------------------------
    # FIRST AGENT REQUEST
    # --------------------------------------------------------

    response = openai.responses.create(

        input=input_text,

        conversation=conversation_id,

        extra_body=agent_ref,
    )

    # --------------------------------------------------------
    # TOOL LOOP
    # --------------------------------------------------------

    for round_number in range(
        MAX_TOOL_ROUNDS
    ):

        tool_outputs = []

        # ----------------------------------------------------
        # READ AGENT RESPONSE
        # ----------------------------------------------------

        for item in response.output:

            item_type = get_value(
                item,
                "type",
            )

            # ------------------------------------------------
            # ONLY FUNCTION CALLS
            # ------------------------------------------------

            if item_type != "function_call":

                continue

            # ------------------------------------------------
            # FUNCTION CALL DETAILS
            # ------------------------------------------------

            tool_name = get_value(
                item,
                "name",
            )

            call_id = get_value(
                item,
                "call_id",
            )

            arguments_text = get_value(
                item,
                "arguments",
                "{}",
            )

            # ------------------------------------------------
            # SAFETY CHECK
            # ------------------------------------------------

            if not tool_name:

                continue

            if not call_id:

                continue

            # ------------------------------------------------
            # PARSE TOOL ARGUMENTS
            # ------------------------------------------------

            try:

                if isinstance(
                    arguments_text,
                    str,
                ):

                    args = json.loads(
                        arguments_text or "{}"
                    )

                elif isinstance(
                    arguments_text,
                    dict,
                ):

                    args = arguments_text.copy()

                else:

                    args = {}

            except (
                json.JSONDecodeError,
                TypeError,
            ):

                args = {}

            # ------------------------------------------------
            # MAKE SURE ARGS IS A DICTIONARY
            # ------------------------------------------------

            if not isinstance(
                args,
                dict,
            ):

                args = {}

            # ------------------------------------------------
            # RUN LOCAL TOOL
            #
            # IMPORTANT:
            #
            # user_email is NOT added to args.
            #
            # The FunctionTool schemas do not expose
            # user_email to the LLM.
            #
            # Instead, the backend receives it separately.
            # ------------------------------------------------

            try:

                result = run_tool(

                    tool_name,

                    args,

                    user_email,
                )

            except Exception as error:

                result = {

                    "status": "ERROR",

                    "error": str(error),
                }

            # ------------------------------------------------
            # ENSURE TOOL RESULT IS SERIALIZABLE
            # ------------------------------------------------

            try:

                result_json = json.dumps(

                    result,

                    default=str,
                )

            except Exception as error:

                result_json = json.dumps({

                    "status": "ERROR",

                    "error": (
                        "Tool result could not be "
                        f"serialized: {str(error)}"
                    ),
                })

            # ------------------------------------------------
            # CREATE FUNCTION CALL OUTPUT
            # ------------------------------------------------

            tool_output = FunctionCallOutput(

                type="function_call_output",

                call_id=call_id,

                output=result_json,
            )

            tool_outputs.append(
                tool_output
            )

        # ----------------------------------------------------
        # NO TOOL CALL
        # ----------------------------------------------------

        if not tool_outputs:

            final_answer = response.output_text

            if final_answer:

                return final_answer

            return (
                "The agent did not return a response."
            )

        # ----------------------------------------------------
        # SEND TOOL RESULTS BACK TO AGENT
        # ----------------------------------------------------

        response = openai.responses.create(

            input=tool_outputs,

            conversation=conversation_id,

            extra_body=agent_ref,
        )

    # --------------------------------------------------------
    # MAX TOOL ROUNDS
    # --------------------------------------------------------

    return (
        "The agent reached the maximum number of "
        "tool rounds without producing a final response."
    )


# ============================================================
# TERMINAL MODE
# ============================================================

def main():

    from azure.ai.projects import AIProjectClient

    from azure.identity import DefaultAzureCredential

    from agent_tools import PROJECT_ENDPOINT

    # --------------------------------------------------------
    # CONNECT TO AZURE
    # --------------------------------------------------------

    print(
        "Connecting to Azure AI Project..."
    )

    project = AIProjectClient(

        endpoint=PROJECT_ENDPOINT,

        credential=DefaultAzureCredential(),
    )

    openai = project.get_openai_client()

    # --------------------------------------------------------
    # CREATE TERMINAL CONVERSATION
    # --------------------------------------------------------

    conversation = (
        openai.conversations.create()
    )

    print()

    print(
        "=========================================="
    )

    print(
        f"Connected to agent: {AGENT_NAME}"
    )

    print(
        f"Conversation ID: {conversation.id}"
    )

    print(
        "Terminal mode has no logged-in user."
    )

    print(
        "Use FastAPI/frontend for user-specific "
        "resume operations."
    )

    print(
        "Type 'exit' to quit."
    )

    print(
        "=========================================="
    )

    print()

    # --------------------------------------------------------
    # TERMINAL CHAT LOOP
    # --------------------------------------------------------

    try:

        while True:

            try:

                text = input(
                    "You: "
                ).strip()

            except (
                KeyboardInterrupt,
                EOFError,
            ):

                print()

                break

            # ------------------------------------------------
            # EXIT
            # ------------------------------------------------

            if text.lower() in {

                "exit",

                "quit",

            }:

                break

            # ------------------------------------------------
            # EMPTY MESSAGE
            # ------------------------------------------------

            if not text:

                continue

            # ------------------------------------------------
            # RUN AGENT
            #
            # No user_email in terminal mode.
            # Therefore user-specific tools will return
            # USER_EMAIL_REQUIRED.
            # ------------------------------------------------

            try:

                answer = run_turn(

                    openai,

                    conversation.id,

                    text,
                )

                print()

                print(
                    "Agent:"
                )

                print(
                    answer
                )

                print()

            except Exception as error:

                print()

                print(
                    "========== ERROR =========="
                )

                print(
                    type(error).__name__
                )

                print(
                    str(error)
                )

                print()

    finally:

        # ----------------------------------------------------
        # DELETE TERMINAL CONVERSATION
        # ----------------------------------------------------

        try:

            openai.conversations.delete(

                conversation_id=conversation.id
            )

            print(
                "Conversation deleted."
            )

        except Exception as error:

            print(
                "Could not delete conversation: "
                f"{str(error)}"
            )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()