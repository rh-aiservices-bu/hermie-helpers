"""Mem0 self-hosted memory provider for Hermes Agent.

Connects directly to a self-hosted Mem0 server via REST.
No SDK, no cloud account required.

All reusable troubleshooting knowledge is stored in one shared AI501 scope.
The attendee UI may prefix a question with an ``AI501_CONTEXT`` envelope;
location and optional course fields from that envelope become memory metadata.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from agent.memory_provider import MemoryProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_TIMEOUT       = 10.0   # read operations (search, get)
_WRITE_TIMEOUT = 90.0   # write operations (add) — LLM extraction can take 30–60 s
_CB_THRESHOLD = 5
_CB_COOLDOWN  = 120.0
_SHARED_USER_ID = "__ai501_shared__"
_DEDUP_THRESHOLD = 0.92
_CONTEXT_RE = re.compile(r"^\[AI501_CONTEXT\](\{.*?\})\[/AI501_CONTEXT\]\s*", re.DOTALL)
_CONTEXT_FIELDS = {
    "location_label",
    "location_city",
    "location_country",
    "module_id",
    "module_label",
    "exercise_id",
    "exercise_label",
}


def _extract_ai501_context(message: str) -> tuple[str, Dict[str, str]]:
    """Remove the UI context envelope and return its safe provenance fields."""
    match = _CONTEXT_RE.match(message or "")
    if not match:
        return message, {}
    try:
        raw = json.loads(match.group(1))
    except (TypeError, ValueError, json.JSONDecodeError):
        return message, {}
    context = {
        key: str(value).strip()[:160]
        for key, value in raw.items()
        if key in _CONTEXT_FIELDS and value is not None and str(value).strip()
    }
    return message[match.end():], context


class Mem0OssProvider(MemoryProvider):

    @property
    def name(self) -> str:
        return "mem0_oss"

    def __init__(self) -> None:
        self._url: str = ""
        self._user_id: str = _SHARED_USER_ID
        self._agent_id: str = "hermie"
        self._run_id: str = ""
        self._client: Optional[httpx.Client] = None
        self._write_client: Optional[httpx.Client] = None
        self._lock = threading.Lock()
        self._prefetch_cache: str = ""
        self._extra_instructions: str = ""
        self._cb_failures: int = 0
        self._cb_tripped_at: float = 0.0

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        return bool(os.getenv("MEM0_URL"))

    def initialize(self, session_id: str, **kwargs) -> None:
        self._url      = os.getenv("MEM0_URL", "").rstrip("/")
        self._user_id = _SHARED_USER_ID
        self._agent_id = os.getenv("MEM0_AGENT_ID") or "hermie"
        self._run_id             = session_id
        self._extra_instructions = os.getenv("MEM0_CUSTOM_INSTRUCTIONS") or ""
        self._client             = httpx.Client(base_url=self._url, timeout=_TIMEOUT)
        self._write_client       = httpx.Client(base_url=self._url, timeout=_WRITE_TIMEOUT)
        logger.info(
            "mem0_oss: connected to %s (shared_scope=%s/%s, run=%s)",
            self._url, self._user_id, self._agent_id, self._run_id,
        )

    def shutdown(self) -> None:
        if self._client:
            self._client.close()
        if self._write_client:
            self._write_client.close()

    # ── Circuit breaker ──────────────────────────────────────────────────────

    def _cb_ok(self) -> bool:
        if self._cb_failures >= _CB_THRESHOLD:
            if time.time() - self._cb_tripped_at < _CB_COOLDOWN:
                return False
            self._cb_failures = 0
        return True

    def _request(self, method: str, path: str, *, _write: bool = False, **kwargs) -> Any:
        if not self._cb_ok():
            raise RuntimeError("mem0 circuit breaker open")
        client = self._write_client if _write else self._client
        try:
            r = client.request(method, path, **kwargs)
            r.raise_for_status()
            self._cb_failures = 0
            return r.json()
        except Exception:
            self._cb_failures += 1
            if self._cb_failures >= _CB_THRESHOLD:
                self._cb_tripped_at = time.time()
                logger.warning("mem0_oss: circuit breaker tripped after %d failures", _CB_THRESHOLD)
            raise

    # ── Memory helpers ───────────────────────────────────────────────────────

    def _search_shared(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search reusable knowledge collected across every AI501 run."""
        data = self._request("POST", "/search", json={
            "query":   query,
            "filters": {"user_id": self._user_id, "agent_id": self._agent_id},
            "top_k":   top_k,
        })
        return data if isinstance(data, list) else data.get("results", [])

    def _extraction_prompt(self, context: Dict[str, str]) -> str:
        """Instructions for extracting reusable, location-aware lab knowledge."""
        provenance = context.get("location_label", "not shared")
        course = context.get("exercise_label") or context.get("module_label") or "not selected"
        prompt = f"""\
AI501 SHARED TROUBLESHOOTING MEMORY (highest priority):
Extract only knowledge that could help another AI501 learner with a similar problem.

Current provenance:
- Enablement location: {provenance}
- Course context: {course}

Good memories describe a concrete symptom, relevant evidence, likely or confirmed cause,
useful diagnostic check, and resolution when one was actually confirmed. Keep uncertainty:
do not turn a suggestion or untested hypothesis into a proven solution. Include the
enablement location naturally when it was shared, for example "During an AI501 run in
Paris, ...". Do not invent a city, country, module, exercise, command output, or result.

Do not extract attendee identity, personal preferences, greetings, generic questions,
or a restatement that contains no reusable diagnostic knowledge. It is correct to return
an empty memory list when the exchange has not produced useful troubleshooting knowledge."""
        if self._extra_instructions:
            prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{self._extra_instructions}"
        return prompt

    def _add(
        self,
        messages: List[Dict],
        infer: bool = True,
        prompt: Optional[str] = None,
        context: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Store memories. Returns True if at least one memory was saved."""
        body: Dict[str, Any] = {
            "messages": messages,
            "user_id":  self._user_id,
            "agent_id": self._agent_id,
            "run_id":   self._run_id,
            "infer":    infer,
            "metadata": {
                "scope":      "shared_ai501",
                "created_at": datetime.now(timezone.utc).isoformat(),
                **(context or {}),
            },
        }
        if infer:
            body["prompt"] = prompt or self._extraction_prompt(context or {})
        try:
            data = self._request("POST", "/memories", json=body, _write=True)
            results = data.get("results", []) if isinstance(data, dict) else (data or [])
            logger.debug("mem0_oss._add: stored %d shared memories, response=%s",
                         len(results), json.dumps(results)[:200])
            return bool(results)
        except Exception as e:
            logger.warning("mem0_oss._add FAILED: %s", e)
            raise

    def _get_all(self) -> List[Dict]:
        data = self._request("GET", "/memories", params={
            "user_id":  self._user_id,
            "agent_id": self._agent_id,
        })
        return data if isinstance(data, list) else data.get("results", [])

    def _delete(self, memory_id: str) -> None:
        self._request("DELETE", f"/memories/{memory_id}")

    def _already_known(self, content: str) -> bool:
        """Skip save if the shared AI501 corpus already has a near duplicate."""
        try:
            hits = self._search_shared(content, top_k=3)
            return any(h.get("score", 0) >= _DEDUP_THRESHOLD for h in hits)
        except Exception:
            return False

    # ── Per-turn hooks ───────────────────────────────────────────────────────

    def system_prompt_block(self) -> str:
        return (
            "You have shared long-term AI501 troubleshooting memory via mem0. "
            "Use `mem0_search` to recall relevant facts before answering, "
            "and `mem0_profile` to review the shared corpus. Memories may include an "
            "enablement location. Mention that location only when it is explicitly present "
            "in the retrieved memory; never invent provenance. Treat tentative diagnoses as tentative."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        logger.info("mem0_oss.prefetch(query=%r, session=%r) — cache=%s",
                    query, session_id, bool(self._prefetch_cache))
        with self._lock:
            result, self._prefetch_cache = self._prefetch_cache, ""
        if result and result.strip():
            logger.info("mem0_oss.prefetch returning cached (%d chars)", len(result))
            return result
        # Turn 1 fallback: cache is empty because nothing was queued before the
        # first message. Run searches inline and return directly so turn 1 gets context.
        try:
            shared = self._search_shared(query, top_k=8)
            logger.info("mem0_oss.prefetch: shared=%d (inline fallback)", len(shared))
            if shared:
                lines = "\n".join(f"- {m.get('memory', m)}" for m in shared)
                result = f"## Shared AI501 troubleshooting memories:\n{lines}"
                logger.info("mem0_oss.prefetch returning %d chars:\n%s", len(result), result)
                return result
        except Exception as exc:
            logger.error("mem0_oss.prefetch fallback FAILED: %s", exc, exc_info=True)
        logger.info("mem0_oss.prefetch returning empty string (no results)")
        return ""

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        logger.debug("mem0_oss.queue_prefetch(query=%r, session=%r)", query, session_id)
        threading.Thread(target=self._bg_prefetch, args=(query,), daemon=True).start()

    def _bg_prefetch(self, query: str) -> None:
        try:
            logger.info("mem0_oss._bg_prefetch(query=%r) starting", query)
            shared = self._search_shared(query, top_k=8)
            logger.info("mem0_oss._bg_prefetch: shared=%d", len(shared))
            if shared:
                lines = "\n".join(f"- {m.get('memory', m)}" for m in shared)
                result = f"## Shared AI501 troubleshooting memories:\n{lines}"
                with self._lock:
                    self._prefetch_cache = result
                logger.info("mem0_oss._bg_prefetch: cached %d chars:\n%s", len(result), result)
            else:
                logger.info("mem0_oss._bg_prefetch: no results for %r", query)
        except Exception as exc:
            logger.error("mem0_oss._bg_prefetch FAILED: %s", exc, exc_info=True)

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if not user_content:
            return
        logger.debug("mem0_oss.sync_turn: scheduling background sync (user=%d chars, asst=%d chars)",
                     len(user_content), len(assistant_content))
        threading.Thread(
            target=self._bg_sync,
            args=(user_content, assistant_content),
            daemon=True,
        ).start()

    def _bg_sync(self, user_msg: str, asst_msg: str) -> None:
        clean_user_msg, context = _extract_ai501_context(user_msg)
        provenance = []
        if context.get("location_label"):
            provenance.append(f"Enablement location: {context['location_label']}")
        if context.get("module_label"):
            provenance.append(f"AI501 module: {context['module_label']}")
        if context.get("exercise_label"):
            provenance.append(f"AI501 exercise: {context['exercise_label']}")
        contextual_user_msg = "\n".join([*provenance, clean_user_msg])
        messages = [
            {"role": "user",      "content": contextual_user_msg},
            {"role": "assistant", "content": asst_msg},
        ]
        try:
            logger.debug("mem0_oss._bg_sync: extracting shared AI501 knowledge")
            dedup_content = f"{clean_user_msg}\n{asst_msg}"
            if not self._already_known(dedup_content):
                self._add(
                    messages,
                    prompt=self._extraction_prompt(context),
                    context=context,
                )
            else:
                logger.debug("mem0_oss: skipping near-duplicate shared memory")
        except Exception as exc:
            logger.warning("mem0_oss shared sync FAILED: %s", exc, exc_info=True)

    # ── Tools ────────────────────────────────────────────────────────────────

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "mem0_search",
                "description": (
                    "Search shared AI501 troubleshooting memory for facts relevant to a query. "
                    "Results may include the enablement location where an issue was encountered."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What to search for",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Max results per tier (default 5)",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "mem0_profile",
                "description": "Retrieve all memories in the shared AI501 knowledge scope.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            # {
            #     "name": "mem0_conclude",
            #     "description": (
            #         "Store a specific fact verbatim (skips LLM extraction). "
            #         "Use scope='team' to share with the whole team."
            #     ),
            #     "parameters": {
            #         "type": "object",
            #         "properties": {
            #             "fact": {
            #                 "type": "string",
            #                 "description": "The fact to store",
            #             },
            #             "scope": {
            #                 "type": "string",
            #                 "enum": ["personal", "team"],
            #                 "description": "personal (default) or team",
            #             },
            #         },
            #         "required": ["fact"],
            #     },
            # },
        ]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        if tool_name == "mem0_search":
            try:
                top_k = args.get("top_k", 5)
                shared = self._search_shared(args["query"], top_k=top_k)
                if not shared:
                    return json.dumps({"result": "No relevant memories found."})
                return json.dumps({
                    "shared_ai501_memories": [m.get("memory", str(m)) for m in shared]
                })
            except RuntimeError:
                return json.dumps({"error": "Memory service temporarily unavailable."})
            except Exception as exc:
                logger.warning("mem0_oss tool error (mem0_search): %s", exc)
                return json.dumps({"error": str(exc)})

        if tool_name == "mem0_profile":
            try:
                memories = self._get_all()
                if not memories:
                    return json.dumps({"result": "No memories stored yet."})
                return json.dumps({
                    "memories": [m.get("memory", str(m)) for m in memories]
                })
            except RuntimeError:
                return json.dumps({"error": "Memory service temporarily unavailable."})
            except Exception as exc:
                logger.warning("mem0_oss tool error (mem0_profile): %s", exc)
                return json.dumps({"error": str(exc)})

        # if tool_name == "mem0_conclude":
        #     try:
        #         scope = args.get("scope", "personal")
        #         stored = self._add(
        #             [{"role": "user", "content": args["fact"]}],
        #             scope=scope,
        #             infer=False,
        #         )
        #         return json.dumps({"result": f"Memory stored ({scope}).", "stored": stored})
        #     except RuntimeError:
        #         return json.dumps({"error": "Memory service temporarily unavailable."})
        #     except Exception as exc:
        #         logger.warning("mem0_oss tool error (mem0_conclude): %s", exc)
        #         return json.dumps({"error": str(exc)})

        # logger.debug("mem0_oss.handle_tool_call: unknown tool %s", tool_name)
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


def register(collector) -> None:
    logger.info("mem0_oss: register() called, registering Mem0OssProvider")
    collector.register_memory_provider(Mem0OssProvider())
