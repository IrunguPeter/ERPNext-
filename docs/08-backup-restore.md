# Backup & Restore

## Automated backup

`scripts/backup.sh` runs `bench backup` inside the backend container:

```bash
# database only (fast, recommended hourly/daily)
./scripts/backup.sh erp.localhost

# database + public/private files (recommended daily/weekly)
./scripts/backup.sh erp.localhost --with-files
```

Backups are written to `/home/frappe/frappe-bench/backups` *inside* the
container. Fetch them out with:

```bash
# copy a named backup out of the container
docker compose -f docker-compose.generated.yml cp \
  backend:/home/frappe/frappe-bench/backups/mysite-2026-01-01.sql.gz ./backups/
```

## Keep a copy off the machine

A backup on the same disk is not a backup. Add a cron entry:

```cron
0 2 * * * cd /home/peter/projects/ERPNext- && ./scripts/backup.sh erp.localhost --with-files >/dev/null 2>&1
0 3 * * * rsync -av /home/peter/projects/ERPNext-/backups/ you@offsite:/backups/erp
```

## Manual weekend rotation

```bash
# keep 14 daily + 8 weekly, then ship
ls -1t backups/*.gz | tail -n +15 | xargs -r rm --
```

## Restore

```bash
# 1. copy the archive into the container
docker compose -f docker-compose.generated.yml cp \
  ./backups/mysite-2026-01-01.sql.gz backend:/home/frappe/frappe-bench/backups/

# 2. restore it (uses --force)
./scripts/restore.sh erp.localhost /home/frappe/frappe-bench/backups/mysite-2026-01-01.sql.gz

# 3. clear cache and restart workers
./scripts/bench.sh erp.localhost clear-cache
docker compose -f docker-compose.generated.yml restart backend schedule worker-default
```

## Backup hygiene checklist

- [ ] Credentials / secrets are kept out of version control
- [ ] Off-box copies exist and a restore has been rehearsed
- [ ] Broken/failed backups are surfaced (cron mail, alerting)
- [ ] Multi-site: run `bench --site <each> backup`