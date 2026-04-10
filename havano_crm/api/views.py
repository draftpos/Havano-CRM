import frappe


@frappe.whitelist()
def get_views(doctype: str):
	"""Synthetic list/kanban/group_by views (no CRM View Settings DocType)."""
	doctypes = [doctype] if doctype else [
		"Lead",
		"Opportunity",
		"Contact",
		"Customer",
		"Note",
		"ToDo",
		"Call Log",
	]
	view_types = ("list", "kanban", "group_by")
	out: list[dict] = []

	for dt in doctypes:
		for vt in view_types:
			out.append(
				{
					"name": f"std-{dt}-{vt}",
					"dt": dt,
					"type": vt,
					"user": "",
					"is_standard": 1,
					"public": 0,
					"pinned": 0,
					"is_default": dt == "Lead" and vt == "list",
					"label": None,
				}
			)

	return out
