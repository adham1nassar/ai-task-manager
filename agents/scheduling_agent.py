
import json
from datetime import datetime

from ollama import Client, Message

from agents.task_tools import schedule_task

client = Client(host="http://localhost:11434")
MODEL = "qwen3:4b-instruct-2507-q4_K_M"


def run_scheduling_agent(message: str) -> str:
    current_time = datetime.now().astimezone().isoformat()

    messages: list[dict | Message] = [
        {
            "role": "system",
            "content": (
                "You are a scheduling specialist for an AI task manager. "
                "Your job is to set deadlines for existing tasks. "
                "Use the schedule_task tool when the user requests scheduling. "
                "The user is in the Europe/Berlin time zone. "
                f"The current local date and time is {current_time}. "
                "Convert relative dates such as 'tomorrow' into "
                "an exact ISO 8601 date and time with a UTC offset. "
                "Never invent task IDs. "
                "If the task ID or scheduling time is missing, "
                "ask the user for clarification. "
                "Keep your responses short and clear."
            ),
        },
        {
            "role": "user",
            "content": message,
        },
    ]

    response = client.chat(
        model=MODEL,
        messages=messages,
        tools=[schedule_task],
    )

    if response.message.tool_calls:
        messages.append(response.message)

        for tool_call in response.message.tool_calls:
            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            if tool_name == "schedule_task":
                print("Executing tool: schedule_task")
                print("Arguments:", arguments)

                result = schedule_task(
                    task_id=arguments["task_id"],
                    due_at=arguments["due_at"],
                )
            else:
                result = {"error": "Tool not supported"}

            messages.append(
                {
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": json.dumps(result, default=str),
                }
            )

        final_response = client.chat(
            model=MODEL,
            messages=messages,
        )

        return final_response.message.content or ""

    return response.message.content or ""


if __name__ == "__main__":
    answer = run_scheduling_agent(
        "Schedule task 1 for October 30, 2026, at 6 PM in Germany."
    )

    print("\nAI:", answer)
