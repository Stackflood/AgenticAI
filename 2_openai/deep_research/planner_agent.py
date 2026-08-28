from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
groq_api_key = os.getenv('GROQ_API_KEY')

groq_client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=groq_api_key)

oss_model = OpenAIChatCompletionsModel(model="qwen/qwen3.6-27b", 
                                       openai_client=groq_client)

MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")
HOW_MANY_SEARCHES = int(os.getenv("HOW_MANY_SEARCHES", 3))


INSTRUCTIONS = f"""
You are a research assistant. Given a user query, come up with a set of web searches
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for.
"""

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    
planner_agent = Agent(name="Planner Agent", instructions=INSTRUCTIONS, model=oss_model, output_type=WebSearchPlan)