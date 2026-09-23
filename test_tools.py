"""Run with:  python test_tools.py
Tests the tool dispatcher and the tool loop WITHOUT Azure (uses a fake client)."""

import json
from types import SimpleNamespace

import agent_tools
from agent_tools import FUNCTION_TOOLS, run_tool
from chat import run_turn

passed = 0


def check(name, condition):
    global passed
    assert condition, f"FAILED: {name}"
    passed += 1
    print(f"  ok  {name}")


print("run_tool")
r = run_tool("check_eligibility", {"company_name": "TechNova"})
check("TechNova for demo student (CGPA 7.2, CSE) is ELIGIBLE", r["status"] == "ELIGIBLE")
check("CloudPeak for demo student is NOT_ELIGIBLE (CGPA < 8.0)",
      run_tool("check_eligibility", {"company_name": "CloudPeak"})["status"] == "NOT_ELIGIBLE")
check("Infosys -> COMPANY_NOT_FOUND",
      run_tool("check_eligibility", {"company_name": "Infosys"})["status"] == "COMPANY_NOT_FOUND")
check("Missing company_name -> INVALID_INPUT", run_tool("check_eligibility", {})["status"] == "INVALID_INPUT")
check("Empty company_name -> INVALID_INPUT",
      run_tool("check_eligibility", {"company_name": "  "})["status"] == "INVALID_INPUT")
check("Model cannot override the profile (extra cgpa arg is ignored)",
      run_tool("check_eligibility", {"company_name": "CloudPeak", "cgpa": 9.9})["status"] == "NOT_ELIGIBLE")
check("Unknown tool -> ERROR", run_tool("delete_everything", {})["status"] == "ERROR")
lst = run_tool("find_eligible_companies", {})
check("find_eligible_companies returns the 3 groups",
      set(lst) == {"eligible", "not_eligible", "needs_more_info"})
check("Demo student: eligible for TechNova, CodeCraft, FinEdge only",
      sorted(c["company"] for c in lst["eligible"])
      == ["CodeCraft Systems", "FinEdge Software", "TechNova Solutions"])

print("Tool schemas")
names = [t.name for t in FUNCTION_TOOLS]
check("Eligibility tools registered first", names[:2] == ["check_eligibility", "find_eligible_companies"])
check("Schemas are strict", all(t.strict is True for t in FUNCTION_TOOLS))


# ---- Fake Foundry client: first reply asks for a tool, second reply is the answer ----
class FakeResponses:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.script.pop(0)


def fake_client(script):
    return SimpleNamespace(responses=FakeResponses(script))


def tool_call(name, args, call_id="call_1"):
    return SimpleNamespace(type="function_call", name=name,
                           arguments=json.dumps(args), call_id=call_id)


print("run_turn (tool loop)")
client = fake_client([
    SimpleNamespace(output=[tool_call("check_eligibility", {"company_name": "TechNova"})], output_text=""),
    SimpleNamespace(output=[SimpleNamespace(type="message")], output_text="FINAL ANSWER"),
])
text = run_turn(client, "conv_1", "TechNova ke liye eligible hu?")
check("Final text is returned", text == "FINAL ANSWER")
second = client.responses.calls[1]
sent = second["input"][0]
check("Tool output sent back with the right call_id", sent["call_id"] == "call_1")
check("Tool output is valid JSON with a status", json.loads(sent["output"])["status"] == "ELIGIBLE")
check("Same conversation is reused", second["conversation"] == "conv_1")

client = fake_client([
    SimpleNamespace(output=[SimpleNamespace(type="message")], output_text="No tool needed"),
])
check("No tool call -> answer returned directly", run_turn(client, "conv_2", "hi") == "No tool needed")

client = fake_client([
    SimpleNamespace(output=[SimpleNamespace(type="function_call", name="check_eligibility",
                                            arguments="{bad json", call_id="c9")], output_text=""),
    SimpleNamespace(output=[], output_text="handled"),
])
check("Bad JSON arguments do not crash the loop", run_turn(client, "conv_3", "x") == "handled")

print(f"\nAll {passed} tests passed.")
