#!/usr/bin/env python3
import sys
import traceback

print("Step 1: Importing gradio", file=sys.stderr, flush=True)
try:
    import gradio as gr
    print("  SUCCESS", file=sys.stderr, flush=True)
except Exception as e:
    print(f"  ERROR: {e}", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)

print("Step 2: Importing dotenv", file=sys.stderr, flush=True)
try:
    from dotenv import load_dotenv
    print("  SUCCESS", file=sys.stderr, flush=True)
except Exception as e:
    print(f"  ERROR: {e}", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)

print("Step 3: Importing research_manager", file=sys.stderr, flush=True)
try:
    from research_manager import ResearchManager
    print("  SUCCESS", file=sys.stderr, flush=True)
except Exception as e:
    print(f"  ERROR: {e}", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)

print("Step 4: Importing styles", file=sys.stderr, flush=True)
try:
    from styles import CSS, JS, EXAMPLES, HEADER_HTML
    print("  SUCCESS", file=sys.stderr, flush=True)
except Exception as e:
    print(f"  ERROR: {e}", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)

print("All imports completed!", file=sys.stderr, flush=True)
