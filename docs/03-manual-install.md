# Manual Install (non-Docker)

For bare-metal or VPS installs, or when you need deep system access, use this
manual path. It matches the ERPNext guidance for:
- Python 3.14 via `uv`, Node 24, MariaDB 11.8, Redis 7, Yarn 1.22+
- Ubuntu 24.04 / Debian 13 (this machine is Zorin OS 18.1 = Ubuntu 24.04 base)

> System check on this laptop: Python 3.14.7, Node 24.20.0, MariaDB 10.11.14,
> Redis 7.0.15, Docker 29.7.2 — 8-core / 7.6 GB RAM.
> NOTE: MariaDB 10.11 supports Frappe v15; upgrade to **MariaDB 11.8** for v16.

## 1. System dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  git curl wget \
  build-essential \
  python3-dev python3-pip python3-venv \
  libffi-dev libssl-dev libjpeg-dev zlib1g-dev \
  libmysqlclient-dev pkg-config \
  redis-server supervisor nginx cron \
  xvfb libfontconfig fontconfig wkhtmltopdf
```

## 2. Python 3.14 + Node 24 (via uv, nvm)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.14 --default

curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g yarn@1.22

export PATH="$HOME/.local/bin:$PATH"
```

## 3. MariaDB 11.8 for Frappe v16

```bash
curl -LsS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup | \
  sudo bash -s -- --mariadb-server-version=11.8
sudo apt update && sudo apt install -y mariadb-server mariadb-client
sudo mysql_secure_installation
```

Append to `/etc/mysql/mariadb.conf.d/50-server.cnf` under `[mysqld]`:

```ini
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
innodb-file-format = barracuda
innodb-file-per-table = 1
innodb-large-prefix = 1
innodb-buffer-pool-size = 2G
wait_timeout = 28800
interactive_timeout = 28800
```

```bash
sudo systemctl restart mariadb
mysql --version   # expect Ver 15.1 Distrib 11.8.x-MariaDB
```

## 4. Bench + app setup (run as a non-root user, e.g. `frappe`)

```bash
sudo adduser --disabled-password --gecos '' frappe
sudo usermod -aG sudo frappe
sudo su - frappe

mkdir -p ~/apps && cd ~/apps
git clone https://github.com/IrunguPeter/ERPNext- erpnext-kr   # or your fork
cd erpnext-kr

uv tool install frappe-bench
export PATH="$PATH:$HOME/.local/bin"
export BENCH_APP_SOURCE="$(pwd)/apps/kenya_hr"
```

Create a bench, then fetch the apps:

```bash
uv run bench init --frappe-branch version-16 frappe-bench --verbose
cd frappe-bench

uv run bench get-app --branch version-16 https://github.com/frappe/erpnext
uv run bench get-app --branch version-16 https://github.com/frappe/hrms
uv run bench get-app "$BENCH_APP_SOURCE" kenya_hr

uv run bench new-site erp.example.com \
  --mariadb-root-password 'Your_DB_Root' \
  --admin-password 'Your_Admin'

uv run bench --site erp.example.com install-app erpnext
uv run bench --site erp.example.com install-app hrms
uv run bench --site erp.example.com install-app kenya_hr

uv run bench build
uv run bench start
```

Open `http://erp.example.com:8000` and log in as `Administrator`.

## 5. Production (replaces `bench start`)

```bash
exit   # back to root
sudo apt install -y ansible
sudo env "PATH=$PATH" bench setup production frappe
bench setup nginx
sudo nginx -t && sudo systemctl reload nginx
sudo supervisorctl restart all
```

## Keep it running

```bash
bench update             # pull + migrate + build
bench --site site backup
bench doctor
```

See also `erpnext-setup-guide.md` for the original full guide and the
PostgreSQL compatibility notes (MariaDB is the supported database for ERPNext).