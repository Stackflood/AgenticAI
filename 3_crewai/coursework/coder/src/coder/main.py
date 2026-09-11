#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from graphviz.backend import Render

from coder.crew import Coder

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

assignment = 'Write a python program to calculate the first 1,000,000 terms \
    of this series, multiplying the total by 4: 1 - 1/3 + 1/5 - 1/7 + ...'

assignment2 = 'Write a python program to create a database with Teacher and Student as ' \
'tables with one Teacher teaching multiple students ' \
'and one student being taught by multiple students. Fill the database with atleast a 100 records' \
'for both students and teacher.Give real Indian names to both students and teacheres. Have students and teachers from multiple classes. Finally show ' \
'these on the prompt by means of a clean diagram. Create ' \
'as many desired tables as possible to complete this assignemnet. Code should be clean ' \
'without any clutter.Delete data from previous database to fill new entries. Use already written code if available.'

assignment3 = 'Build a clean, dependency-free Tic-Tac-Toe ' \
'(3x3) game in Python and simulate a full game between two automated dummy players.' \
'Dummy Player Behavior: Implement two automated players (Player X and Player O). '\
'Each turn, the active dummy player randomly selects an available cell from the remaining empty spots.'\

'Execution & Output:vPrint the empty board at the start.'\

'Render the updated board to stdout after every move, clearly labeling whose turn it was and what position they chose.'

def run():
    """
    Run the crew.
    """
    inputs = {
            'assignment': assignment3
        }

    try:
        Coder().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        Coder().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Coder().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        Coder().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = Coder().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
