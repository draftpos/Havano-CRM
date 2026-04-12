"""ERPNext Call Log API for the Havano CRM UI (replaces Frappe CRM ``CRM Call Log`` helpers)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_url

from havano_crm.compat import parse_call_log


def _recording_src(raw: str | None) -> str | None:
	if not raw:
		return None
	raw = raw.strip()
	if raw.startswith("http://") or raw.startswith("https://"):
		return raw
	if raw.startswith("/"):
		return get_url(raw)
	return raw


@frappe.whitelist()
def get_call_log(name: str):
	if not frappe.db.exists("Call Log", name):
		frappe.throw(_("Call Log not found"), frappe.DoesNotExistError)
	if not frappe.has_permission("Call Log", "read", doc=name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("Call Log", name)
	call = doc.as_dict()
	call["recording_url_path"] = _recording_src(call.get("recording_url"))
	call = parse_call_log(call)

	tasks: list[dict] = []
	notes: list[dict] = []

	for row in call.get("links") or []:
		ld, ln = row.get("link_doctype"), row.get("link_name")
		if not ld or not ln:
			continue
		if ld == "ToDo" and frappe.db.exists("ToDo", ln):
			tasks.append(frappe.get_doc("ToDo", ln).as_dict())
		elif ld == "Note" and frappe.db.exists("Note", ln):
			notes.append(frappe.get_doc("Note", ln).as_dict())
		elif ld == "Lead":
			call["_lead"] = ln
		elif ld == "Opportunity":
			call["_deal"] = ln

	if not notes and call.get("summary"):
		notes.append({"title": "", "content": call.get("summary")})

	call["_tasks"] = tasks
	call["_notes"] = notes
	return call
