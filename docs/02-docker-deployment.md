# Docker Deployment

The recommended deployment path uses the official
[frappe_docker](https://github.com/frappe/frappe_docker) project, which this
repository wraps with `scripts/deploy-docker.sh`.

## How the images are built

**Stage 1 — ERPNext + HRMS.** `deploy-docker.sh` clones `frappe_docker`, then
builds an image from its `images/layered/Containerfile` using
[docker/apps.json](../docker/apps.json):

```json
[
  { "url": "https://github.com/frappe/erpnext", "branch": "version-16" },
  { "url": "https://github.com/frappe/hrms",     "branch": "version-16" }
]
```

**Stage 2 — Kenya HR.** The Kenya HR app lives in a sub-directory of this repo
(`apps/kenya_hr`), so it is layered on top via
[docker/Containerfile.kenya_hr](../docker/Containerfile.kenya_hr):

```bash
docker build -f docker/Containerfile.kenya_hr --build-arg BASE_IMAGE=erpnext-hrms:16 -t kenya-hr-stack:16 .
```

**Compose file.** The final stack is rendered from the upstream `compose.yaml`
plus the official MariaDB, Redis, and no-proxy overrides. The rendered file is
kept at `docker-compose.generated.yml` so you can inspect exactly what runs.

## Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `-s, --site` | `erp.localhost` | Site/domain name |
| `-p, --admin-pass` | `admin` | Administrator password |
| `-d, --db-pass` | `123` | MariaDB root password |
| `-P, --port` | `8080` | Public HTTP port |
| `-e, --env FILE` | `docker/.env` | Environment file for the pipeline |
| `--version TAG` | `v16.34.1` | ERPNext base image tag |
| `--dev` | off | Mount `apps/kenya_hr` instead of baking it |
| `FRAPPE_DOCKER_REF` env | `main` | Pin the frappe_docker commit/tag |

Examples:

```bash
# production-ish: real domain, strong passwords, port 80
./scripts/deploy-docker.sh --site erp.example.com \
    --admin-pass 'X#9k!pL2' --db-pass 'X#9k!pL2' --port 80

# iterate on the Kenya HR app source without rebuilding the image
./scripts/deploy-docker.sh --dev
```

With `--dev`, `apps/kenya_hr` is mounted read-only into the backend container and
installed with `bench get-app` + `bench install-app`. Re-run
`bench --site <site> migrate` after editing source.

## Going to production

1. **Strong passwords** — always pass `--admin-pass` and `--db-pass`.
2. **A real hostname** — create the site with your actual domain and point DNS
   at the server. For DNS-based multi-tenancy keep `FRAPPE_SITE_NAME_HEADER` empty.
3. **Ports** — the no-proxy stack publishes HTTP on `${HTTP_PUBLISH_PORT}`.
   Terminate TLS at the edge (nginx/caddy/traefik) or use the frappe_docker
   HTTPS/traefik overrides (see its docs).
4. **Firewall** — allow only what you need: `22` (SSH), `80`/`443` (or your
   custom port if remote, although reverse-proxying on 80/443 is preferred).
5. **Tuning** — set `GUNICORN_WORKERS`/`GUNICORN_THREADS` in your env file
   (guide: `(2 × CPU cores) + 1` workers).
6. **Backups** — automate [backup.sh](../scripts/backup.sh) with cron and ship
   the archives off-box. See [Backup & restore](08-backup-restore.md).
7. **Updates** — rebuild the image (`--no-cache` for the layered build) and run
   `bench migrate` for every site. Test on a staging site first.

## Infrastructure layout

| Container | Role |
| --- | --- |
| `backend` | Gunicorn serving the Frappe WSGI app |
| `frontend` | nginx reverse proxy (also serves built assets) |
| `worker-default/short/long` | Background job workers (Celery) |
| `schedule` | Clock/beat scheduler |
| `websocket` | Real-time updates (if enabled in your compose) |
| `configurator` | One-off that writes nginx + supervisor config |
| `db` | MariaDB 11.8 |
| `redis-cache/queue/socketio` | Redis instances for cache, jobs, and real-time |

## Troubleshooting

- **Migration hangs / OOM during build** — give Docker ≥ 4GB RAM
  (Docker Desktop → Settings), or add swap.
- **`mariadb:11.8` not found** — older Docker instances need a registry refresh;
  `docker pull mariadb:11.8` first.
- **Broken/missing CSS after adding an app** — this is the known `/sites/assets`
  split-volume issue; mount a named `sites-assets` volume for `backend`,
  `frontend`, and `configurator`, then `bench build` and restart.
- **Site not reachable** — add your site name to `/etc/hosts` and confirm the
  port in `docker-compose.generated.yml`.

See [Architecture](09-architecture.md) for the full stack diagram and
[Manual install](03-manual-install.md) for the non-Docker path.