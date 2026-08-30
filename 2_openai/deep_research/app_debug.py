import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from styles import CSS, JS, EXAMPLES, HEADER_HTML
import sys

print("Loading environment...", file=sys.stderr, flush=True)
load_dotenv(override=True)
print("Environment loaded", file=sys.stderr, flush=True)

async def run(query: str):
    print(f"Running query: {query}", file=sys.stderr, flush=True)
    async for status_update in ResearchManager().run(query):
        yield status_update

print("Creating Gradio Blocks...", file=sys.stderr, flush=True)
try:
    with gr.Blocks(title="Deep Research") as ui:
        gr.HTML(HEADER_HTML)

        with gr.Row(elem_classes="dr-query-row"):
            query_textbox = gr.Textbox(
                placeholder="Type a research question...",
                show_label=False,
                container=False,
                autofocus=True,
                elem_id="dr-query",
                scale=5,
            )
            run_button = gr.Button("Investigate", variant="primary", elem_id="dr-run", scale=1)

        gr.HTML('<div class="dr-examples-label">Try one</div>')
        gr.Examples(examples=EXAMPLES, inputs=query_textbox, elem_id="dr-examples")

        report = gr.Markdown(elem_id="dr-report")

        run_button.click(run, inputs=query_textbox, outputs=report)
        query_textbox.submit(run, inputs=query_textbox, outputs=report)

    print("Gradio Blocks created successfully", file=sys.stderr, flush=True)
except Exception as e:
    print(f"ERROR creating Gradio Blocks: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

print("Launching Gradio UI...", file=sys.stderr, flush=True)
if __name__ == "__main__":
    try:
        ui.launch(css=CSS, js=JS, theme=gr.themes.Base(), share=True)
    except Exception as e:
        print(f"ERROR launching: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
