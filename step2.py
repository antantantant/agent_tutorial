import os
with OpenRouter (
) as client:
api_key=os-getenv("OPENROUTER_API_KEY")
messages = []
while True:
user_input = input("\n/T: ")
messages. append (f"role": "user", "content": user_input})
response = client.chat.send(
model="anthropic/claude-opus-4.6", messages=messages
)
reply = response.choices[0].message.content
messages-append (f"role": "assistant", "content": reply})
print(reply)