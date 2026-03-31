import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openrouter import OpenRouter


HOST = "127.0.0.1"
PORT = 8002
MODEL = "openai/gpt-5.4"
AGENT_PATH = "AGENT_STEP8.md"
SKILL_PATH = "SKILL_STEP8.md"
GOOGLE_CREDENTIALS_PATH = "GoogleCalendarCredential.json"
MCP_SERVER_COMMAND = "npx"
MCP_SERVER_ARGS = ["-y", "@cocal/google-calendar-mcp", "start"]
ENABLED_TOOLS = ",".join(
    [
        "list-calendars",
        "list-events",
        "search-events",
        "get-event",
        "get-freebusy",
        "get-current-time",
    ]
)

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Google Calendar MCP Demo</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4efe8;
      --panel: #fffaf3;
      --ink: #1c1c1c;
      --muted: #5d5952;
      --line: #d9cfc0;
      --accent: #0d5c8f;
      --accent-2: #d07b2d;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, #e7dfcb 0, transparent 24%),
        radial-gradient(circle at bottom right, #d9e9f3 0, transparent 28%),
        var(--bg);
      color: var(--ink);
    }
    main {
      max-width: 760px;
      margin: 48px auto;
      padding: 0 20px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 18px 50px rgba(28, 28, 28, 0.08);
    }
    h1 {
      margin: 0 0 8px;
      font-size: clamp(2rem, 5vw, 3.2rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }
    p {
      margin: 0 0 20px;
      color: var(--muted);
      line-height: 1.5;
    }
    textarea {
      width: 100%;
      min-height: 120px;
      resize: vertical;
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-radius: 14px;
      font: inherit;
      color: var(--ink);
      background: #fff;
    }
    .row {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 14px;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      cursor: pointer;
    }
    .primary {
      background: var(--accent);
      color: #fff;
    }
    .secondary {
      background: var(--accent-2);
      color: #fff;
    }
    .ghost {
      background: #ece4d8;
      color: var(--ink);
    }
    #status {
      margin-top: 14px;
      color: var(--muted);
      min-height: 24px;
    }
    pre {
      margin: 16px 0 0;
      padding: 16px;
      border-radius: 14px;
      background: #1f2327;
      color: #f7f4ee;
      white-space: pre-wrap;
      word-break: break-word;
      min-height: 180px;
      overflow-x: auto;
    }
  </style>
</head>
<body>
  <main>
    <section class="panel">
      <h1>Calendar MCP</h1>
      <p>Ask by voice or text. This demo uses a local Google Calendar MCP server and OpenRouter for the model.</p>
      <textarea id="prompt" placeholder="Try: what do I have tomorrow after 2 PM?"></textarea>
      <div class="row">
        <button class="secondary" id="voiceBtn" type="button">Start Voice Input</button>
        <button class="primary" id="sendBtn" type="button">Ask</button>
        <button class="ghost" id="clearBtn" type="button">Clear</button>
      </div>
      <div id="status">Idle.</div>
      <pre id="output"></pre>
    </section>
  </main>
  <script>
    const promptEl = document.getElementById("prompt");
    const outputEl = document.getElementById("output");
    const statusEl = document.getElementById("status");
    const voiceBtn = document.getElementById("voiceBtn");
    const sendBtn = document.getElementById("sendBtn");
    const clearBtn = document.getElementById("clearBtn");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let listening = false;

    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = true;
      recognition.continuous = false;

      recognition.onstart = () => {
        listening = true;
        voiceBtn.textContent = "Listening...";
        statusEl.textContent = "Listening for speech...";
      };

      recognition.onresult = (event) => {
        let transcript = "";
        for (const result of event.results) {
          transcript += result[0].transcript;
        }
        promptEl.value = transcript.trim();
      };

      recognition.onerror = (event) => {
        statusEl.textContent = "Voice error: " + event.error;
      };

      recognition.onend = () => {
        listening = false;
        voiceBtn.textContent = "Start Voice Input";
        statusEl.textContent = promptEl.value.trim() ? "Voice captured." : "Idle.";
      };
    } else {
      voiceBtn.disabled = true;
      statusEl.textContent = "Voice input is not supported in this browser. Use Chrome or Edge.";
    }

    voiceBtn.addEventListener("click", () => {
      if (!recognition) return;
      if (listening) {
        recognition.stop();
        return;
      }
      promptEl.value = "";
      recognition.start();
    });

    clearBtn.addEventListener("click", () => {
      promptEl.value = "";
      outputEl.textContent = "";
      statusEl.textContent = "Idle.";
    });

    sendBtn.addEventListener("click", async () => {
      const message = promptEl.value.trim();
      if (!message) {
        statusEl.textContent = "Enter or speak a question first.";
        return;
      }

      outputEl.textContent = "";
      statusEl.textContent = "Checking calendar...";

      try {
        const response = await fetch("/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message })
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "Request failed.");
        }

        outputEl.textContent = data.output || "";
        statusEl.textContent = "Done.";
      } catch (error) {
        statusEl.textContent = "Error.";
        outputEl.textContent = String(error);
      }
    });
  </script>
