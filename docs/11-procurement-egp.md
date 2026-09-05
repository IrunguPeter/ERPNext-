# Procurement & E-GP Integration

The `kenya_procurement` app adds a **public-procurement section** to ERPNext
that mirrors Kenya's **E-GP (Electronic Government Procurement)** system,
operated by the National Treasury under the *Public Procurement and Asset
Disposal Act, 2015* (PPADA) and its regulations.

## Legal background (why this matters)

- Since **1 July 2025** all public procurement runs exclusively through E-GP at
  <https://egpkenya.go.ke>. From **1 July 2026** there are **no exemptions**:
  an unregistered supplier cannot submit a single government bid by any channel.
- Supplier registration is mandatory and auto-verified in real time against
  **iTax** (KRA PIN), the **Business Registration Service** (company number) and
  the **Integrated Population Registration System** (directors' IDs).
- Procuring entities must be registered on E-GP (Reg 24/54, PPADR 2020) and
  conduct initiation, planning, evaluation, award and contract management in it.
- **AGPO** set-asides (youth / women / persons-with-disabilities = 30% of
  procurement) are flagged at registration and reserved in awarding.

## What the app tracks

| ERPNext doctype | E-GP equivalent |
| --- | --- |
| `Supplier Onboarding` | E-GP supplier profile (BRS no., KRA PIN, authorised rep, business categories, AGPO, county) |
| `Tender` | Tender notice (Tender ID, Reference No., Procuring Entity, Method, Start/End datetimes) |
| `Tender Bid` (child table) | Bid submission on E-GP (reference, amount, evaluation result) |
| `Kenya EGP Settings` | Connector configuration (gateway endpoint, token, toggles) |

Plus a **Tender Pipeline** script report and (optional) a daily sync job.

## Integration modes

### 1. Manual mirror (default, zero-config)

Procurement officers keep the records by hand from the E-GP portal. Nothing
phone-homes, works offline, and the fields map 1:1 to the portal. This is the
recommended starting mode.

### 2. Gateway connector (opt-in)

**The public E-GP portal does not publish a REST API.** The connector in
`kenya_procurement/egp_sync.py` therefore talks to a *gateway endpoint you
control* (your own middleware that pulls from E-GP, or the Treasury's API once
published). When the official API opens, this one module is where you point it.

Enable it:

1. **Kenya EGP Settings → Enable E-GP Connector** ✔
2. Set **API Gateway Endpoint** (e.g. `https://egp-gateway.yourorg.example/api/v1`)
3. Set **API Token / Key**
4. Tick **Synchronise Tenders** / **Synchronise Suppliers** as needed

What happens when enabled:

- the **daily** scheduler runs `egp_sync.sync_all_due()` (also re-checks the
  switch inside — safe even if you flip it while the job is queued),
- `GET {endpoint}/tenders` → tenders are **upserted** on the E-GP `Tender ID`,
- `GET {endpoint}/suppliers/{business_registration_no}` → `Supplier Onboarding`
  `egp_status` is refreshed,
- `Supplier` updates auto-annotate the name with its E-GP status
  (`[EGP Registered] ...`).

### Expected JSON shapes (gateway contract)

Tenders (list endpoint):

```json
{
  "tenders": [
    {
      "tender_id": 27214,
      "tender_reference": "KYU/828/RFQ/0174/2026-27",
      "title": "PROVISION FOR THE HIRE OF CLEAN WHITE TENTS AND PLASTIC CHAIRS...",
      "procuring_entity": "KIRINYAGA UNIVERSITY",
      "procurement_method": "Request for Quotation (RFQ)",
      "start_datetime": "2026-08-12 16:30:00",
      "closing_datetime": "2026-08-19 11:00:00",
      "status": "Open"
    }
  ]
}
```

Supplier (single endpoint):

```json
{
  "business_registration_no": "PVC-A-1234567",
  "status": "Registered"
}
```

Only fields the ERPNext record lacks are filled (never overwrite existing
input). Use the whitelisted `mirror_tender` endpoint to test one record.

## Roles

| Role | Purpose |
| --- | --- |
| `Procurement Manager` | Full control: settings, connectors, delete rights |
| `Procurement Officer` | Daily ops: onboard suppliers, maintain tenders & bids |

## Reports

**Tender Pipeline** — status breakdown bar chart, summary counts, and a table
sorted by closing deadline. Filter by status, method, entity.

## Notes on data hygiene

- A supplier's E-GP **business email must be a private domain** (public email
  providers are rejected at registration) — captured on `Supplier Onboarding`.
- Directors / authorised reps need a National ID; foreign vendors need a
  BRS-registered entity and a certified Power of Attorney.
- Keep categories complete — procuring entities *search* by registered
  categories, so thin registrations miss tenders.