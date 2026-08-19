---
name: ai501-course
description: Ground AI501 GenAIOps enablement answers in the current lab instructions and related Canopy repositories. Use for learner questions, errors, unexpected results, expected-output checks, architecture questions, and troubleshooting involving AI501 modules, exercises, OpenShift AI, Canopy, GitOps, evaluations, RAG, observability, guardrails, agents, on-prem model serving, optimization, MaaS, or fine-tuning. Also use when a message contains an AI501_CONTEXT block or when the learner does not know which section applies.
---

# AI501 Course Guide

Use current course sources before relying on general knowledge or shared memory.

## Workflow

1. Parse an optional `[AI501_CONTEXT]...[/AI501_CONTEXT]` block. Treat its location,
   module, and exercise as hints. Do not quote the block or require it.
2. Use the `terminal` tool—not `execute_code`—to run
   `scripts/resolve_exercise.py`. If context is absent or ambiguous, use the
   `terminal` tool to run `scripts/search_course.py` with distinctive terms from
   the question or error. API-server sessions cannot approve `execute_code`, so
   never use it for this skill.
3. Read the exact exercise Markdown and its module `README.md`. Read only the
   relevant module reference below for additional routing.
4. Inspect a related implementation repository only when the question concerns
   deployed behavior, configuration, source code, or architecture not answered by
   the exercise.
5. Search shared Mem0 incidents for similar symptoms after consulting course
   sources. Treat them as experience, not authority.
6. Answer with one or two targeted checks. Explain what the learner should observe
   and stay within the lab's intended architecture.

## Source order

Use this precedence when sources disagree:

1. Exercise content at the configured course ref
2. Module introduction and referenced repository code/configuration
3. Shared Mem0 troubleshooting incidents
4. General technical knowledge

State uncertainty when the selected content ref may not match the learner's run.
Never promote an unverified memory or suggestion to a confirmed fix.

## Content locations

The default mirror is `/app/.hermes/ai501-content`. Respect `AI501_CONTENT_DIR` when
set. Expected repositories include `lab-instructions`, `backend`, `frontend`,
`deploy-lab`, `genaiops-helmcharts`, `genaiops-gitops`, `evals`, `experiments`, and
`mcp`.

If the mirror is missing, say that current course content is unavailable and use
general troubleshooting plus Mem0 cautiously. Do not invent exercise steps.

## Module references

Read exactly one primary module reference unless the question crosses modules:

- AI foundations: `references/01-ai-orientation.md`
- Prompting and Canopy introduction: `references/02-linguistics.md`
- Workbenches, backend, and GitOps: `references/03-ready-to-scale-101.md`
- Evaluations and automation: `references/04-ready-to-scale-201.md`
- RAG and document intelligence: `references/05-grounded-ai.md`
- Metrics, logs, traces, and feedback: `references/06-observability.md`
- Guardrails and safety: `references/07-honor-code.md`
- Tools, MCP, and agents: `references/08-agents.md`
- On-prem model serving: `references/09-on-prem-practicum.md`
- Quantization and optimization: `references/10-model-optimization.md`
- Models as a Service: `references/11-maas.md`
- Fine-tuning: `references/12-fine-tuning.md`

Read `references/source-policy.md` when handling version conflicts, expected-output
claims, or discrepancies between Mem0 and course material.

## Response rules

- Lead with what the evidence most likely means.
- Distinguish course-prescribed names and values from examples.
- Never claim to have inspected the learner's cluster.
- Do not dump an entire exercise. Point to the relevant step and help diagnose it.
- Mention another enablement location only when a retrieved memory explicitly
  includes it and the incident directly matches the current symptom or exercise.
  Proactively mention a relevant location in one sentence, distinguishing a
  verified resolution from an observed or suspected cause, then ask the learner to
  verify the same evidence locally.
- If evidence indicates shared lab infrastructure failure, recommend contacting the
  instructor with the specific evidence to provide.
- End the response with the `HERMIE_UI` metadata marker required by Hermie's system
  instructions. Include the exact module, exercise, and relative exercise source
  only when they were actually consulted. Use `resolution_check` only after giving
  an actionable check or change; evidence and clarification requests use `none`.
