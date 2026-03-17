from openrouter import OpenRouter import os
with OpenRouter (
) as client:
api_key=os-getenv("OPENROUTER_API_KEY")
while True:
user_input = input("\n/T: ")
response = client.chat.send(
model="anthropic/claude-opus-4.6", messages=|
{"role": "user", "content": user_input}
]
)
print(response.choices[0].message.content)