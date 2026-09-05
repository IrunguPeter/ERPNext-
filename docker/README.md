# Docker & image building

This directory contains the pieces used to build the ERPNext container image
and the environment template consumed during deployment.

| File | Purpose |
| --- | --- |
| [`apps.json`](apps.json) | Apps baked into the Frappe image on top of Frappe core (for **public** repos). Add your private apps here using an https URL with a PAT embedded, e.g. `https://{{PAT}}@github.com/you/app.git`. |
| [`Containerfile.kenya_hr`](Containerfile.kenya_hr) | Stage-2 image that layers this repo's custom apps (`apps/kenya_hr`, `apps/kenya_procurement`) onto the built image. |
| [`.env.example`](.env.example) | Template for the compose environment (ERPNEXT_VERSION, DB_PASSWORD, ports, custom image refs). Copy to `docker/.env`. |

`deploy-docker.sh` drives this whole process — see
[scripts/README.md](../scripts/README.md) and
[docs/02-docker-deployment.md](../docs/02-docker-deployment.md).

> **Note:** `apps.json` is intentionally valid strict JSON. The Kenya HR and
> Kenya Procurement apps are sub-directories of this repository, so they cannot
> be referenced by URL here — they are copied into the image by
> `Containerfile.kenya_hr`.