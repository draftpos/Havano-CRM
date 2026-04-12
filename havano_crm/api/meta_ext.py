import frappe


def _options_as_statuses(meta_doctype: str, fieldname: str) -> list[dict]:
	meta = frappe.get_meta(meta_doctype)
	field = meta.get_field(fieldname)
	if not field or not field.options:
		return []
	palette = ["gray", "blue", "orange", "green", "teal", "red", "purple", "pink", "yellow"]
	out = []
	for i, opt in enumerate(field.options.split("\n")):
		name = opt.strip()
		if not name:
			continue
		out.append(
			{
				"name": name,
				"color": palette[i % len(palette)],
				"position": i + 1,
				"type": "Open",
			}
		)
	return out


@frappe.whitelist()
def get_lead_status_options():
	return _options_as_statuses("Lead", "status")


@frappe.whitelist()
def get_deal_status_options():
	# Opportunity.status (Open, Quotation, …) — not sales_stage (Link to Sales Stage)
	return _options_as_statuses("Opportunity", "status")


@frappe.whitelist()
def get_opportunity_status_options():
	return _options_as_statuses("Opportunity", "status")


@frappe.whitelist()
def get_communication_status_options():
	return _options_as_statuses("Communication", "status")
