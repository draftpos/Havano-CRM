import frappe
from frappe import _


def validate(doc, method):
	update_deals_email_mobile_no(doc)


def update_deals_email_mobile_no(doc):
	"""Sync Opportunity contact_email / contact_mobile when Contact changes (ERPNext links via contact_person)."""
	if not doc.name:
		return

	# Frappe CRM uses child table CRM Contacts on deals; keep support if that app is installed.
	if frappe.db.exists("DocType", "CRM Contacts"):
		linked = frappe.get_all(
			"CRM Contacts",
			filters={"contact": doc.name, "is_primary": 1},
			fields=["parent"],
		)
		for row in linked:
			if not frappe.db.exists("Opportunity", row.parent):
				continue
			curr = frappe.db.get_value(
				"Opportunity",
				row.parent,
				["contact_email", "contact_mobile"],
				as_dict=True,
			)
			if curr and (
				curr.get("contact_email") != doc.email_id
				or curr.get("contact_mobile") != doc.mobile_no
			):
				frappe.db.set_value(
					"Opportunity",
					row.parent,
					{
						"contact_email": doc.email_id,
						"contact_mobile": doc.mobile_no,
					},
				)

	# Standard ERPNext: Opportunity.contact_person -> Contact
	for opp_name in frappe.get_all(
		"Opportunity",
		filters={"contact_person": doc.name},
		pluck="name",
	):
		curr = frappe.db.get_value(
			"Opportunity",
			opp_name,
			["contact_email", "contact_mobile"],
			as_dict=True,
		)
		if curr and (
			curr.get("contact_email") != doc.email_id
			or curr.get("contact_mobile") != doc.mobile_no
		):
			frappe.db.set_value(
				"Opportunity",
				opp_name,
				{
					"contact_email": doc.email_id,
					"contact_mobile": doc.mobile_no,
				},
			)


@frappe.whitelist()
def get_linked_deals(contact: str):
	"""Get linked deals for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if frappe.db.exists("DocType", "CRM Contacts"):
		deal_names = frappe.get_all(
			"CRM Contacts",
			filters={"contact": contact, "parenttype": "Opportunity"},
			pluck="parent",
			distinct=True,
		)
	else:
		deal_names = frappe.get_all(
			"Opportunity",
			filters={"contact_person": contact},
			pluck="name",
		)

	deals = []
	for name in deal_names:
		deal = frappe.get_cached_doc("Opportunity", name)
		row = deal.as_dict()
		# Aliases for UI that still expects CRM Deal field names
		row["organization"] = row.get("customer_name")
		row["email"] = row.get("contact_email")
		row["mobile_no"] = row.get("contact_mobile")
		deals.append(row)

	return deals


@frappe.whitelist()
def create_new(contact: str, field: str, value: str):
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact.email_ids) == 0 else 0}
		contact.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact.phone_nos) == 0 else 0}
		contact.append("phone_nos", mobile_no)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def set_as_primary(contact: str, field: str, value: str):
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def search_emails(txt: str):
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results
