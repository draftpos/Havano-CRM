import frappe


@frappe.whitelist()
def get_first_lead():
	lead = frappe.get_all(
		"Lead",
		filters={"status": ["!=", "Converted"]},
		fields=["name"],
		order_by="creation",
		limit=1,
	)
	return lead[0].name if lead else None


@frappe.whitelist()
def get_first_deal():
	deal = frappe.get_all(
		"Opportunity",
		fields=["name"],
		order_by="creation",
		limit=1,
	)
	return deal[0].name if deal else None
