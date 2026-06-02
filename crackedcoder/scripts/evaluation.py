"""
Evaluation runner for skill output quality.

Usage:
    python scripts/evaluation.py evaluation.xml
    python scripts/evaluation.py -u https://example.com/endpoint evaluation.xml
    python scripts/evaluation.py -o report.md evaluation.xml

Reads <qa_pair> entries from an XML file, runs each question through
the skill, and scores results by exact string match.
"""

import argparse
import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path


EVALUATION_PROMPT = """You are evaluating a skill implementation. Answer the question using only
the tools and context available. Provide your final answer inside <response> tags.
Include a brief summary of your reasoning in <summary> tags.
If you encountered any issues, describe them in <feedback> tags."""


def parse_evaluation_file(path: str) -> list[dict]:
    """Parse <qa_pair> entries from an evaluation XML file."""
    tree = ET.parse(path)
    root = tree.getroot()
    pairs = []
    for pair in root.findall("qa_pair"):
        question = pair.findtext("question", "").strip()
        answer = pair.findtext("answer", "").strip()
        if question and answer:
            pairs.append({"question": question, "answer": answer})
    return pairs


def extract_tag(text: str, tag: str) -> str:
    """Extract content between <tag> and </tag>."""
    start = text.find(f"<{tag}>")
    end = text.find(f"</{tag}>")
    if start == -1 or end == -1:
        return ""
    return text[start + len(tag) + 2 : end].strip()


def score_answer(expected: str, actual: str) -> bool:
    return expected.strip().lower() == actual.strip().lower()


async def run_evaluation(eval_file: str, output_file: str | None = None):
    """
    TODO: wire up your skill's runner here.

    Replace the stub below with actual calls to your implementation,
    e.g. an MCP connection, a subprocess, or a direct function call.
    """
    pairs = parse_evaluation_file(eval_file)
    results = []

    for i, pair in enumerate(pairs, 1):
        print(f"[{i}/{len(pairs)}] {pair['question'][:80]}...")

        # --- STUB: replace with your skill invocation ---
        raw_response = f"<response>TODO</response><summary>Not implemented</summary>"
        # ------------------------------------------------

        actual = extract_tag(raw_response, "response")
        passed = score_answer(pair["answer"], actual)
        results.append(
            {
                "question": pair["question"],
                "expected": pair["answer"],
                "actual": actual,
                "passed": passed,
                "summary": extract_tag(raw_response, "summary"),
                "feedback": extract_tag(raw_response, "feedback"),
            }
        )
        print(f"  {'PASS' if passed else 'FAIL'} — expected: {pair['answer']!r}, got: {actual!r}")

    passed_count = sum(r["passed"] for r in results)
    accuracy = passed_count / len(results) if results else 0
    report = _build_report(results, accuracy)

    if output_file:
        Path(output_file).write_text(report)
        print(f"\nReport written to {output_file}")
    else:
        print(f"\n{report}")


def _build_report(results: list[dict], accuracy: float) -> str:
    lines = [f"# Evaluation Report\n", f"**Accuracy:** {accuracy:.0%} ({sum(r['passed'] for r in results)}/{len(results)})\n"]
    for i, r in enumerate(results, 1):
        status = "✅" if r["passed"] else "❌"
        lines.append(f"## {status} Case {i}\n**Q:** {r['question']}\n**Expected:** {r['expected']}\n**Got:** {r['actual']}")
        if r["feedback"]:
            lines.append(f"**Feedback:** {r['feedback']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run skill evaluations")
    parser.add_argument("eval_file", help="Path to evaluation XML file")
    parser.add_argument("-u", "--url", help="Endpoint URL (if applicable)")
    parser.add_argument("-o", "--output", help="Write markdown report to this file")
    args = parser.parse_args()
    asyncio.run(run_evaluation(args.eval_file, args.output))
