
from ollama import Client

# Connect to Ollama running on Windows
client = Client(host="http://localhost:11434")

# Our locally installed AI model
MODEL = "qwen3:4b-instruct-2507-q4_K_M"


def chat_with_ai(message: str) -> str:
    """
    Send a user message to our local AI model
    and return its response.
    """

    response = client.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful AI task management assistant. "
                    "Keep your answers short and clear."
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    )

    return response.message.content or ""


if __name__ == "__main__":
    answer = chat_with_ai(
        "What is Docker? Explain it in one sentence."
    )

    print("AI response:", answer)
