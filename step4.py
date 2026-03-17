import os
from openrouter import OpenRouter

# Ensure the API key is retrieved correctly
api_key = os.getenv("OPENROUTER_API_KEY")

with OpenRouter(api_key=api_key) as client:
    # Load system instructions from Agent.md
    try:
        with open("Agent.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        system_prompt = "You are a helpful agent. Use 'COMMAND: [cmd]' to execute or 'DONE: [summary]' to finish."

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