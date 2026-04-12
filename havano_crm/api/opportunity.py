"""Opportunity (deal) contact helpers for ERPNext — replaces Frappe CRM ``crm_deal`` APIs."""

from __future__ import annotations

import frappe
from erpnext.crm.doctype.lead.lead import make_opportunity
from frappe import _
from frappe.utils import today

_SKIP_OPPORTUNITY_LAYOUT_FIELDS = frozenset(
	{
		"Tab Break",
		"Section Break",
		"Column Break",
		"HTML",
		"Heading",
		"Fold",
		"Button",
		"Barcode",
	}
)


def _clean_child_rows(rows: list, child_doctype: str) -> list:
	if not child_doctype or not frappe.db.exists("DocType", child_doctype):
		return []
	cmeta = frappe.get_meta(child_doctype)
	valid = {f.fieldname for f in cmeta.fields}
	out = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		one = {k: v for k, v in row.items() if k in valid and not str(k).startswith("_")}
		if one:
			out.append(one)
	return out


def _filter_opportunity_payload(raw: dict) -> dict:
	"""Keep only real Opportunity / child fields; map legacy CRM aliases."""
	if not raw:
		return {}
	data = dict(raw)
	if data.get("organization") and not data.get("customer_name"):
		data["customer_name"] = data.pop("organization")
	data.pop("organization", None)

	meta = frappe.get_meta("Opportunity")
	out: dict = {}
	for df in meta.fields:
		if df.fieldtype in _SKIP_OPPORTUNITY_LAYOUT_FIELDS:
			continue
		if df.fieldname not in data:
			continue
		val = data[df.fieldname]
		if val is None:
			continue
		if df.fieldname == "name" and not str(val).strip():
			continue
		if df.fieldtype == "Table":
			if isinstance(val, list):
				out[df.fieldname] = _clean_child_rows(val, df.options)
		elif df.fieldtype == "Table MultiSelect":
			if isinstance(val, list):
				out[df.fieldname] = val
		else:
			out[df.fieldname] = val
	return out


def _default_company() -> str | None:
	c = frappe.defaults.get_user_default("Company")
	if c and frappe.db.exists("Company", c):
		return c
	gd = frappe.db.get_single_value("Global Defaults", "default_company")
	if gd and frappe.db.exists("Company", gd):
		return gd
	names = frappe.get_all("Company", pluck="name", limit_page_length=1)
	return names[0] if names else None


def _apply_opportunity_defaults(data: dict) -> None:
	if not data.get("company"):
		data["company"] = _default_company()
	if not data.get("transaction_date"):
		data["transaction_date"] = today()
	if not data.get("currency") and data.get("company"):
		data["currency"] = frappe.db.get_value("Company", data["company"], "default_currency")
	if not data.get("opportunity_from"):
		data["opportunity_from"] = "Lead"


@frappe.whitelist()
def get_lead_convert_deal_defaults(lead: str):
	"""Default Opportunity field values when converting a specific Lead (Series, From, Party, Company, etc.)."""
	if not lead or not frappe.db.exists("Lead", lead):
		frappe.throw(_("Lead not found"), frappe.DoesNotExistError)
	frappe.has_permission("Lead", "read", lead, throw=True)
	if frappe.db.get_value("Lead", lead, "status") == "Converted":
		frappe.throw(_("This lead has already been converted"))
	tmp = frappe.new_doc("Opportunity")
	co = _default_company()
	data = {
		"naming_series": tmp.naming_series,
		"opportunity_from": "Lead",
		"party_name": lead,
		"company": co,
		"transaction_date": str(today()),
	}
	_apply_opportunity_defaults(data)
	# Keep Lead linkage explicit after generic defaults
	data["opportunity_from"] = "Lead"
	data["party_name"] = lead
	return data


@frappe.whitelist()
def get_create_deal_defaults():
	"""Defaults for the create-deal modal (aligned with :func:`_apply_opportunity_defaults`)."""
	co = _default_company()
	return {
		"opportunity_from": "Lead",
		"transaction_date": str(today()),
		"company": co,
	}


@frappe.whitelist()
def create_deal(doc):
	"""Create an ERPNext Opportunity from the CRM quick-entry form (no Frappe CRM app)."""
	if isinstance(doc, str):
		doc = frappe.parse_json(doc)
	if not isinstance(doc, dict):
		frappe.throw(_("Invalid data"))

	frappe.has_permission("Opportunity", "create", throw=True)

	row = _filter_opportunity_payload(doc)
	_apply_opportunity_defaults(row)
	if not row.get("party_name"):
		row.pop("party_name", None)

	opp = frappe.get_doc({"doctype": "Opportunity", **row})
	opp.insert()
	return opp.name


