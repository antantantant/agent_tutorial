from openrouter import OpenRouter
import os
with OpenRouter (
api_key=os.getenv("OPENROUTER_API_KEY")
) as client:
response = client.chat.send(
model="ifnimax/minimax-m2",
messages=l
{"role": "user", "content": "Hello!"}
]
)
print(response.choices [0].message.content)