"""
Kenya ERP - a consolidated Frappe extension app for ERPNext.

The package merges the three former applications (Kenya HR, Kenya Procurement,
Kenya Fleet) and is split into focused modules so each concern stays clear:

- ``kenya_erp.install``     one-time setup run at install time
- ``kenya_erp.overrides``   doc_events handlers for standard + custom doctypes
- ``kenya_erp.api``         whitelisted helper endpoints
- ``kenya_erp.hris_k_sync`` optional integration with the Kenya HRIS-K API
- ``kenya_erp.egp_sync``    optional E-GP (procurement) connector
- ``kenya_erp.gvms_sync``   optional GVMS (fleet) connector
- ``kenya_erp.doctype``     custom DocTypes owned by this app
- ``kenya_erp.report``      custom reports shipped with this app
"""
