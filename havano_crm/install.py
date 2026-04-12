# Copyright (c) 2026, Havano and contributors
# SPDX-License-Identifier: MIT

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Link CRM notes to Lead / Opportunity (standard Note has no reference fields).
NOTE_REFERENCE_FIELDS = {
	"Note": [
		{
			"fieldname": "reference_doctype",
			"fieldtype": "Link",
			"label": "Reference DocType",
			"options": "DocType",
			"insert_after": "content",
		},
		{
			"fieldname": "reference_docname",
			"fieldtype": "Dynamic Link",
			"label": "Reference DocName",
			"options": "reference_doctype",
			"insert_after": "reference_doctype",
		},
	]
}


def ensure_note_reference_fields():
	"""So NoteModal can persist links and get_linked_notes() can load them."""
	create_custom_fields(NOTE_REFERENCE_FIELDS, update=True)


def before_install():
	if "erpnext" not in frappe.get_installed_apps():
		frappe.throw("ERPNext is required for Havano CRM.")


def after_install():
	ensure_note_reference_fields()
	frappe.db.commit()


def after_migrate():
	ensure_note_reference_fields()
	frappe.clear_cache()
