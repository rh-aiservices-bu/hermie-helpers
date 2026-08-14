# Module 3 — Ready to Scale 101

Primary sources: `docs/3-ready-to-scale-101/`. Related repositories: `backend`,
`frontend`, `genaiops-helmcharts`, and `genaiops-gitops`.

Use this module for workbenches, model API calls, Canopy backend integration,
Gitea, Argo CD, ApplicationSets, and test/prod deployment.

Troubleshooting focus:

- Locate failure at workbench, backend, Git, Argo CD, Helm, or workload level.
- For GitOps, compare repository state, Argo sync/health, rendered values, and pod
  status in that order.
- Preserve the test-to-production flow taught by the lab; avoid manual changes that
  Argo CD will overwrite.

