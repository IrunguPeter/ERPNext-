# HRIS-K Integration

The Kenya HR app provides an opt-in client for the government's
**HRIS-K** (Human Resource Information System – Kenya, https://uhr.kenya.go.ke).

## How it works

- Wiring lives in `kenya_hr/hris_k_sync.py`.
- Nothing happens until **Enable HRIS-K Synchronisation** is ticked in
  **Kenya HR Settings**.
- When enabled:
  - an **Employee** is pushed on create (`after_insert`) and update (`on_update`),
  - a **Leave Application** is pushed on submit, and cancelled on cancel,
  - a daily scheduler job (`sync_all_employees_due`) re-syncs recently-changed
    employees.
- Payloads use the Kenya identity fields added by this app (`custom_national_id`,
  `custom_kra_pin`, ...). Responses — and errors — are logged to the `Log`
  doctype; failures never break the main transaction.

## Configuration

1. Open **Kenya HR → Kenya HR Settings**.
2. Enter the **HRIS-K Base URL**, **Organization Code**, and **API Key**
   (the key is stored encrypted in the Password field).
3. Tick **Enable HRIS-K Synchronisation** and save.

## Adapting to the live API

The HRIS-K endpoint contract is not public. Treat `hris_k_sync.py` as an
adapter: the four functions (`sync_employee_to_hris`, `sync_leave_to_hris`,
`cancel_leave_in_hris`, `sync_all_employees_due`) each build one payload and
POST to one endpoint. Rename payload keys / paths to match the official
swagger/OpenAPI spec, commit, and migrate.

## Security notes

- The API key is read via `settings.get_password("hris_k_api_key")` and never
  logged.
- Requests are HTTPS-only and time out after 10s.
- The connectors run inside the backend worker; use the app's
  `Log`/`Error Log` to monitor.
- Add outbound egress for `uhr.kenya.go.ke` in your firewall / proxy if you
  deploy behind one.

## Rollout checklist

- [ ] API credentials provided by the HRIS-K administrator
- [ ] Test Employee sync on one record
- [ ] Test Leave submit / cancel sync
- [ ] Confirm no regressions with sync *disabled* (default)
- [ ] Monitor `Log` for 4xx/5xx and tune payload mappings