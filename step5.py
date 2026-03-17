import os
from openrouter import OpenRouter

# Initialize the client
api_key = os.getenv("OPENROUTER_API_KEY")

with OpenRouter(api_key=api_key) as client:
    # Safely load system and skill files
    try:
        with open("Agent.md", "r", encoding="utf-8") as f:
            agent_md = f.read()
        with open("SKILL.md", "r", encoding="utf-8") as f:
            skill_md = f.read()
    except FileNotFoundError as e:
        print(f"Error: Could not find configuration file: {e}")
        exit(1)

    # Initialize message history with combined instructions
    messages = [{"role": "system", "content": f"{agent_md}\n\n{skill_md}"}]

    while True:
        user_input = input("\n[User] ")
        if user_input.lower() in ["exit", "quit"]:
            break

        messages.append({"role": "user", "content": user_input})

        # Agent Reasoning/Execution Loop
        while True:
            response = client.chat.send(
                model="openai/gpt-5.4",
                messages=messages
            )
            
            reply = response.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": reply})
            
            # Print AI response in Green
            print(f"\033[32m[AI] {reply}\033[0m\n")

            # Check if the agent is finished (using 'DONE:' as the trigger)
            if reply.startswith("DONE:"):
                break
            
            # If the agent wants to execute a command (using 'COMMAND:' as the trigger)
            if "COMMAND:" in reply:
                try:
                    # Extract command string after the trigger
                    command = reply.split("COMMAND:")[1].strip()
                    
                    # Execute and capture output
                    with os.popen(command) as pipe:
                        command_result = pipe.read()
                    
                    feedback = f"Execution finished. Output:\n{command_result}"
                    print(f"[Agent] {feedback}")
                    
                    # Feed the result back to the LLM
                    messages.append({"role": "user", "content": feedback})
                except Exception as e:
                    error_feedback = f"Execution failed: {str(e)}"
                    messages.append({"role": "user", "content": error_feedback})
            else:
                # If no command or done signal is found, break to prevent infinite loops
                break