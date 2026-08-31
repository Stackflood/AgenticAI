from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from qa_agent import qa_agent, QuestionAnswerPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import uuid
import asyncio

class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        # When a function containing yield is called,
        # it returns a generator object without executing 
        # the function body immediately. Each time next() 
        # is called on the generator (or during a loop), 
        # the function executes until it hits yield, emits the value, 
        # and pauses its execution state,
        # resuming from that exact spot on the next request.
        # return: Terminates the function, destroys the local execution stack, 
        # and sends a single value back to the caller.

        # yield: Pauses the function, saves all local variables and
        # execution state,
        # emits a value, and waits for the next request to resume.
    async def run(self, query: str, qa_payload: list[tuple[str, str]] = None):
        """Runs the research pipeline using the original query and the clarifying Q&A pairs."""
        trace_id = gen_trace_id()
        
        # Format the collected Q&A pairs into text for your planner agent
        if qa_payload:
            qareport = "\n".join([f"Q: {q}\nA: {a}" for q, a in qa_payload])
        else:
            qareport = ""

        with trace("Research trace", trace_id=trace_id):
            yield "Clarifications received. Planning searches..."
            print(f"Question Answer Plan:\n{qareport}")
            yield f"Starting research. Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            
            # Pass both the clarification context and the original query to your search planner
            search_plan = await self.plan_searches(qareport, query)
            # Continue downstream research pipeline...
            yield f"Searches planned, starting {len(search_plan.searches)} searches..."     
            search_results = await self.perform_searches(search_plan)
            print(f"Search plan results:\n{search_results}")
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report

    async def ask_questions(self, query: str) -> QuestionAnswerPlan:
            """ Ask the user  questions related to the query """
            result = await Runner.run(qa_agent, f"Query: {query}")
            return result.final_output        

    async def plan_searches(self,qa_plan: QuestionAnswerPlan, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        input_message = f"Original query: {query}\nQuestion Answer results: {qa_plan}"
        result = await Runner.run(planner_agent, input_message)
        return result.final_output

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        tasks = [self.search(item) for item in search_plan.searches]
        return await asyncio.gather(*tasks)

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input_message = f"Search term: {item.query}\nReason for searching: {item.reason}"
        result = await Runner.run(search_agent, input_message)
        return result.final_output

    # async def write_report(self, query: str, search_results: list[str]) -> ReportData:
    #     """ Write the report for the query """
    #     input_message = f"Original query: {query}\nSummarized search results: {search_results}"
    #     result = await Runner.run(writer_agent, input_message)
    #     return result.final_output
    
    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        print("Thinking about report...")
        input_message = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(writer_agent, input_message)
        print("Finished writing report")
        return ReportData(
            short_summary=result.final_output[:500],
            markdown_report=result.final_output,
            follow_up_questions=[],
        )
    
    async def send_email(self, report: ReportData) -> None:
        await Runner.run(email_agent, report.markdown_report)