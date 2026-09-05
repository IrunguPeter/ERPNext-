"""
Kenya HR - a Frappe extension app for ERPNext.

The package is split into focused modules so each concern is self-documenting:

- ``kenya_hr.install``      one-time setup run at install time
- ``kenya_hr.overrides``    doc_events handlers for standard HRMS doctypes
- ``kenya_hr.api``          whitelisted helper endpoints
- ``kenya_hr.hris_k_sync``  optional integration with the Kenya HRIS-K API
- ``kenya_hr.doctype``      custom DocTypes owned by this app
- ``kenya_hr.report``       custom reports shipped with this app

See ``docs/05-kenya-hr-app.md`` for a guided walkthrough.
"""