import os
import subprocess
import xml.etree.ElementTree as ET
from openrouter import OpenRouter


def format_command_output(output: str) -> str:
    text = output.strip()
    if "<rss" not in text and "<feed" not in text:
        return text[:4000]

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return text[:4000]

    items = []

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if title and link:
            items.append(f"- {title} | {link}")
        if len(items) == 5:
            return "\n".join(items)

    for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        link = ""
        for node in entry.findall("{http://www.w3.org/2005/Atom}link"):
            href = node.attrib.get("href", "").strip()
            if href:
                link = href
                break
        if title and link:
            items.append(f"- {title} | {link}")
        if len(items) == 5:
            break

    return "\n".join(items) if items else text[:4000]


def get_directive(reply: str) -> tuple[str | None, str]:
    for line in reply.splitlines():
        line = line.strip()
        if line.startswith("COMMAND:"):
            return "COMMAND", line.split("COMMAND:", 1)[1].strip()
        if line.startswith("DONE:"):
            return "DONE", line.split("DONE:", 1)[1].strip()
    return None, ""


# Initialize the client
api_key = os.getenv("OPENROUTER_API_KEY")

with OpenRouter(api_key=api_key) as client:
    # Safely load system and skill files
    try:
        with open("AGENT.md", "r", encoding="utf-8") as f:
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
            directive, payload = get_directive(reply)
            
            # Print AI response in Green
            print(f"\033[32m[AI] {reply}\033[0m\n")

            if directive == "DONE":
                break
            
            if directive == "COMMAND":
                try:
                    result = subprocess.run(
                        payload,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                    command_result = format_command_output(result.stdout)
                    
                    feedback = f"Execution finished. Output:\n{command_result}"
                    print(f"[Agent] {feedback}")
                    
                    # Feed the result back to the LLM
                    messages.append({"role": "user", "content": feedback})
                except Exception as e:
                    error_feedback = f"Execution failed: {str(e)}"
                    messages.append({"role": "user", "content": error_feedback})
            else:
                break
