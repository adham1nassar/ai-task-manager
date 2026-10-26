

import json

from ollama import Client, Message

from agents.task_tools import (
    list_tasks,
    create_task,
    update_task,
    delete_task,
)


client = Client(host="http://localhost:11434")

MODEL = "qwen3:4b-instruct-2507-q4_K_M"

pending_deletion: int | None = None



def run_task_agent(message: str) -> str:
    global pending_deletion
    messages: list[dict | Message] = [
        {
            "role": "system",
            "content": (
                "You are an AI task management assistant. "
                "Use the available tools when the user asks "
                "about their stored tasks. "
                "Never invent task information. "
                "Keep your responses short and clear."
            ),
        },
        {
            "role": "user",
            "content": message,
        },
    ]

    # Step 1: Ask the model what to do
    response = client.chat(
        model=MODEL,
        messages=messages,
        tools=[list_tasks, create_task, update_task, delete_task],
    )

    # Step 2: Check whether the model requested a tool
    if response.message.tool_calls:

        # Add the assistant's tool-call message to history
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
                task_id = arguments.get("task_id")

                if type(task_id) is not int or task_id <= 0:
                    result = {
                        "status": "error",
                        "message": "A valid task ID is required.",
                    }

                else:
                    pending_deletion = task_id

                    print("Pending deletion:", pending_deletion)

                    result = {
                        "status": "confirmation_required",
                        "task_id": pending_deletion,
                        "message": (
                            f"Task {pending_deletion} has NOT been deleted. "
                            "Ask the user to confirm the deletion."
                        ),
                    }

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

        # Step 5: Ask the model to explain the results
        final_response = client.chat(
            model=MODEL,
            messages=messages,
        )

        return final_response.message.content or ""

    # No tool was requested
    return response.message.content or ""




if __name__ == "__main__":
    answer = run_task_agent(
        "Delete task 5."
    )

    print("\nAI:", answer)


