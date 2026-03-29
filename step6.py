import json
import os
import subprocess
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from openrouter import OpenRouter


HOST = "127.0.0.1"
PORT = 8000
MODEL = "openai/gpt-5.4"

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Voice News Agent</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f1e8;
      --panel: #fffaf0;
      --ink: #1f1f1f;
      --muted: #5f5a52;
      --line: #d7cfc1;
      --accent: #0d6b5c;
      --accent-2: #d98c2b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, #efe4c8 0, transparent 28%),
        radial-gradient(circle at bottom right, #e6efe7 0, transparent 30%),
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
      box-shadow: 0 18px 50px rgba(52, 44, 27, 0.08);
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
      background: #ebe4d6;
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
      background: #1e1f1c;
      color: #f5f1e8;
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
      <h1>Voice News Agent</h1>
      <p>Speak or type a request. The agent returns text only.</p>
      <textarea id="prompt" placeholder="Try: grab recent news about Arizona State University"></textarea>
      <div class="row">
        <button class="secondary" id="voiceBtn" type="button">Start Voice Input</button>
        <button class="primary" id="sendBtn" type="button">Send</button>
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
        if (promptEl.value.trim()) {
          statusEl.textContent = "Voice captured.";
        } else {
          statusEl.textContent = "Idle.";
        }
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
        statusEl.textContent = "Enter or speak a request first.";
        return;
      }

      outputEl.textContent = "";
      statusEl.textContent = "Running agent...";

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


def run_agent(user_input: str) -> str:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing and openrouter.md was not found.")

    agent_md = load_text("AGENT.md")
    skill_md = load_text("SKILL.md")
    messages = [{"role": "system", "content": f"{agent_md}\n\n{skill_md}"}]
    messages.append({"role": "user", "content": user_input})

    with OpenRouter(api_key=api_key) as client:
        for _ in range(6):
            response = client.chat.send(model=MODEL, messages=messages)
            reply = response.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": reply})
            directive, payload = get_directive(reply)

            if directive == "DONE":
                return payload

            if directive == "COMMAND":
                result = subprocess.run(
                    payload,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
                output = result.stdout or result.stderr
                command_result = format_command_output(output)
                feedback = f"Execution finished. Output:\n{command_result}"
                messages.append({"role": "user", "content": feedback})
                continue

            raise RuntimeError("Agent reply did not contain COMMAND: or DONE:.")

    raise RuntimeError("Agent did not finish within the execution limit.")


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
            output = run_agent(message)
            self._send_json(200, {"output": output})
        except Exception as error:
            self._send_json(500, {"error": str(error)})

    def log_message(self, format: str, *args) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving http://{HOST}:{PORT}")
    server.serve_forever()
