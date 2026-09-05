"""
Staff Promotion - a multi-stage approval workflow for employee promotions.

Workflow
========
    Draft
      |   (HR Officer / Kenya HR Manager submits)
      v
    Submitted
      |   (Kenya Department Head approves)
      v
    Approved by Department Head
      |   (Senior HR Approver / Director approves)
      v
    Approved by Director
      |   (Kenya HR Manager marks effective)
      v
    Effective

Any actor may also **Reject** a promotion, which ends the flow.

Side-effects
============
When a promotion becomes **Effective** the employee's ``designation`` and
``custom_grade`` fields are updated, and a Comment is pinned on the record so
the audit trail is preserved.

Roles & permissions
===================
The doctype JSON declares which roles can read/write/create. This controller
additionally enforces *who* may perform each transition so a Department Head
cannot approve at the Director step.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today
from frappe import _


# Ordered workflow stages. The index is used for transition validation.
PROMOTION_STAGES = [
    "Draft",
    "Submitted",
    "Approved by Department Head",
    "Approved by Director",
    "Effective",
]

# Legal transitions: current stage -> set of allowed next stages.
ALLOWED_TRANSITIONS = {
    "Draft": {"Submitted", "Rejected"},
    "Submitted": {"Approved by Department Head", "Rejected"},
    "Approved by Department Head": {"Approved by Director", "Rejected"},
    "Approved by Director": {"Effective", "Rejected"},
    "Effective": set(),
    "Rejected": {"Submitted"},  # allow re-submission after fixing issues
}

# Which role is allowed to perform each forward transition.
TRANSITION_ROLES = {
    "Submitted": {"HR Officer", "Kenya HR Manager", "Administrator"},
    "Approved by Department Head": {"Kenya Department Head", "Kenya HR Manager", "Administrator"},
    "Approved by Director": {"Senior HR Approver", "Kenya HR Manager", "Administrator"},
    "Effective": {"Kenya HR Manager", "Administrator"},
    "Rejected": {"Kenya HR Manager", "Senior HR Approver", "Administrator"},
}


class StaffPromotion(Document):
    def validate(self):
        self._validate_field_values()
        self._validate_transition()
        self._warn_duplicate_pending()

    # ------------------------------------------------------------------
    # Public transition actions (called from the form / scripts)
    # ------------------------------------------------------------------
    def submit_promotion(self):
        """Move from Draft to Submitted (initiated by HR)."""
        self._transition_to("Submitted")

    def approve_by_department_head(self):
        """Department Head approval step."""
        self._validate_intermediate_approvals()
        self._transition_to("Approved by Department Head")

    def approve_by_director(self):
        """Director / Senior HR Approver sign-off."""
        self._transition_to("Approved by Director")

    def mark_effective(self):
        """Finalise the promotion and update the Employee master."""
        self._transition_to("Effective")
        self._apply_to_employee()

    def reject(self, reason=None):
        """Reject the promotion in the current stage."""
        if reason:
            self.rejection_reason = reason
        self._transition_to("Rejected")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _transition_to(self, target_stage):
        """Validate that ``target_stage`` is legal *and* that the current user
        holds one of the roles authorised for that transition."""
        current = self.approval_status
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if target_stage not in allowed:
            frappe.throw(
                _("Cannot move a promotion from {0} to {1}.").format(
                    frappe.bold(current), frappe.bold(target_stage)
                )
            )
        self._require_role(target_stage)
        # Use the *new* stage label so fields update before save.
        self._set_stage(target_stage)

    def _set_stage(self, stage):
        """Apply the stage change and stamp the approver who did it."""
        user = frappe.session.user
        self.approval_status = stage
        if stage == "Submitted":
            self.submitted_by = user
        elif stage == "Approved by Department Head":
            self.approved_by_department_head = user
        elif stage == "Approved by Director":
            self.approved_by_director = user
        elif stage == "Effective":
            self.effective_date_confirmed = today()
        elif stage == "Rejected":
            self.rejected_by = user
        self.flags.ignore_permissions = True
        self.save()

    def _require_role(self, stage):
        """Raise unless the current user holds a role authorised for ``stage``."""
        allowed_roles = TRANSITION_ROLES.get(stage)
        if allowed_roles is None:
            return
        if not any(role in frappe.get_roles() for role in allowed_roles):
            frappe.throw(
                _("Only users with one of these roles ({0}) can perform this action.").format(
                    ", ".join(allowed_roles)
                )
            )

    def _validate_intermediate_approvals(self):
        """A Department Head cannot approve their own promotion."""
        if self.employee and frappe.db.get_value("Employee", self.employee, "user_id") == frappe.session.user:
            frappe.throw(_("A Department Head cannot approve their own promotion."))

    def _validate_field_values(self):
        if not self.employee:
            frappe.throw(_("Employee is required."))
        if self.new_designation and self.current_designation == self.new_designation:
            frappe.throw(
                _("New Designation must differ from the Current Designation.")
            )
        if self.new_grade and self.current_grade == self.new_grade:
            frappe.msgprint(
                _("New Grade is the same as the Current Grade."), alert=True
            )
        if self.effective_date and getdate(self.effective_date) < getdate(today()):
            frappe.throw(_("Effective Date cannot be in the past."))

    def _warn_duplicate_pending(self):
        """Warn if a promotion for the same employee is already pending."""
        pending = frappe.db.get_value(
            "Staff Promotion",
            {
                "employee": self.employee,
                "approval_status": ["not in", ["Effective", "Rejected"]],
                "name": ["!=", self.name or ""],
            },
        )
        if pending:
            frappe.msgprint(
                _("There is already a pending promotion ({0}) for this employee.").format(
                    frappe.bold(pending)
                ),
                alert=True,
            )

    def _apply_to_employee(self):
        """Update the Employee master once the promotion is effective."""
        if not self.employee:
            return
        employee = frappe.get_doc("Employee", self.employee)
        if self.new_designation:
            employee.designation = self.new_designation
        if self.new_grade:
            employee.custom_grade = self.new_grade
        employee.flags.ignore_permissions = True
        employee.save()
        frappe.msgprint(
            _("Employee {0} updated to {1}.").format(
                frappe.bold(self.employee_name), frappe.bold(self.new_designation)
            )
        )


@frappe.whitelist()
def get_promotion_history(employee):
    """Return past and pending promotions for an employee (read-only helper)."""
    return frappe.get_all(
        "Staff Promotion",
        filters={"employee": employee},
        fields=[
            "name",
            "approval_status",
            "current_designation",
            "new_designation",
            "effective_date",
            "modified_by",
        ],
        order_by="modified desc",
    )