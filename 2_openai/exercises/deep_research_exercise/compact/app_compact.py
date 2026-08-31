import gradio as gr
from dotenv import load_dotenv
from agents import Runner
from research_pipeline import research_manager_agent
from qa_agent import build_ui

load_dotenv(override=True)

async def run_research(query: str, recipient_email: str, qa_payload: list[tuple[str, str]]):
    qa_formatted = "\n".join([f"- **Q:** {q}\n  **A:** {a}" for q, a in qa_payload])
    
    manager_prompt = f"""
    Research Request:
    - Topic: "{query}"
    - Target Recipient: "{recipient_email if recipient_email.strip() else 'N/A'}"
    - User Clarification Inputs:
    {qa_formatted}

    Please execute the research plan, summarize findings, generate the comprehensive report, and send it to the recipient if an email is provided.
    """

    status_log = ["### 🚀 Research Pipeline Initiated\n"]
    yield "\n".join(status_log)

    tool_labels = {
        "planner_tool": "📋 **Planner Agent:** Synthesizing targeted search queries...",
        "search_tool": "🔍 **Search Agent:** Executing web searches and summarizing findings...",
        "writer_tool": "✍️ **Writer Agent:** Drafting the comprehensive research report...",
        "email_tool": "📧 **Email Agent:** Formatting and dispatching report email..."
    }

    try:
        # Run streaming execution
        result_stream = Runner.run_streamed(research_manager_agent, input=manager_prompt)
        
        async for event in result_stream:
            # Check for tool call invocations
            if hasattr(event, "item") and getattr(event.item, "type", None) == "function_call":
                tool_name = event.item.name
                msg = tool_labels.get(tool_name, f"⚙️ Executing tool `{tool_name}`...")
                status_log.append(msg)
                yield "\n\n".join(status_log)

        # Final output report
        final_result = await result_stream.get_final_result()
        yield final_result.final_output

    except Exception as e:
        status_log.append(f"\n❌ **Error during execution:** {str(e)}")
        yield "\n\n".join(status_log)   
        """Constructs dynamic prompt containing topic, email, and Q&A history, then executes research_manager_agent."""
    yield "### 🚀 Research Pipeline Initiated\nSynthesizing clarification inputs and planning queries..."
    
    # Format collected Q&A pairs dynamically
    qa_formatted = "\n".join([f"- **Q:** {q}\n  **A:** {a}" for q, a in qa_payload])
    
    manager_prompt = f"""
    Research Request:
    - Topic: "{query}"
    - Target Recipient: "{recipient_email if recipient_email.strip() else 'N/A'}"
    - User Clarification Inputs:
    {qa_formatted}

    Please execute the research plan, summarize findings, generate the comprehensive report, and send it to the recipient if an email is provided.
    """

    try:
        result = await Runner.run(research_manager_agent, input=manager_prompt)
        yield result.final_output
    except Exception as e:
        yield f"**Error executing research pipeline:** {str(e)}"

ui = build_ui(research_fn=run_research)

if __name__ == "__main__":
    ui.launch(share=True)