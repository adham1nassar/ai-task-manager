


import json
import os

from ollama import Client, Message

from agents.task_tools import (
    list_tasks,
    create_task,
    update_task,
    delete_task,
)

client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
MODEL = "qwen3:4b-instruct-2507-q4_K_M"


def run_task_agent(message: str) -> str:
    messages: list[dict | Message] = [
        {
            "role": "system",
            "content": (
                "You are an AI task management assistant. "
                "Use the available tools to manage tasks in PostgreSQL. "
                "You can list, create, update, and delete tasks. "
                "When the user requests an action, use the appropriate tool. "
                "Never invent task information. "
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
        tools=[
            list_tasks,
            create_task,
            update_task,
            delete_task,
        ],
    )

    if response.message.tool_calls:
        messages.append(response.message)

        for tool_call in response.message.tool_calls:
            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            if tool_name == "list_tasks":
                print("Executing tool: list_tasks")
                result = list_tasks()

            elif tool_name == "create_task":
                print("Executing tool: create_task")
                print("Arguments:", arguments)

                result = create_task(
                    title=arguments["title"],
                    description=arguments.get("description", ""),
                )

            elif tool_name == "update_task":
                print("Executing tool: update_task")
                print("Arguments:", arguments)

                result = update_task(
                    task_id=arguments["task_id"],
                    title=arguments.get("title"),
                    description=arguments.get("description"),
                    completed=arguments.get("completed"),
                )

            elif tool_name == "delete_task":
                print("Executing tool: delete_task")
                print("Arguments:", arguments)

                result = delete_task(
                    task_id=arguments["task_id"],
                )

            else:
                print("Unknown tool:", tool_name)
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
    answer = run_task_agent(
        "Delete task 5."
    )

    print("\nAI:", answer)
