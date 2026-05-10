from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import os
load_dotenv()
API_KEY_3 = os.getenv("NVIDIA_API_KEY_3")

if not API_KEY_3:
    raise ValueError("❌ API keys not found in .env file")



# Initialize model once (reuse across app)
client = ChatNVIDIA(
    model="meta/llama-3.1-8b-instruct",
    api_key=API_KEY_3,
    temperature=0.2,
    top_p=0.7,
    max_tokens=1024,
)


def initialize_messages():
    """
    Initialize chat with system prompt
    """
    return [
        {
            "role": "system",
            "content": "You are a helpful, concise AI assistant."
        }
    ]


def get_bot_response(messages):
    """
    Takes message history and returns full bot response (streamed)
    """
    full_response = ""

    for chunk in client.stream(messages):
        if chunk.content:
            full_response += chunk.content

    return full_response


def chat_step(messages, user_input):
    """
    Handles one chat interaction:
    - adds user message
    - gets bot response
    - updates memory
    """

    # Add user message
    messages.append({"role": "user", "content": user_input})

    # Get bot reply
    bot_reply = get_bot_response(messages)

    # Add bot response
    messages.append({"role": "assistant", "content": bot_reply})

    # Limit memory (keep last 10 messages)
    if len(messages) > 10:
        messages = messages[-10:]

    return bot_reply, messages