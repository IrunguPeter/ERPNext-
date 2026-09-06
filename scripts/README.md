# Scripts

Every script is idempotent where possible and prints what it is doing.

| Script | Purpose |
| --- | --- |
| [`deploy-docker.sh`](deploy-docker.sh) | Full Docker deployment: builds the ERPNext + HRMS + Kenya ERP image, starts the stack, and creates the site with the app installed. |
| [`teardown-docker.sh`](teardown-docker.sh) | Stops the stack. Use `--volumes` to also **delete** your data. |
| [`bench.sh`](bench.sh) | Runs `bench` commands inside the backend container for a given site. |
| [`backup.sh`](backup.sh) | Creates a database (and optional file) backup. |
| [`restore.sh`](restore.sh) | Restores a database backup from inside the container. |

## Common usage

```bash
# one-shot deployment (localhost demo)
./scripts/deploy-docker.sh

# custom site / passwords
./scripts/deploy-docker.sh --site erp.example.com --admin-pass S3cret --db-pass S3cret --port 80

# list apps on the site
./scripts/bench.sh erp.localhost list-apps

# open a python console
./scripts/bench.sh erp.localhost console

# daily backup (database only)
./scripts/backup.sh erp.localhost

# full backup including files
./scripts/backup.sh erp.localhost --with-files
```

## Development loop

When making changes to `apps/kenya_erp`, rebuild the image and re-run a
migration, or use the `--dev` flag of `deploy-docker.sh` and iterate with:

```bash
docker compose -f docker-compose.generated.yml exec backend bench --site erp.localhost migrate
```

See [docs/02-docker-deployment.md](../docs/02-docker-deployment.md) and
[docs/05-kenya-hr-app.md](../docs/05-kenya-hr-app.md) for details.