# Module 8 — Autonomous Systems 101

Primary sources: `docs/8-agents/`. Related repositories: `mcp`, `backend`, `evals`,
GitOps, and Helm charts.

Use this module for tools, MCP servers, ReAct workflows, Llama Stack, LangGraph,
agent deployment, tool tests, agent evaluation, and MCP authorization.

Troubleshooting focus:

- Separate model reasoning failure from tool discovery, schema, transport,
  authorization, execution, and response-shape failures.
- For MCP, verify server availability and advertised tools before debugging the
  agent prompt.
- For agent evaluation, identify whether the failing layer is a tool unit test,
  trajectory/trace assertion, or end-to-end result.
- Do not claim a tool ran unless the learner supplies evidence that it did.

