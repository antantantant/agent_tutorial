import os
from openrouter import OpenRouter

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY")
) as client:
    messages = []
    while True:
        user_input = input("\nUser: ")
        messages.append({"role": "user", "content": user_input})
        response = client.chat.send(
            model="anthropic/claude-opus-4.6",
            messages=messages
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(reply)
