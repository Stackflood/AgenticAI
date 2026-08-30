import os
import gradio as gr
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from agents import Agent, Runner, OpenAIChatCompletionsModel

# Define Structured Output Schema
class QuestionAnswerPlan(BaseModel):
    questions: list[str] = Field(
        description="List of clear, targeted clarifying questions to ask the user."
    )

# Prompt Instructions
INSTRUCTIONS = """
You are an expert QA assistant. Your task is to generate clarifying questions to resolve ambiguities in the user's query.
Generate clear, single-point questions without conversational filler.
"""

# Configure Async Gemini Client
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=GOOGLE_API_KEY)

# Initialize Gemini Model
gemini_model = OpenAIChatCompletionsModel(
    model="gemini-3.1-flash-lite",
    openai_client=gemini_client
)

# Initialize QA Agent
qa_agent = Agent(
    name="QA Agent",
    instructions=INSTRUCTIONS,
    model=gemini_model,
    output_type=QuestionAnswerPlan
)

async def start_clarification(user_query: str, how_many: int = 3):
    """Executes the agent to generate questions and initialises the chat interface."""
    if not user_query.strip():
        return (
            [], 0, [],
            [{"role": "assistant", "content": "Please enter a valid query to begin."}],
            gr.update(visible=False), # chat_container
            gr.update(visible=True),  # query_row
            gr.update(visible=False)  # report container
        )

    task_prompt = f"""
    Initial user query: "{user_query}"
    Generate exactly {how_many} clarifying questions for this query.
    """

    try:
        result = await Runner.run(qa_agent, task_prompt)
        plan: QuestionAnswerPlan = result.final_output
        questions = plan.questions

        first_q = questions[0]
        # Dict messages format: [{"role": "user"|"assistant", "content": "..."}]
        chat_history = [
            {"role": "user", "content": f"**Research Topic:** {user_query}"},
            {"role": "assistant", "content": f"**Question 1 of {len(questions)}:**\n{first_q}"}
        ]

        return (
            questions,                # questions_state
            0,                        # current_index_state
            [],                       # answers_state
            chat_history,             # chatbot UI
            gr.update(visible=True),  # chat_container (show)
            gr.update(visible=False), # query_row (hide)
            gr.update(visible=False)  # report container (hide)
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
    """Collects answers one by one and transitions to the research phase once complete."""
    if not user_input.strip():
        return chat_history, "", curr_idx, answers, gr.update(visible=True), gr.update(visible=False), []

    current_question = questions[curr_idx]
    updated_answers = answers + [(current_question, user_input.strip())]
    
    # Append the user's response
    chat_history.append({"role": "user", "content": user_input.strip()})
    next_idx = curr_idx + 1

    if next_idx < len(questions):
        next_question = questions[next_idx]
        chat_history.append({
            "role": "assistant",
            "content": f"**Question {next_idx + 1} of {len(questions)}:**\n{next_question}"
        })
        return (
            chat_history,
            "",
            next_idx,
            updated_answers,
            gr.update(visible=True),  # keep chat active
            gr.update(visible=False), # report hidden
            []                        # payload empty
        )
    else:
        chat_history.append({
            "role": "assistant",
            "content": "All clarifying questions answered. Starting Deep Research..."
        })
        return (
            chat_history,
            "",
            next_idx,
            updated_answers,
            gr.update(visible=False), # hide chat input row
            gr.update(visible=True),  # show research report container
            updated_answers           # final Q&A payload passed downstream
        )