# AI501 Shared Memory Specification

## Purpose

Hermie uses Mem0 as a shared troubleshooting knowledge base for AI501 deliveries.
There are no attendee profiles, teams, or personal memories. A useful observation
from one enablement may help learners at a later enablement.

## Storage scope

Every memory uses one shared Mem0 scope:

| Mem0 field | Value |
|---|---|
| `user_id` | `__ai501_shared__` |
| `agent_id` | `MEM0_AGENT_ID` (default `hermie`) |
| `run_id` | Current ephemeral Hermes session |
| `metadata.scope` | `shared_ai501` |

`run_id` gives Mem0 extraction short-term conversational context. Searches filter
only by the shared `user_id` and `agent_id`, so retrieval crosses sessions and
enablement locations.

## Optional provenance

The attendee UI prefixes the latest user turn with a machine-readable envelope:

```text
[AI501_CONTEXT]{"location_label":"Helsinki, Finland","location_city":"Helsinki","location_country":"Finland","module_id":"6-observability","exercise_id":"4-tracing"}[/AI501_CONTEXT]
```

The plugin removes the envelope before extracting knowledge and copies supported
fields into memory metadata:

- `location_label`
- `location_city`
- `location_country`
- `module_id` and `module_label`
- `exercise_id` and `exercise_label`

All fields are optional. The UI remains usable when a learner skips location and
does not select course context.

## Extraction policy

Memories should capture reusable troubleshooting knowledge: symptom, evidence,
diagnostic check, likely or confirmed cause, and resolution when confirmed.

The extraction prompt must preserve uncertainty. An untested recommendation must
not become a confirmed solution. Attendee identity, preferences, greetings, and
questions without reusable diagnostic knowledge are not stored.

When a location is supplied, it should appear naturally in the extracted memory,
for example:

> During an AI501 run in Helsinki, Canopy traces were absent because the backend
> tracing variables were missing. Adding the variables and redeploying resolved it.

Hermie may mention a location only when it appears explicitly in a retrieved
memory.

## Retrieval

Each query performs one semantic search across the shared AI501 scope. Results are
injected under `Shared AI501 troubleshooting memories`. Near-duplicate writes are
skipped when an existing result has a similarity score of at least `0.92`.

