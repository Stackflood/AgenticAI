from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
groq_api_key = os.getenv('GROQ_API_KEY')

groq_client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=groq_api_key)

oss_model = OpenAIChatCompletionsModel(model="openai/gpt-oss-120b", 
                                       openai_client=groq_client)

HOW_MANY_SEARCHES = int(os.getenv("HOW_MANY_SEARCHES", 3))


INSTRUCTIONS = f"""
You are an expert research planner assistant. 

Your task is to analyze the user's main research topic alongside the clarifying Q&A pairs provided, then synthesize a targeted web search plan.

Guidelines:
1. Carefully evaluate the clarifications to disambiguate the initial research topic.
2. Formulate exactly {HOW_MANY_SEARCHES} distinct, highly targeted web search queries that cover different angles (e.g., core concepts, recent developments, specific constraints mentioned in the Q&A).
3. For each search item, provide a clear, concise justification explaining why that search is necessary.
4. Keep search terms specific, avoiding punctuation or search engine stop words where possible.
5. Do not include introductory filler, notes, or concluding conversational text.

Expected Output Schema:
{{
  "searches": [
    {{
      "reason": "<Specific reason explaining why this search helps answer the user's intent>",
      "query": "<Targeted web search query>"
    }}
  ]
}}
"""

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    
planner_agent = Agent(name="Planner Agent", instructions=INSTRUCTIONS, model=oss_model, output_type=WebSearchPlan)