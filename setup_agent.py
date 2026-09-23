"""
Run whenever you change instructions.txt or the tool schemas:

    python setup_agent.py

Creates a new version of the agent AGENT_NAME in your Foundry project with:
  - the instructions from instructions.txt
  - 3 function tools:
      1. check_eligibility
      2. find_eligible_companies
      3. score_resume
  - the placement knowledge-base tool (MCP), COPIED (read-only)
    from KB_SOURCE_AGENT

Web search and other unrelated tools are NOT copied.
"""

from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

from agent_tools import (
    AGENT_NAME,
    FUNCTION_TOOLS,
    KB_SOURCE_AGENT,
    MODEL,
    PROJECT_ENDPOINT,
)


# ---------------------------------------------------------------------------
# LOAD AGENT INSTRUCTIONS
# ---------------------------------------------------------------------------

INSTRUCTIONS = (
    Path(__file__)
    .with_name("instructions.txt")
    .read_text(encoding="utf-8")
)


# ---------------------------------------------------------------------------
# TOOL HELPERS
# ---------------------------------------------------------------------------

def tool_type(tool):
    """Return the tool type as plain text: function, mcp, etc."""

    value = getattr(tool, "type", None)

    if value is None and hasattr(tool, "get"):
        value = tool.get("type")

    return str(getattr(value, "value", value))


def tool_label(tool):
    """Return a readable label for logging."""

    kind = tool_type(tool)

    if kind == "function":
        return f"function:{getattr(tool, 'name', '?')}"

    label = (
        getattr(tool, "server_label", None)
        or (
            tool.get("server_label")
            if hasattr(tool, "get")
            else None
        )
    )

    return f"{kind}:{label}" if label else kind


# ---------------------------------------------------------------------------
# COPY KNOWLEDGE-BASE TOOLS
# ---------------------------------------------------------------------------

def copy_knowledge_tools(project, source_agent_name):
    """
    Read the latest version of the portal agent and return ONLY its MCP tools.

    The source agent is never modified.

    This allows the new agent to use the existing placement
    knowledge-base tool without copying unrelated tools such as web search.
    """

    if not source_agent_name:
        return []

    source = project.agents.get(
        agent_name=source_agent_name
    )

    tools = list(
        source.versions.latest.definition.tools or []
    )

    kb_tools = []
    seen = set()

    for tool in tools:

        # We only want MCP tools from the source agent.
        if tool_type(tool) != "mcp":
            continue

        label = tool_label(tool)

        # Avoid duplicate MCP server labels.
        if label in seen:
            continue

        seen.add(label)
        kb_tools.append(tool)

    return kb_tools


# ---------------------------------------------------------------------------
# CREATE AGENT VERSION
# ---------------------------------------------------------------------------

def main():

    if "PASTE_YOUR" in PROJECT_ENDPOINT:

        raise SystemExit(
            "Open agent_tools.py and set PROJECT_ENDPOINT first."
        )


    # ---------------------------------------------------------------
    # Connect to Foundry project
    # ---------------------------------------------------------------

    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )


    # ---------------------------------------------------------------
    # Copy placement Knowledge Base tool
    # ---------------------------------------------------------------

    try:

        kb_tools = copy_knowledge_tools(
            project,
            KB_SOURCE_AGENT,
        )

    except Exception as exc:

        kb_tools = []

        print(
            f"WARNING: could not read {KB_SOURCE_AGENT}: "
            f"{type(exc).__name__}: {exc}"
        )


    if not kb_tools:

        print(
            "WARNING: no knowledge-base tool copied. "
            "Placement-rule questions will NOT work."
        )


    # ---------------------------------------------------------------
    # Combine function tools + KB tools
    # ---------------------------------------------------------------

    tools = list(FUNCTION_TOOLS) + kb_tools


    # ---------------------------------------------------------------
    # Create new agent version
    # ---------------------------------------------------------------

    agent = project.agents.create_version(
        agent_name=AGENT_NAME,

        definition=PromptAgentDefinition(
            model=MODEL,
            instructions=INSTRUCTIONS,
            tools=tools,
        ),
    )


    # ---------------------------------------------------------------
    # Result
    # ---------------------------------------------------------------

    print(
        f"Agent ready: name={agent.name}, version={agent.version}"
    )

    print(
        "Tools:",
        ", ".join(tool_label(t) for t in tools)
    )


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()