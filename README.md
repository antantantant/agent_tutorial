# agent_tutorial
Minimum code for an agent tutorial. This project is developed based on [cenzwong/claw-from-scratch](https://github.com/cenzwong/claw-from-scratch) and the tutorial materials below.

# Steps
- `step0.py`: Sends a single "Hello!" request to OpenRouter and prints the model response.
- `step1.py`: Adds a simple terminal chat loop, but each user message is still handled without conversation memory.
- `step2.py`: Keeps a running message history so the terminal chat becomes stateful across turns.
- `step3.py`: Introduces a basic agent loop where the model can reply with `COMMAND:` or `DONE:` and shell commands are executed automatically.
- `step4.py`: Cleans up the agent loop structure and keeps the command-execution pattern more explicit and reliable.
- `step5.py`: Adds `AGENT.md` and `SKILL.md`, parses agent directives more safely, and formats RSS/news command output into short readable results.
- `step6.py`: Wraps the news agent in a local web app with text input, browser voice input, and a small HTTP server backend.
- `step7.py`: Builds a document-grounded assistant for the `MAE301 Project Guideline v1.1.docx` file by extracting relevant chunks and answering questions in a web UI.
- `step8.py`: Connects the agent to a Google Calendar MCP server so the web app can answer calendar questions with tool calls instead of raw shell commands.

# Reference
- https://www.youtube.com/watch?v=WxDCQhKCS7g
- https://www.youtube.com/watch?v=2rcJdFuNbZQ
- https://learnprompting.org/docs/introduction
