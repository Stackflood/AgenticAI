import gradio as gr
from typing import Callable
from agents import Runner
from research_pipeline import qa_agent, QuestionAnswerPlan

# Initial user query
# user_query = "Find India's largest by benefeciaries religious food distribution programs"

async def start_clarification(user_query: str, how_many: int = 3):
    """Dynamically generates clarifying questions based on any user query."""
    if not user_query.strip():
        return (
            [], 0, [],
            [{"role": "assistant", "content": "Please enter a valid research topic to begin."}],
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False)
        )

    task_prompt = f"Initial user query: \"{user_query}\"\nGenerate exactly {how_many} clarifying questions."
    
    try:
        result = await Runner.run(qa_agent, task_prompt)
        plan: QuestionAnswerPlan = result.final_output
        questions = plan.questions

        first_q = questions[0]
        chat_history = [
            {"role": "user", "content": f"**Research Topic:** {user_query}"},
            {"role": "assistant", "content": f"**Question 1 of {len(questions)}:**\n{first_q}"}
        ]

        return (
            questions, 0, [], chat_history,
            gr.update(visible=True),   # show chat container
            gr.update(visible=False),  # hide query row
            gr.update(visible=False)   # hide report
        )
    except Exception as e:
        return (
            [], 0, [],
            [{"role": "assistant", "content": f"Error generating questions: {str(e)}"}],
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False)
        )

def handle_user_answer(user_input: str, questions: list[str], curr_idx: int, answers: list[tuple[str, str]], chat_history: list[dict]):
    """Collects individual user answers and advances the interactive dialogue."""
    if not user_input.strip():
        return chat_history, "", curr_idx, answers, gr.update(visible=True), gr.update(visible=False), []

    current_question = questions[curr_idx]
    updated_answers = answers + [(current_question, user_input.strip())]
    chat_history.append({"role": "user", "content": user_input.strip()})
    next_idx = curr_idx + 1

    if next_idx < len(questions):
        next_question = questions[next_idx]
        chat_history.append({
            "role": "assistant",
            "content": f"**Question {next_idx + 1} of {len(questions)}:**\n{next_question}"
        })
        return (
            chat_history, "", next_idx, updated_answers,
            gr.update(visible=True),
            gr.update(visible=False),
            []
        )
    else:
        chat_history.append({
            "role": "assistant",
            "content": "All clarifications received! Starting Deep Research pipeline..."
        })
        return (
            chat_history, "", next_idx, updated_answers,
            gr.update(visible=False), # hide chat input row
            gr.update(visible=True),  # show research markdown
            updated_answers           # populate final payload
        )

def build_ui(research_fn: Callable) -> gr.Blocks:
    """Builds the dynamic Gradio interface."""
    with gr.Blocks(title="Deep Research AI") as ui:
        gr.Markdown("## 🔍 Deep Research Orchestrator")
        gr.Markdown("Enter any topic. The QA agent will ask targeted questions to refine your inquiry before researching.")

        # States
        questions_state = gr.State([])
        current_index_state = gr.State(0)
        answers_state = gr.State([])
        final_payload_state = gr.State([])

        # 1. Query & Recipient Row
        with gr.Column() as query_row:
            with gr.Row():
                query_textbox = gr.Textbox(
                    placeholder="Enter any research topic (e.g., 'Find the best food available in South Asia')...",
                    label="Research Topic",
                    scale=4,
                    autofocus=True
                )
                email_textbox = gr.Textbox(
                    placeholder="Optional: Enter email to receive report...",
                    label="Recipient Email",
                    scale=2
                )
            run_button = gr.Button("Start Clarification", variant="primary")

        # 2. Clarification Dialogue UI
        with gr.Column(visible=False) as chat_container:
            chatbot = gr.Chatbot(label="Clarification Dialogue", height=340)
            with gr.Row() as chat_input_row:
                user_answer_input = gr.Textbox(
                    placeholder="Type your answer here...",
                    show_label=False,
                    scale=8,
                    container=False
                )
                submit_answer_btn = gr.Button("Reply", variant="primary", scale=2)

        # 3. Final Research Report Output
        report = gr.Markdown(visible=False)

        # --- Bindings ---

        query_textbox.submit(
            start_clarification,
            inputs=[query_textbox],
            outputs=[questions_state, current_index_state, answers_state, chatbot, chat_container, query_row, report]
        )
        run_button.click(
            start_clarification,
            inputs=[query_textbox],
            outputs=[questions_state, current_index_state, answers_state, chatbot, chat_container, query_row, report]
        )

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

        for event in submit_events:
            event.then(
                lambda payload: gr.update(visible=bool(payload)),
                inputs=[final_payload_state],
                outputs=[report]
            ).then(
                research_fn,
                inputs=[query_textbox, email_textbox, final_payload_state],
                outputs=[report]
            )

    return ui