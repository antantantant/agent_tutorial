import os
from openrouter import OpenRouter

# Initialize the client with your API Key
api_key = os.getenv("OPENROUTER_API_KEY")

try:
    with open("AGENT.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()
except FileNotFoundError:
    system_prompt = (
        "Your goal is to complete the user's task.\n\n"
        "You must choose one of the following formats for every response:\n"
        "1. If a command needs to be executed, output `COMMAND: XXX`, where `XXX` is the command itself. Do not add any explanation or formatting.\n"
        "2. If no command is necessary, output `DONE: XXX`, where `XXX` is your final summary.\n\n"
        "Rules:\n"
        "- If the user asks for current or external information such as latest news, current prices, weather, recent events, or content from a website, do not answer from memory.\n"
        "- For those requests, first output a `COMMAND:` that fetches the needed information.\n"
        "- For recent news, prefer `curl` with a browser user agent against a news RSS feed. Google News RSS is acceptable.\n"
        "- Example news command:\n"
        "  `curl -L -A \"Mozilla/5.0\" \"https://news.google.com/rss/search?q=ASU&hl=en-US&gl=US&ceid=US:en\"`\n"
        "- After command output is returned to you, read it and then respond with `DONE:`.\n"
        "- Only use `DONE:` immediately when the task can be completed without running any command."
    )

with OpenRouter(api_key=api_key) as client:
    messages = [
        {
            "role": "system", 
            "content": system_prompt
        }
    ]

    while True:
        user_input = input("\n[T] ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        messages.append({"role": "user", "content": user_input})
        print("\n--- Agent Loop Started ---")

        while True:
            response = client.chat.send(
                model="openai/gpt-5.4",
                messages=messages
            )
            
            reply = response.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": reply})
            print(f"[AI] {reply}")

            # Check if the AI has finished the task
            if reply.startswith("DONE:"):
                summary = reply.split("DONE:")[1].strip()
                print(f"\n[AI] Final Summary: {summary}")
                print("--- Agent Loop Ended ---")
                break
            
            # Check if the AI wants to execute a command
            elif reply.startswith("COMMAND:"):
                command = reply.split("COMMAND:")[1].strip()
                
                # Execute the command and capture output
                try:
                    # Using os.popen for basic output capture
                    command_result = os.popen(command).read()
                except Exception as e:
                    command_result = f"Error executing command: {str(e)}"
                
                content = f"Execution finished. Result: {command_result}"
                print(f"[Agent] {content}")
                messages.append({"role": "user", "content": content})
            else:
                # Fallback for unexpected formats to prevent infinite loops
                print("[System] Format error or unexpected response. Terminating loop.")
                break
