import frappe
from frappe import _

from havano_crm.compat import notify_user


def after_insert(doc, method):
	if doc.reference_type in ["Lead", "Opportunity"] and doc.reference_name and doc.allocated_to:
		fieldname = "lead_owner" if doc.reference_type == "Lead" else "opportunity_owner"
		owner = frappe.db.get_value(doc.reference_type, doc.reference_name, fieldname)
		if not owner:
			frappe.db.set_value(
				doc.reference_type, doc.reference_name, fieldname, doc.allocated_to, update_modified=False
			)

	if doc.reference_type in ["Lead", "Opportunity", "ToDo"] and doc.reference_name and doc.allocated_to:
		notify_assigned_user(doc)


def on_update(doc, method):
	if (
		doc.has_value_changed("status")
		and doc.status == "Cancelled"
		and doc.reference_type in ["Lead", "Opportunity", "ToDo"]
		and doc.reference_name
		and doc.allocated_to
	):
		notify_assigned_user(doc, is_cancelled=True)


def notify_assigned_user(doc, is_cancelled=False):
	_doc = frappe.get_doc(doc.reference_type, doc.reference_name)
	owner = frappe.get_cached_value("User", frappe.session.user, "full_name")
	notification_text = get_notification_text(owner, doc, _doc, is_cancelled)

	message = (
		_("Your assignment on {0} {1} has been removed by {2}").format(
			doc.reference_type, doc.reference_name, owner
		)
		if is_cancelled
		else _("{0} assigned a {1} {2} to you").format(owner, doc.reference_type, doc.reference_name)
	)

	redirect_to_doctype, redirect_to_name = get_redirect_to_doc(doc)

	notify_user(
		{
			"owner": frappe.session.user,
			"assigned_to": doc.allocated_to,
			"notification_type": "Assignment",
			"message": message,
			"notification_text": notification_text,
			"reference_doctype": doc.reference_type,
			"reference_docname": doc.reference_name,
			"redirect_to_doctype": redirect_to_doctype,
			"redirect_to_docname": redirect_to_name,
		}
	)


def get_notification_text(owner, doc, reference_doc, is_cancelled=False):
	name = doc.reference_name
	doctype = (doc.reference_type or "").lower()

	if doctype == "lead":
		name = reference_doc.lead_name or name
	elif doctype == "opportunity":
		name = reference_doc.customer_name or reference_doc.title or name

	if doctype in ("lead", "opportunity"):
		if is_cancelled:
			return f"""
                <div class="mb-2 leading-5 text-ink-gray-5">
                    <span>{ _('Your assignment on {0} {1} has been removed by {2}').format(
                        doctype,
                        f'<span class="font-medium text-ink-gray-9">{ name }</span>',
                        f'<span class="font-medium text-ink-gray-9">{ owner }</span>'
                    ) }</span>
                </div>
            """

		return f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{ owner }</span>
                <span>{ _('assigned a {0} {1} to you').format(
                    doctype,
                    f'<span class="font-medium text-ink-gray-9">{ name }</span>'
                ) }</span>
            </div>
        """

	if doctype == "todo":
		label = frappe.utils.strip_html(reference_doc.description or "")[:80] or name
		if is_cancelled:
			return f"""
                <div class="mb-2 leading-5 text-ink-gray-5">
                    <span>{ _('Your assignment on task {0} has been removed by {1}').format(
                        f'<span class="font-medium text-ink-gray-9">{ label }</span>',
                        f'<span class="font-medium text-ink-gray-9">{ owner }</span>'
                    ) }</span>
                </div>
            """
		return f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{ owner }</span>
                <span>{ _('assigned a new task {0} to you').format(
                    f'<span class="font-medium text-ink-gray-9">{ label }</span>'
                ) }</span>
            </div>
        """


def get_redirect_to_doc(doc):
	if doc.reference_type == "ToDo":
		reference_doc = frappe.get_doc(doc.reference_type, doc.reference_name)
		return reference_doc.reference_type, reference_doc.reference_name

	return doc.reference_type, doc.reference_name
