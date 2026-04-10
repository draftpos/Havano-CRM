import frappe


@frappe.whitelist()
def get_form_scripts(doctype: str, view: str = "Form"):
	"""Same shape as a CRM Form Script list; returns [] when Frappe CRM is not installed."""
	if not frappe.db.exists("DocType", "CRM Form Script"):
		return []
	return frappe.get_all(
		"CRM Form Script",
		filters={"dt": doctype, "view": view, "enabled": 1},
		fields=["name", "dt", "view", "script"],
		order_by="modified asc",
	)
