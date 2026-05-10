"""Smoke test for RAG indexing and agent tool flow.

This script is runnable locally and does not require the Groq API or Streamlit.
It exercises:
- Indexing sample documents with `streamlit.rag`
- Retrieving top-k passages for a query
- Simulating a model CALL_TOOL tag and executing the safe `search_docs` tool
"""
from __future__ import annotations
import re
import os
import pprint

import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOCAL_STREAMLIT_DIR = os.path.join(REPO_ROOT, "streamlit")

# Ensure local app modules resolve before installed packages.
sys.path.insert(0, LOCAL_STREAMLIT_DIR)

import rag


def main() -> None:
    print("Smoke test: RAG indexing + simulated agent tool call")

    # Clear any existing store for a clean run
    rag.clear_store()

    docs = [
        "Company security policy:\nAll employees must use MFA and rotate keys every 90 days.",
        "Incident response plan:\nReport incidents to secops@example.com and preserve logs.",
        "Data handling:\nSensitive PII must be encrypted at rest and in transit.",
    ]

    print(f"Indexing {len(docs)} sample documents...")
    rag.index_texts(docs)

    query = "How often should keys be rotated?"
    print(f"Retrieving for query: {query!r}")
    results = rag.retrieve(query, top_k=3)
    pprint.pprint(results)

    # Simulate a model response that calls the search_docs tool
    simulated_model_output = f"Here is my plan:\n<CALL_TOOL name=\"search_docs\">{query}</CALL_TOOL>"
    print("\nSimulated model output: \n", simulated_model_output)

    # Extract tool call
    TOOL_PATTERN = re.compile(r'<CALL_TOOL name="(?P<name>\w+)">(?P<arg>.*?)</CALL_TOOL>', re.DOTALL)
    m = TOOL_PATTERN.search(simulated_model_output)
    if not m:
        print("No tool call detected in simulated output.")
        return

    tool = m.group("name")
    arg = m.group("arg").strip()
    print(f"Detected tool call: {tool} with arg: {arg!r}")

    tool_output = ""
    if tool == "search_docs":
        r = rag.retrieve(arg, top_k=3)
        if r:
            tool_output = "\n\n".join([f"[source {i}] (score={s:.3f})\n{t}" for i, s, t in r])
        else:
            tool_output = "(no relevant documents found)"
    else:
        tool_output = f"(unsupported tool: {tool})"

    print("\nTool output:\n", tool_output)

    # Simulate re-querying the model with TOOL_RESULT appended and printing final answer
    final_prompt = (
        f"User asked: {arg}\n\nTOOL_RESULT for {tool}:\n{tool_output}\n\n"
        "Based on the tool result, provide a concise final answer."
    )

    # Here we cannot call the real LLM; instead we generate a naive final answer
    # using a simple heuristic for the demo.
    if "rotate keys" in arg.lower() or "keys be rotated" in arg.lower():
        final_answer = "Keys should be rotated every 90 days according to the indexed policy."
    else:
        final_answer = "(simulate LLM final answer based on TOOL_RESULT)"

    print("\nFinal Answer:\n", final_answer)


if __name__ == "__main__":
    main()
