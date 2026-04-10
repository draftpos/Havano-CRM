import frappe


@frappe.whitelist()
def get_ui_settings():
	"""Branding for the Vue shell (replaces DocType FCRM Settings)."""
	try:
		ws = frappe.get_single("Website Settings")
		return {
			"name": "Havano UI",
			"brand_name": ws.app_name or frappe.get_system_settings("app_name") or "Havano CRM",
			"brand_logo": ws.banner_image,
			"favicon": ws.favicon,
		}
	except Exception:
		return {
			"name": "Havano UI",
			"brand_name": "Havano CRM",
			"brand_logo": None,
			"favicon": None,
		}
