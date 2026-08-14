# mem0_oss — Shared AI501 Memory for Hermie

This Hermes memory-provider plugin connects to the self-hosted Mem0 REST API and
shares reusable troubleshooting knowledge across AI501 enablements.

## Configuration

```bash
MEM0_URL=http://mem0-server.hermie-helpers.svc.cluster.local:8000
MEM0_AGENT_ID=genaiops-hermie
MEM0_CUSTOM_INSTRUCTIONS=
```

Activate it in Hermes `config.yaml`:

```yaml
memory:
  memory_enabled: true
  memory_char_limit: 2200
  provider: mem0_oss
```

The Helm deployment copies this repository's `hermes-plugins` directory into the
Hermes data volume during initialization.

## Behavior

- Searches one shared AI501 knowledge scope before each answer.
- Extracts reusable troubleshooting knowledge asynchronously after each turn.
- Stores optional enablement location and course context from the UI envelope.
- Does not create attendee, username, personal, or team memory partitions.
- Skips near-duplicate memories at a similarity score of `0.92` or higher.
- Fails open when Mem0 is temporarily unavailable.

See [SPEC.md](SPEC.md) for the storage and provenance contract.