@frappe.whitelist()
def convert_lead_to_deal(lead, deal=None, existing_contact=None, existing_organization=None):
	"""Convert Lead → Opportunity; optional form overrides and existing Customer / Contact."""
	if not lead:
		frappe.throw(_("Lead is required"))
	if not frappe.db.exists("Lead", lead):
		frappe.throw(_("Lead not found"), frappe.DoesNotExistError)
	if frappe.db.get_value("Lead", lead, "status") == "Converted":
		frappe.throw(_("This lead has already been converted"))
	frappe.has_permission("Lead", "write", lead, throw=True)
	frappe.has_permission("Opportunity", "create", throw=True)

	deal_d = frappe.parse_json(deal) if isinstance(deal, str) else (deal or {})
	existing_contact = (existing_contact or "").strip()
	existing_organization = (existing_organization or "").strip()

	opp = make_opportunity(lead)
	for key, val in _filter_opportunity_payload(deal_d).items():
		if key in ("name", "doctype"):
			continue
		opp.set(key, val)

	if existing_contact and frappe.db.exists("Contact", existing_contact):
		opp.contact_person = existing_contact
		crow = frappe.db.get_value(
			"Contact",
			existing_contact,
			["email_id", "mobile_no"],
			as_dict=True,
		)
		if crow:
			if crow.get("email_id"):
				opp.contact_email = crow.email_id
			if crow.get("mobile_no"):
				opp.contact_mobile = crow.mobile_no

	if existing_organization and frappe.db.exists("Customer", existing_organization):
		opp.opportunity_from = "Customer"
		opp.party_name = existing_organization

	opp.insert()
	return opp.name


def _linked_contact_names(opportunity: str) -> list[str]:
	return frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Contact",
			"link_doctype": "Opportunity",
			"link_name": opportunity,
		},
		pluck="parent",
		distinct=True,
	)


def _contact_row(contact_name: str) -> dict | None:
	row = frappe.db.get_value(
		"Contact",
		contact_name,
		["name", "full_name", "email_id", "mobile_no", "image"],
		as_dict=True,
	)
	if not row:
		return None
	return {
		"name": row.name,
		"full_name": row.full_name or row.name,
		"email": row.email_id,
		"mobile_no": row.mobile_no,
		"image": row.image,
	}


@frappe.whitelist()
def get_opportunity_contacts(name: str):
	"""Return contacts linked to this Opportunity (via Contact.links), CRM-shaped for the UI."""
	if not frappe.db.exists("Opportunity", name):
		frappe.throw(_("Opportunity not found"), frappe.DoesNotExistError)
	if not frappe.has_permission("Opportunity", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	primary = frappe.db.get_value("Opportunity", name, "contact_person")
	linked = list(dict.fromkeys(_linked_contact_names(name)))
	if primary and primary not in linked:
		linked.insert(0, primary)
	elif primary and primary in linked:
		linked.remove(primary)
		linked.insert(0, primary)
	elif not linked and primary:
		linked = [primary]

	out: list[dict] = []
	for cname in linked:
		row = _contact_row(cname)
		if row:
			row["is_primary"] = cname == primary
			out.append(row)
	return out


@frappe.whitelist()
def add_contact(opportunity: str, contact: str):
	if not frappe.db.exists("Opportunity", opportunity):
		frappe.throw(_("Opportunity not found"), frappe.DoesNotExistError)
	if not frappe.db.exists("Contact", contact):
		frappe.throw(_("Contact not found"), frappe.DoesNotExistError)
	if not frappe.has_permission("Opportunity", "write", opportunity):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("Contact", contact)
	for row in doc.links or []:
		if row.link_doctype == "Opportunity" and row.link_name == opportunity:
			return contact

	doc.append("links", {"link_doctype": "Opportunity", "link_name": opportunity})
	doc.save()

	primary = frappe.db.get_value("Opportunity", opportunity, "contact_person")
	if not primary:
		set_primary_contact(opportunity, contact)

	return contact


@frappe.whitelist()
def remove_contact(opportunity: str, contact: str):
	if not frappe.db.exists("Opportunity", opportunity):
		frappe.throw(_("Opportunity not found"), frappe.DoesNotExistError)
	if not frappe.has_permission("Opportunity", "write", opportunity):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("Contact", contact)
	to_drop = [
		row
		for row in (doc.links or [])
		if row.link_doctype == "Opportunity" and row.link_name == opportunity
	]
	for row in to_drop:
		doc.remove(row)
	doc.save()

	primary = frappe.db.get_value("Opportunity", opportunity, "contact_person")
	if primary == contact:
		remaining = _linked_contact_names(opportunity)
		opp = frappe.get_doc("Opportunity", opportunity)
		if remaining:
			_set_primary_on_opportunity_doc(opp, remaining[0])
		else:
			opp.contact_person = None
			opp.contact_email = None
			opp.contact_mobile = None
		opp.save()

	return True


def _set_primary_on_opportunity_doc(opp, contact_name: str):
	opp.contact_person = contact_name
	row = frappe.db.get_value(
		"Contact",
		contact_name,
		["email_id", "mobile_no"],
		as_dict=True,
	)
	if row:
		opp.contact_email = row.email_id
		opp.contact_mobile = row.mobile_no


@frappe.whitelist()
def set_primary_contact(opportunity: str, contact: str):
	if not frappe.db.exists("Opportunity", opportunity):
		frappe.throw(_("Opportunity not found"), frappe.DoesNotExistError)
	if not frappe.db.exists("Contact", contact):
		frappe.throw(_("Contact not found"), frappe.DoesNotExistError)
	if not frappe.has_permission("Opportunity", "write", opportunity):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	linked = set(_linked_contact_names(opportunity))
	if contact not in linked:
		frappe.throw(_("Contact is not linked to this opportunity"), frappe.ValidationError)

	opp = frappe.get_doc("Opportunity", opportunity)
	_set_primary_on_opportunity_doc(opp, contact)
	opp.save()
	return contact
