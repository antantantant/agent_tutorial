import os
from openrouter import OpenRouter

# Initialize the client with your API Key
api_key = os.getenv("OPENROUTER_API_KEY")

with OpenRouter(api_key=api_key) as client:
    messages = [
        {
            "role": "system", 
            "content": (
                "Your goal is to complete the user's task. You must choose one of the following formats for your response:\n"
                "1. If you believe a command needs to be executed, output 'COMMAND: XXX', where XXX is the command itself. Do not use any formatting or explanation.\n"
                "2. If you believe no command is necessary, output 'DONE: XXX', where XXX is your summary information."
            )
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