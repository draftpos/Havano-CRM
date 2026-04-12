import frappe


def get_site_info(site_info):
	return {"activation": get_sales_data(site_info)}


def get_sales_data(site_info):
	activation_level = site_info.get("activation", {}).get("activation_level", 0)
	sales_data = site_info.get("activation", {}).get("sales_data", [])
	doctypes = [
		"Lead",
		"Opportunity",
		"Customer",
		"Contact",
		"ToDo",
		"Note",
		"Call Log",
	]

	for doctype in doctypes:
		try:
			count = frappe.db.count(doctype)
		except Exception:
			count = 0
		sales_data.append({doctype: count})

	return {"activation_level": activation_level, "sales_data": sales_data}
