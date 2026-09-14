"""
TranscriptRecorder — capture EVERYTHING that goes to / comes back from the model
during a Strands agent run, and render it as a self-contained HTML page.

Why this is educational: an agent is "an LLM that runs tools in a loop." This
recorder makes that loop visible turn by turn — you see the message list GROW as
tool results are appended, exactly what the model receives on each call, and what
it emits back (text, tool calls, stop_reason).

Usage:
    from transcript import TranscriptRecorder
    rec = TranscriptRecorder(task="...", model_id="openrouter/free")
    agent = Agent(..., hooks=[rec, ...])
    agent(task)
    rec.to_html("transcript.html")

It hooks four lifecycle events:
    BeforeModelCallEvent  -> snapshot the full messages list being SENT
    AfterModelCallEvent   -> capture the response message + stop_reason
    BeforeToolCallEvent   -> record which tool the model chose + its args
    MessageAddedEvent     -> record every message appended (incl. tool results)
"""

import copy
import html
import json

from strands.hooks import (
    HookProvider,
    HookRegistry,
    BeforeModelCallEvent,
    AfterModelCallEvent,
    BeforeToolCallEvent,
)


class TranscriptRecorder(HookProvider):
    def __init__(self, task: str = "", model_id: str = ""):
        self.task = task
        self.model_id = model_id
        self.system_prompt = None
        self.events = []          # ordered list of recorded steps
        self._call_no = 0

    # ---- registration -----------------------------------------------------
    def register_hooks(self, registry: HookRegistry, **_):
        registry.add_callback(BeforeModelCallEvent, self._before_model)
        registry.add_callback(AfterModelCallEvent, self._after_model)
        registry.add_callback(BeforeToolCallEvent, self._before_tool)

    # ---- capture ----------------------------------------------------------
    def _before_model(self, event: BeforeModelCallEvent):
        self._call_no += 1
        if self.system_prompt is None:
            self.system_prompt = getattr(event.agent, "system_prompt", None)
        # Snapshot the EXACT message list being sent to the model this turn.
        messages = copy.deepcopy(list(getattr(event.agent, "messages", [])))
        self.events.append({
            "kind": "request",
            "call_no": self._call_no,
            "messages": messages,
            "projected_input_tokens": getattr(event, "projected_input_tokens", None),
        })

    def _after_model(self, event: AfterModelCallEvent):
        resp = getattr(event, "stop_response", None)
        if resp is not None:
            self.events.append({
                "kind": "response",
                "call_no": self._call_no,
                "message": copy.deepcopy(resp.message),
                "stop_reason": resp.stop_reason,
            })
        elif getattr(event, "exception", None) is not None:
            self.events.append({
                "kind": "error",
                "call_no": self._call_no,
                "error": str(event.exception),
            })

    def _before_tool(self, event: BeforeToolCallEvent):
        tu = event.tool_use or {}
        self.events.append({
            "kind": "tool",
            "call_no": self._call_no,
            "name": tu.get("name", "?"),
            "input": tu.get("input", {}),
        })

    # ---- rendering --------------------------------------------------------
    def to_html(self, path: str):
        html_str = self._render()
        with open(path, "w") as f:
            f.write(html_str)
        return path

    # -- helpers for rendering message content blocks --
    @staticmethod
    def _esc(s):
        return html.escape(str(s))

    # -- content blocks: return (label, body_text) tuples --
    @classmethod
    def _block_parts(cls, block: dict):
        """Return (kind, body_string) for one content block."""
        if "text" in block:
            return ("text", block["text"])

        if "toolUse" in block:
            tu = block["toolUse"]
            body = "name: {}\ninput: {}".format(
                tu.get("name", "?"),
                json.dumps(tu.get("input", {}), indent=2, default=str),
            )
            return ("tool_use", body)

        if "toolResult" in block:
            tr = block["toolResult"]
            inner = tr.get("content", [])
            texts = []
            for c in inner:
                if isinstance(c, dict) and "text" in c:
                    texts.append(c["text"])
                else:
                    texts.append(json.dumps(c, default=str))
            body = "\n".join(texts)
            if len(body) > 6000:
                body = body[:6000] + f"\n… [truncated, {len(body)} chars total]"
            status = tr.get("status", "")
            head = f"status: {status}\n" if status else ""
            return ("tool_result", head + body)

        if "reasoningContent" in block:
            rc = block["reasoningContent"]
            txt = ""
            if isinstance(rc, dict):
                txt = (rc.get("reasoningText", {}) or {}).get("text", "") or json.dumps(rc, default=str)
            return ("reasoning", txt)

        return ("raw", json.dumps(block, indent=2, default=str))

    @classmethod
    def _render_message(cls, msg: dict, idx: int, open_default: bool) -> str:
        """One collapsible <details> per message."""
        role = msg.get("role", "?")
        content = msg.get("content", [])
        if isinstance(content, str):
            content = [{"text": content}]
        if not isinstance(content, list):
            content = [{"text": json.dumps(content, default=str)}]

        # Build a short summary of what's inside (block kinds).
        kinds = []
        body_html = []
        for b in content:
            kind, body = cls._block_parts(b)
            kinds.append(kind)
            label = kind.replace("_", " ")
            body_html.append(
                f'<div class="blk"><span class="blabel b-{kind}">{label}</span>'
                f'<pre>{cls._esc(body)}</pre></div>'
            )
        # de-dup summary preserving order
        seen = []
        for k in kinds:
            if k not in seen:
                seen.append(k)
        summary_kinds = ", ".join(seen) if seen else "empty"

        openattr = " open" if open_default else ""
        return (
            f'<details class="msg r-{cls._esc(role)}"{openattr}>'
            f'<summary><span class="rolebadge">{cls._esc(role)}</span>'
            f'<span class="msummary">{cls._esc(summary_kinds)}</span></summary>'
            f'<div class="mbody">{"".join(body_html)}</div>'
            '</details>'
        )

    def _render(self) -> str:
        parts = []
        by_call = {}
        for e in self.events:
            by_call.setdefault(e["call_no"], []).append(e)

        total_calls = self._call_no
        tool_calls = sum(1 for e in self.events if e["kind"] == "tool")

        for call_no in sorted(by_call):
            group = by_call[call_no]
            req = next((e for e in group if e["kind"] == "request"), None)
            resp = next((e for e in group if e["kind"] == "response"), None)
            err = next((e for e in group if e["kind"] == "error"), None)

            parts.append('<section class="call">')
            parts.append(f'<div class="callno">MODEL CALL #{call_no}</div>')

            # REQUEST — the full message list sent this turn.
            if req:
                msgs = req["messages"]
                tok = req.get("projected_input_tokens")
                tok_str = f' &middot; ~{tok} tokens' if tok else ""
                parts.append(
                    f'<div class="dir">&rarr; REQUEST &middot; {len(msgs)} messages{tok_str}</div>'
                )
                last = len(msgs) - 1
                for i, m in enumerate(msgs):
                    # Only auto-expand the newest message; collapse the rest.
                    parts.append(self._render_message(m, i, open_default=(i == last)))

            # RESPONSE — what the model returned.
            if resp:
                parts.append(
                    f'<div class="dir">&larr; RESPONSE &middot; stop_reason = '
                    f'<span class="stopr">{self._esc(resp["stop_reason"])}</span></div>'
                )
                parts.append(self._render_message(resp["message"], 0, open_default=True))
            elif err:
                parts.append(f'<div class="dir err">&times; ERROR: {self._esc(err["error"])}</div>')

            parts.append('</section>')

        calls_html = "\n".join(parts)
        sys_html = ""
        if self.system_prompt:
            sys_html = (
                '<details class="msg r-system" open>'
                '<summary><span class="rolebadge">system prompt</span></summary>'
                f'<div class="mbody"><div class="blk"><pre>{self._esc(self.system_prompt)}</pre></div></div>'
                '</details>'
            )

        return _HTML_TEMPLATE.format(
            task=self._esc(self.task),
            model=self._esc(self.model_id),
            total_calls=total_calls,
            tool_calls=tool_calls,
            system=sys_html,
            calls=calls_html,
        )


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Model transcript</title>
<style>
  :root{{
    --bg:#ffffff; --fg:#1b1b1b; --muted:#767676; --line:#e0e0e0;
    --code-bg:#f6f6f6; --accent:#444;
    --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  }}
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{background:var(--bg);color:var(--fg);font-family:var(--sans);line-height:1.5;
        max-width:920px;margin:0 auto;padding:32px 20px 100px;font-size:14px;}}
  h1{{font-size:18px;font-weight:600;}}
  header{{border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:8px;}}
  .meta{{font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:6px;}}
  .meta b{{color:var(--fg);font-weight:600;}}
  .task{{font-size:13px;color:var(--fg);margin-top:8px;}}
  .controls{{margin:14px 0 6px;font-family:var(--mono);font-size:12px;}}
  .controls button{{font-family:var(--mono);font-size:12px;border:1px solid var(--line);
        background:#fafafa;padding:4px 10px;border-radius:4px;cursor:pointer;margin-right:6px;}}
  .controls button:hover{{background:#f0f0f0;}}

  .call{{margin:22px 0;padding-top:14px;border-top:1px solid var(--line);}}
  .callno{{font-family:var(--mono);font-size:12px;font-weight:600;letter-spacing:.05em;color:var(--fg);margin-bottom:8px;}}
  .dir{{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin:12px 0 6px;letter-spacing:.03em;}}
  .dir.err{{color:#b00020;}}
  .stopr{{color:var(--fg);}}

  /* one collapsible message */
  .msg{{border:1px solid var(--line);border-radius:5px;margin:5px 0;background:#fff;}}
  .msg > summary{{list-style:none;cursor:pointer;padding:7px 10px;display:flex;align-items:center;gap:10px;
        font-family:var(--mono);font-size:12px;}}
  .msg > summary::-webkit-details-marker{{display:none;}}
  .msg > summary::before{{content:"▸";color:var(--muted);font-size:10px;}}
  .msg[open] > summary::before{{content:"▾";}}
  .rolebadge{{font-weight:600;text-transform:uppercase;letter-spacing:.06em;font-size:11px;
        border:1px solid var(--line);border-radius:3px;padding:1px 7px;background:#f3f3f3;}}
  .msummary{{color:var(--muted);}}
  /* subtle left border per role — neutral grays, one gentle accent */
  .r-system{{border-left:3px solid #b8b8b8;}}
  .r-user{{border-left:3px solid #8a8a8a;}}
  .r-assistant{{border-left:3px solid #5b5b5b;}}

  .mbody{{padding:2px 10px 10px;border-top:1px solid var(--line);}}
  .blk{{margin:8px 0;}}
  .blabel{{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;
        color:var(--muted);border:1px solid var(--line);border-radius:3px;padding:1px 6px;display:inline-block;margin-bottom:4px;}}
  .blk pre{{white-space:pre-wrap;word-break:break-word;font-family:var(--mono);font-size:12px;
        background:var(--code-bg);border:1px solid var(--line);border-radius:4px;padding:9px 11px;overflow-x:auto;}}
</style></head>
<body>
<header>
  <h1>Model transcript</h1>
  <div class="meta"><b>{model}</b> &middot; {total_calls} model calls &middot; {tool_calls} tool calls</div>
  <div class="task">{task}</div>
</header>
<div class="controls">
  <button onclick="document.querySelectorAll('details.msg').forEach(d=>d.open=true)">expand all</button>
  <button onclick="document.querySelectorAll('details.msg').forEach(d=>d.open=false)">collapse all</button>
</div>
{system}
{calls}
</body></html>"""