</body>
</html>
"""


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def load_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if api_key:
        return api_key

    try:
        with open("openrouter.md", "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""


def build_mcp_server_params() -> StdioServerParameters:
    env = {
        "GOOGLE_OAUTH_CREDENTIALS": os.path.abspath(GOOGLE_CREDENTIALS_PATH),
        "ENABLED_TOOLS": ENABLED_TOOLS,
    }
    return StdioServerParameters(command=MCP_SERVER_COMMAND, args=MCP_SERVER_ARGS, env=env)


def build_openrouter_tools(mcp_tools) -> list[dict]:
    tools = []
    for tool in mcp_tools:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
        )
    return tools


def assistant_content_to_text(content) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            text = getattr(item, "text", None)
            if text:
                parts.append(text.strip())
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]).strip())
        return "\n".join(part for part in parts if part).strip()

    return ""


def serialize_assistant_message(message) -> dict:
    serialized = {"role": "assistant"}
    if message.content is not None:
        serialized["content"] = message.content
    if message.tool_calls:
        serialized["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
            for tool_call in message.tool_calls
        ]
    return serialized


def format_mcp_result(result) -> str:
    parts = []

    for block in result.content:
        if getattr(block, "type", "") == "text":
            parts.append(block.text)
        elif getattr(block, "type", "") == "resource":
            resource = getattr(block, "resource", None)
            uri = getattr(resource, "uri", "resource")
            parts.append(f"[resource] {uri}")
        elif getattr(block, "type", "") == "image":
            parts.append("[image omitted]")
        elif getattr(block, "type", "") == "audio":
            parts.append("[audio omitted]")

    if result.structuredContent:
        parts.append(json.dumps(result.structuredContent, indent=2, default=str))

    text = "\n".join(part for part in parts if part).strip()
    if result.isError:
        return f"Tool error:\n{text}" if text else "Tool error."
    return text or "{}"


async def ask_calendar_async(question: str) -> str:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing and openrouter.md was not found.")

    if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
        raise RuntimeError(f"{GOOGLE_CREDENTIALS_PATH} is missing.")

    instructions = f"{load_text(AGENT_PATH)}\n\n{load_text(SKILL_PATH)}"

    async with stdio_client(build_mcp_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            openrouter_tools = build_openrouter_tools(mcp_tools)

            messages = [
                {"role": "system", "content": instructions},
                {"role": "user", "content": question},
            ]

            with OpenRouter(api_key=api_key) as client:
                for _ in range(8):
                    response = client.chat.send(
                        model=MODEL,
                        messages=messages,
                        tools=openrouter_tools,
                    )

                    assistant_message = response.choices[0].message
                    messages.append(serialize_assistant_message(assistant_message))

                    if assistant_message.tool_calls:
                        for tool_call in assistant_message.tool_calls:
                            arguments = json.loads(tool_call.function.arguments or "{}")
                            result = await session.call_tool(tool_call.function.name, arguments=arguments)
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": format_mcp_result(result),
                                }
                            )
                        continue

                    final_text = assistant_content_to_text(assistant_message.content)
                    if final_text:
                        return final_text

                    if assistant_message.refusal:
                        return assistant_message.refusal

                    return "No final text returned from the calendar demo."

    raise RuntimeError("Calendar demo did not finish within the tool-call limit.")


def ask_calendar(question: str) -> str:
    return anyio.run(ask_calendar_async, question)


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return

        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/ask":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)

        try:
            data = json.loads(raw_body.decode("utf-8"))
            message = str(data.get("message", "")).strip()
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON."})
            return

        if not message:
            self._send_json(400, {"error": "Message is required."})
            return

        try:
            output = ask_calendar(message)
            self._send_json(200, {"output": output})
        except Exception as error:
            self._send_json(500, {"error": str(error)})

    def log_message(self, format: str, *args) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving http://{HOST}:{PORT}")
    server.serve_forever()
