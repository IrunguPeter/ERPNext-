# HR Configuration Guide

This is the operating manual for the HR module. It covers the three areas this
project adds on top of stock ERPNext/HRMS: **employees**, **leave management**,
and **promotions**.

## 1. Employees

**HR → Employee → New.** The Kenya HR app adds a *Kenya* section with:

| Field | Purpose | Required (recommended) |
| --- | --- | --- |
| National ID Number | Kenya national identity card | yes |
| KRA PIN | Kenya Revenue Authority PIN | yes |
| NHIF Number | Hospital fund membership | yes |
| NSSF Number | Pension fund membership | yes |
| Unified Payroll Number (UPN) | Public payroll unique ID | for public servants |
| Grade | Pay grade used by promotions | recommended |
| Staff Roll | Official staff serial number | for public servants |

### Employment types

Create the ones you use: `Permanent`, `Contract`, `Casual`, `Internship`.
Each employment type can later map to a Leave Policy (see below).

### Employee self-user (optional)

HRMS links a **User** per employee (`Employee.user_id`). Create users with the
`Employee` role so staff can view their record and apply for leave.

## 2. Leave Management

### Statutory leave types (created automatically)

| Leave Type | Days | Notes |
| --- | --- | --- |
| Annual Leave | 21 | carry-forward enabled (12 months, max 21 days, expires 30th June) |
| Sick Leave | 7 | medical certificate required by policy |
| Maternity Leave | 90 | statutory 3 months |
| Paternity Leave | 14 | statutory minimum |
| Compassionate Leave | 7 | death of immediate family |
| Study Leave | 30 | approved studies/exams |

### Leave policy (per employment type)

1. **HR → Leave and Attendance → Leave Policy → New**.
2. Give the policy a name (e.g. `Permanent Staff`).
3. Add the leave types above with appropriate annual allocations.
4. In **Employee**, set the policy on each employee's **Leave Policy** field.

### Allocation & application workflow

```text
HR allots   → Employee applies   → Manager/Dept Head approves → HR reviews
```
- Allocations: `Leave Allocation` (HR creates, or via accrual rules).
- Applications: `Leave Application` — the Kenya HR app annotates the
  application with the employee's remaining balance on submit.
- Optional HRIS-K sync fires on submit/cancel when enabled in Settings.

## 3. Promotions (Staff Promotion)

A promotion flows through a controlled state machine:

```text
Draft ──> Submitted ──> Approved by Dept Head ──> Approved by Director ──> Effective
   │          │                  │                        │
   └──────────┴──────────────────┴────────────────────────┘──> Rejected
```

| State | Who can perform | What happens |
| --- | --- | --- |
| Draft | HR Officer / Kenya HR Manager | record created; fields can still be edited |
| Submitted | same as above (Submit button) | edits are locked |
| Approved by Department Head | Kenya Department Head | first sign-off |
| Approved by Director | Senior HR Approver / Director | second sign-off |
| Effective | Kenya HR Manager (Mark Effective) | **updates the Employee** designation + grade |
| Rejected | Kenya HR Manager / Senior HR Approver | requires a rejection reason; can re-submit later |

Rules enforced by the controller:

- `New Designation` must differ from `Current Designation`.
- `Effective Date` cannot be in the past.
- A Department Head cannot approve their own promotion.
- Every transition is recorded with the acting user (`submitted_by`,
  `approved_by_department_head`, ...) for a full audit trail.
- A warning is raised if another promotion is already pending for the employee.

Optionally toggle `promotion_requires_director_approval` off in Settings to
skip the Director stage.

## 4. Reports

- **Staff Promotion Log** (`Kenya HR → Reports`) — pipeline status, filterable
  by status / department / effective-date range.
- **Leave Balance** (stock HRMS report) — balances per leave type.
- HRIS-K sync events are captured in the `Log` doctype.

## 5. Workspace setup (one-off, in the UI)

After first login, create a *Workspace* called **Kenya HR** with shortcuts to
`Staff Promotion`, `Kenya HR Settings`, and the Promotion Log report. The roles
are already created by the app — see [Roles & permissions](07-roles-permissions.md).