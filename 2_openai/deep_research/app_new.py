import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from styles import CSS, JS, EXAMPLES, HEADER_HTML
from qa_agent import start_clarification, handle_user_answer

load_dotenv(override=True)

async def run_research(query: str, qa_payload: list[tuple[str, str]]):
    """Streams the deep research status updates to the report markdown."""
    async for status_update in ResearchManager().run(query=query, qa_payload=qa_payload):
        yield status_update

async def on_start(query: str):
    """Asynchronously starts the clarification agent."""
    return await start_clarification(query, how_many=3)

with gr.Blocks(title="Deep Research") as ui:
    gr.HTML(HEADER_HTML)

    # State containers
    questions_state = gr.State([])
    current_index_state = gr.State(0)
    answers_state = gr.State([])
    final_payload_state = gr.State([])

    # 1. Query Input Row
    with gr.Row(elem_classes="dr-query-row") as query_row:
        query_textbox = gr.Textbox(
            placeholder="Type a research question...",
            show_label=False,
            container=False,
            autofocus=True,
            elem_id="dr-query",
            scale=5,
        )
        run_button = gr.Button("Investigate", variant="primary", elem_id="dr-run", scale=1)

    examples_wrapper = gr.Column(visible=True)
    with examples_wrapper:
        gr.HTML('<div class="dr-examples-label">Try one</div>')
        gr.Examples(examples=EXAMPLES, inputs=query_textbox, elem_id="dr-examples")

    # 2. Interactive Clarification Conversation UI
    with gr.Column(visible=False) as chat_container:
        chatbot = gr.Chatbot(label="Clarification Dialogue", height=320)
        with gr.Row() as chat_input_row:
            user_answer_input = gr.Textbox(
                placeholder="Type your clarification answer...", 
                show_label=False, 
                scale=8,
                container=False
            )
            submit_answer_btn = gr.Button("Reply", variant="primary", scale=2)

    # 3. Final Research Report Output
    report = gr.Markdown(elem_id="dr-report", visible=False)

    # --- Event Bindings ---

    # Step A: User initiates query -> Run async on_start
    query_textbox.submit(
        on_start,
        inputs=[query_textbox],
        outputs=[questions_state, current_index_state, answers_state, chatbot, chat_container, query_row, report]
    )
    run_button.click(
        on_start,
        inputs=[query_textbox],
        outputs=[questions_state, current_index_state, answers_state, chatbot, chat_container, query_row, report]
    )

    # Step B: User answers each question -> Advances turn
    submit_events = [
        submit_answer_btn.click(
            handle_user_answer,
            inputs=[user_answer_input, questions_state, current_index_state, answers_state, chatbot],
            outputs=[chatbot, user_answer_input, current_index_state, answers_state, chat_input_row, report, final_payload_state]
        ),
        user_answer_input.submit(
            handle_user_answer,
            inputs=[user_answer_input, questions_state, current_index_state, answers_state, chatbot],
            outputs=[chatbot, user_answer_input, current_index_state, answers_state, chat_input_row, report, final_payload_state]
        )
    ]

    # Step C: Once all answers are collected -> Launch ResearchManager
    for event in submit_events:
        event.then(
            lambda payload: gr.update(visible=bool(payload)),
            inputs=[final_payload_state],
            outputs=[report]
        ).then(
            run_research,
            inputs=[query_textbox, final_payload_state],
            outputs=[report]
        )

if __name__ == "__main__":
    ui.launch(css=CSS, js=JS, theme=gr.themes.Base(), share=True)