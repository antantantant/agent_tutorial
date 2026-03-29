import os
from openrouter import OpenRouter

# Ensure the API key is retrieved correctly
api_key = os.getenv("OPENROUTER_API_KEY")

with OpenRouter(api_key=api_key) as client:
    # Load system instructions from AGENT.md
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

    messages = [{"role": "system", "content": system_prompt}]

    while True:
        user_input = input("\n[User]: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        messages.append({"role": "user", "content": user_input})

        # Internal Agent Reasoning Loop
        while True:
            response = client.chat.send(
                model="openai/gpt-5.4",
                messages=messages
            )
            
            reply = response.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": reply})
            print(f"[AI] {reply}")

            # Exit the loop if the agent indicates completion
            if reply.startswith("DONE:"):
                break
            
            # Execute command if the agent requests it
            if "COMMAND:" in reply:
                try:
                    # Isolating the command string after the trigger
                    command = reply.split("COMMAND:")[1].strip()
                    
                    # Capturing stdout via os.popen
                    with os.popen(command) as pipe:
                        command_result = pipe.read()
                    
                    execution_msg = f"Execution finished. Output:\n{command_result}"
                    print(f"[Agent] {execution_msg}")
                    messages.append({"role": "user", "content": execution_msg})
                except Exception as e:
                    error_msg = f"Execution failed: {str(e)}"
                    messages.append({"role": "user", "content": error_msg})
            else:
                # Break to avoid infinite loops if the model deviates from format
                break
