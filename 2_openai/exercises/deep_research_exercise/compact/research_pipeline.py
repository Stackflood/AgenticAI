import os
import json
from typing import List, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from messenger import send_email, push
from ddgs import DDGS

from agents import Agent, ModelSettings, Runner, OpenAIChatCompletionsModel, function_tool

load_dotenv()
USE_EMAIL = os.getenv("USE_EMAIL", "true").lower() == "true"

# --- 1. Client Setup (Groq OpenAI Endpoint) ---

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

groq_client = AsyncOpenAI(
    base_url=GROQ_BASE_URL,
    api_key=GROQ_API_KEY
)

model_openai = OpenAIChatCompletionsModel(
    model="openai/gpt-oss-120b",
    openai_client=groq_client
)

model_openai_small = OpenAIChatCompletionsModel(
    model="openai/gpt-oss-20b",
    openai_client=groq_client
)

# Best Spiritual Places to visit in india
model_qwen = OpenAIChatCompletionsModel(
    model="qwen/qwen3.8-27b",
    openai_client=groq_client
)

model_minimaxal = OpenAIChatCompletionsModel(
    model="minimaxai/minimax-m2.7",
    openai_client=groq_client
)

HOW_MANY_SEARCHES = 3

# --- 2. Schemas & Functions ---

class QuestionAnswerPlan(BaseModel):
    questions: List[str] = Field(
        description="Clarifying questions to resolve ambiguities in the query."
    )

class SearchItem(BaseModel):
    reason: str = Field(description="Why this search helps answer user intent.")
    query: str = Field(description="Targeted web search query.")

class PlannerOutput(BaseModel):
    searches: List[SearchItem]

@function_tool
def web_search(query: str) -> str:
    """Performs a live DuckDuckGo web search and returns concise text snippets."""
    try:
        with DDGS() as ddgs:
            # Reduce max_results and truncate body length to save tokens
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return f"No results found for query: {query}"
            
            snippets = [
                f"Title: {r.get('title')}\nSnippet: {r.get('body', '')[:300]}"
                for r in results
            ]
            return "\n\n".join(snippets)
    except Exception as e:
        return f"Search failed: {str(e)}"

@function_tool
def send_email_tool(subject: str, text_body: str, html_body: str) -> str:
    """
    Send out an email with the given subject and body
    
    Args:
        subject: The subject of the email
        text_body: The body of the email as plain text
        html_body: The HTML body of the email
    """
    if USE_EMAIL:
        send_email(subject, text_body, html_body)
    else:
        push(f"Subject: {subject}\n\n{text_body}")
    return "Email sent successfully"

# --- 3. Sub-Agents Definition ---

# 1. QA Agent
qa_agent = Agent(
    name="QAAgent",
    instructions="""
    You are an expert QA assistant. Generate targeted, clear clarifying questions 
    to resolve ambiguities in any user research topic.
    """,
    model=model_qwen,
    output_type=QuestionAnswerPlan
)

# 2. Planner Agent
planner_agent = Agent(
    name="PlannerAgent",
    instructions=f"""
    You are an expert research planner assistant.
    Analyze the user's research topic alongside the clarifying Q&A pairs to synthesize a search plan.
    Formulate exactly {HOW_MANY_SEARCHES} distinct, targeted search queries covering different angles.
    Do not include introductory filler or notes.
    """,
    model=model_qwen,
    output_type=PlannerOutput
)

# 3. Search Agent
search_agent = Agent(
    name="SearchAgent",
    instructions="""
    You are a research assistant. Given a search term, use your web_search tool to retrieve 
    information and produce a concise summary (2-3 paragraphs, <300 words). Reply only with the summary.
    """,
    model=model_openai_small,
    tools=[web_search]
)

# 4. Writer Agent
writer_agent = Agent(
    name="WriterAgent",
    instructions="""
    You are a senior researcher tasked with writing a cohesive report for a research query.
    You will be provided with the original query, and some research.
    Generate a comprehensive report based on the research and the query.
    The final output should be in markdown format, and it should be lengthy and detailed. Aim 
    for 3-5 pages of content, at least 700 words.
    Return only the Markdown report, without JSON or code fences.
    """,
    model=model_qwen,
)

# 5. Email Agent
email_agent = Agent(
    name="EmailAgent",
    instructions="""
    You are provided with a detailed report. Use your tool to send an email, converting the report into
    a clean, well presented HTML email with an appropriate subject line.
    """,
    model=model_openai_small,
    tools=[send_email_tool]
)

# --- 4. Main Research Manager Agent ---

research_manager_agent = Agent(
    name="ResearchManagerAgent",
    model_settings=ModelSettings(
        max_tokens=5000
    ),    
    instructions="""
    You are the primary Research Manager. You orchestrate an end-to-end deep research pipeline using your sub-agent tools:
    1. Evaluate the topic and user clarifications provided.
    2. Generate search queries using `planner_tool`.
    3. For each search query, retrieve findings using `search_tool`.
    4. Compile the findings into a markdown report using `writer_tool`.
    5. Dispatch the report via email using `email_tool` if an email is provided.
    6. Return the final markdown report directly as your final response.
    """,
    model=model_openai,
    tools=[
        qa_agent.as_tool(tool_name="clarification_tool", tool_description="Generates clarifying questions."),
        planner_agent.as_tool(tool_name="planner_tool", tool_description="Plans targeted search queries based on Q&A context."),
        search_agent.as_tool(tool_name="search_tool", tool_description="Performs web search and summarizes findings."),
        writer_agent.as_tool(tool_name="writer_tool", tool_description="Synthesizes search summaries into a deep report."),
        email_agent.as_tool(tool_name="email_tool", tool_description="Dispatches report via formatted HTML email."),
    ]
)