from agents import Agent, OpenAIChatCompletionsModel, WebSearchTool, ModelSettings
from dotenv import load_dotenv
from openai import AsyncOpenAI
from ddgs import DDGS
from agents import function_tool
import os

google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


load_dotenv(override=True)
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)

gemini_model = OpenAIChatCompletionsModel(model="gemini-3.1-flash-lite", openai_client=gemini_client)

MODEL_NAME_GEMINI = gemini_model

INSTRUCTIONS = """
You are a research assistant. Given a search term, you search the web for that term and 
produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 words.
Capture the main points and be succinct. Reply only with the summary.
"""

@function_tool
def search_web_duckduckgo(query: str, max_results: int = 3) -> str:
    """Searches the web using DuckDuckGo.

    Args:
        query: Search keywords.
        max_results: Max results to return.
    """
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        
        formatted = []
        for item in results:
            title = item.get("title", "No Title")
            url = item.get("href", "")
            snippet = item.get("body", "")
            formatted.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}\n---")
        return "\n".join(formatted)
    except Exception as exc:
        return f"Error connecting to DuckDuckGo: {exc}"

settings = ModelSettings(tool_choice="required")
tools = [search_web_duckduckgo]

search_agent = Agent(name="Search Agent", instructions=INSTRUCTIONS, tools=tools, 
                     model=MODEL_NAME_GEMINI, model_settings=settings)