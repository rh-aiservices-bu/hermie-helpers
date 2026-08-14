# Module 12 — The Tuning Room

Primary sources: `docs/12-fine-tuning/`. Related repositories: `experiments`,
`evals`, `backend`, and model-serving/GitOps configuration.

Use this module for the Socratic Tutor use case, dataset preparation, fine-tuning,
evaluation, Model Registry, deployment, MaaS registration, Llama Stack, and Canopy.

Troubleshooting focus:

- Separate data preparation, training job, artifact/registry, serving, MaaS,
  Llama Stack, and Canopy failures.
- For failed training, request the job status and the smallest relevant log section.
- For poor behavior, verify dataset and evaluation results before altering serving.
- Test each boundary—registered model, endpoint, MaaS, Llama Stack, Canopy—in order.

