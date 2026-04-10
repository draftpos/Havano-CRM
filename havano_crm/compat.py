"""Shims for Frappe CRM DocTypes removed in Havano CRM (ERPNext-native doctypes only)."""

from __future__ import annotations

import frappe
from frappe import _


def notify_user(*_args, **_kwargs) -> None:
	"""CRM used in-app notifications; optional for Havano."""
	return None


def get_form_script(_doctype: str | None = None, _view: str | None = None) -> str:
	return ""


def _user_avatar_brief(user_id: str | None) -> dict:
	if not user_id:
		return {"label": "", "image": ""}
	row = frappe.db.get_value("User", user_id, ["full_name", "user_image"], as_dict=True)
	if not row:
		return {"label": user_id, "image": ""}
	return {"label": row.full_name or user_id, "image": row.user_image or ""}


def _phone_party(phone: str | None) -> dict:
	text = (phone or "").strip()
	return {"label": text or _("Unknown"), "image": ""}


def parse_call_log(call: dict) -> dict:
	"""Normalise ERPNext Call Log rows for the Frappe CRM-style activities UI."""
	call["show_recording"] = bool(call.get("recording_url") or call.get("recording_html"))
	if "_duration" not in call and call.get("duration") is not None:
		try:
			secs = float(call["duration"])
			m, s = divmod(int(secs), 60)
			h, m = divmod(m, 60)
			call["_duration"] = f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"
		except Exception:
			call["_duration"] = ""

	if call.get("summary") is not None and not call.get("note"):
		call["note"] = call["summary"]

	incoming = (call.get("type") or "") == "Incoming"
	user_brief = _user_avatar_brief(call.get("employee_user_id"))
	emp_name = ""
	if call.get("call_received_by"):
		emp_name = frappe.db.get_value("Employee", call["call_received_by"], "employee_name") or ""

	if incoming:
		call["_caller"] = _phone_party(call.get("from"))
		if user_brief["label"]:
			call["_receiver"] = user_brief
		elif emp_name:
			call["_receiver"] = {"label": emp_name, "image": ""}
		else:
			call["_receiver"] = _phone_party(call.get("to"))
	else:
		if user_brief["label"]:
			call["_caller"] = user_brief
		elif emp_name:
			call["_caller"] = {"label": emp_name, "image": ""}
		else:
			call["_caller"] = {"label": _("Agent"), "image": ""}
		call["_receiver"] = _phone_party(call.get("to"))

	# CallLogDetailModal iterates keys and runs getCallLogDetail('caller'|'receiver', …)
	call.setdefault("caller", call.get("employee_user_id") or call.get("from") or ".")
	call.setdefault("receiver", call.get("to") or call.get("from") or ".")

	return call


def get_default_currency() -> str:
	"""Prefer global defaults; fall back to USD."""
	try:
		return frappe.db.get_default("currency") or frappe.db.get_single_value("Global Defaults", "default_currency") or "USD"
	except Exception:
		return "USD"
