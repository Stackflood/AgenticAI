#!/usr/bin/env python3
import sys
print("Testing qa_agent import...", file=sys.stderr)

try:
    from qa_agent import qa_agent, QuestionAnswerPlan
    print("Import successful!", file=sys.stderr)
    print(f"qa_agent: {qa_agent}", file=sys.stderr)
    print(f"QuestionAnswerPlan: {QuestionAnswerPlan}", file=sys.stderr)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
