# Module 9 — On-Prem Practicum

Primary sources: `docs/9-on-prem-practicum/`. Related repositories: `backend`,
`genaiops-helmcharts`, and GitOps configuration.

Use this module for model selection, model-card interpretation, infrastructure
requirements, model serving, endpoint access, and switching Canopy to an on-prem
model.

Troubleshooting focus:

- Check model compatibility, accelerator/resource availability, scheduling,
  runtime startup, readiness, route/service access, and API behavior in order.
- Distinguish `Pending`, startup failure, failed readiness, and inference errors.
- Read the exercise before naming the serving runtime, model, storage, or resource
  values.
- When Canopy fails after a model switch, test the model endpoint independently
  before changing Canopy.

