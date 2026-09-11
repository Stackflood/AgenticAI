import time
import re

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from .tools.sandbox_tools import sandbox_tools


@CrewBase
class EngineeringTeam:
    """EngineeringTeam crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # ---------------------------------------------------------
    # AGENTS
    # ---------------------------------------------------------

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config["engineering_lead"],
            verbose=False,
            max_iter=2,
            max_retry_limit=2,
            mcps=["https://mcp.context7.com/mcp"],
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_engineer"],
            verbose=False,
            max_iter=2,
            max_retry_limit=2,
            tools=sandbox_tools,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["frontend_engineer"],
            verbose=False,
            max_iter=2,
            max_retry_limit=2,
            tools=sandbox_tools,
            mcps=["https://mcp.context7.com/mcp"],
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["test_engineer"],
            verbose=False,
            max_iter=2,
            max_retry_limit=2,
            tools=sandbox_tools,
        )

    # ---------------------------------------------------------
    # TASKS
    # ---------------------------------------------------------

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config["design_task"],
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config["code_task"],
        )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config["frontend_task"],
        )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config["test_task"],
        )

    # ---------------------------------------------------------
    # CREW
    # ---------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        """Creates the EngineeringTeam crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
            tracing=True,

            # Limit number of requests per minute.
            # NOTE:
            # This controls REQUESTS per minute, not INPUT TOKENS
            # per minute.
            max_rpm=10,
        )

    # ---------------------------------------------------------
    # KICKOFF WITH GROQ RATE-LIMIT RETRY
    # ---------------------------------------------------------

    def kickoff_with_retry(self, inputs=None):
        """
        Runs the crew and automatically retries when Groq
        returns a rate-limit error.

        Groq may return an error such as:

        Please try again in 3.651428571s

        The method extracts that value and waits before
        trying again.
        """

        max_rate_limit_retries = 5

        crew_instance = self.crew()

        for attempt in range(max_rate_limit_retries):

            try:
                print(
                    f"Starting crew "
                    f"(attempt {attempt + 1}/"
                    f"{max_rate_limit_retries})..."
                )

                result = crew_instance.kickoff()

                print("Crew completed successfully.")

                return result

            except Exception as e:

                error_text = str(e)

                # -------------------------------------------------
                # Check whether this is a Groq rate-limit error
                # -------------------------------------------------

                if "rate_limit_exceeded" not in error_text:
                    raise

                # -------------------------------------------------
                # Try to extract Groq's recommended wait time.
                #
                # Example:
                # "Please try again in 3.651428571s"
                # -------------------------------------------------

                match = re.search(
                    r"try again in ([\d.]+)s",
                    error_text,
                    re.IGNORECASE,
                )

                if match:
                    wait_time = float(match.group(1)) + 1
                else:
                    # Fallback if Groq doesn't provide
                    # the retry time.
                    wait_time = 5

                print(
                    "\nGroq rate limit reached."
                )

                print(
                    f"Waiting {wait_time:.1f} seconds "
                    f"before retry..."
                )

                print(
                    f"Rate-limit retry "
                    f"{attempt + 1}/{max_rate_limit_retries}"
                )

                time.sleep(wait_time)

        # ---------------------------------------------------------
        # All retries exhausted
        # ---------------------------------------------------------

        raise RuntimeError(
            "Groq rate limit persisted after "
            f"{max_rate_limit_retries} retries."
        )
