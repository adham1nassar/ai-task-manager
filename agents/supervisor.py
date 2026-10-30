
import json
import os

from ollama import Client
from agents.task_agent import run_task_agent
from agents.scheduling_agent import run_scheduling_agent

client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

MODEL = "qwen3:4b-instruct-2507-q4_K_M"


def route_request(message: str) -> str:
    response = client.chat(
        model=MODEL,
        format="json",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a supervisor agent for an AI task manager. "
                    "Your only responsibility is to classify user requests. "
                    "Choose exactly one specialist: "
                    "'task_agent' or 'scheduling_agent'. "
                    "Choose task_agent for listing, creating, "
                    "updating, or deleting tasks. "
                    "Choose scheduling_agent for deadlines, "
                    "reminders, and scheduling requests. "
                    "Return only a JSON object with one key named 'agent'. "
                    "Do not answer the user's request."
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    )

    content = response.message.content or "{}"
    decision = json.loads(content)

    agent = decision.get("agent")

    if agent not in ("task_agent", "scheduling_agent"):
        raise ValueError(f"Unknown agent selected: {agent}")

    return agent


def run_supervisor(message: str) -> str:
    selected_agent = route_request(message)

    print("Supervisor selected:", selected_agent)

    if selected_agent == "task_agent":
        return run_task_agent(message)

    elif selected_agent == "scheduling_agent":
        return run_scheduling_agent(message)

    return "Unable to process this request."


if __name__ == "__main__":
    request = (
        "Schedule task 1 for October 31, 2026, "
        "at 3 PM in Germany."
    )

    answer = run_supervisor(request)

    print("\nUser:", request)
    print("AI:", answer)
    
