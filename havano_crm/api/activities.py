import json

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.desk.form.load import get_docinfo
from frappe.translate import get_translated_doctypes

from havano_crm.compat import parse_call_log


@frappe.whitelist()
def get_activities(name: str):
	if frappe.db.exists("Opportunity", name):
		return get_deal_activities(name)
	elif frappe.db.exists("Lead", name):
		return get_lead_activities(name)
	else:
		frappe.throw(_("Document not found"), frappe.DoesNotExistError)


def get_linked_events(reference_doctype: str, reference_name: str, limit: int = 40) -> list:
	"""Calendar events linked via Event Participants to a Lead or Opportunity."""
	if not reference_doctype or not reference_name:
		return []
	if not frappe.db.exists("DocType", "Event"):
		return []
	if not frappe.db.exists(reference_doctype, reference_name):
		return []
	if not frappe.has_permission("Event", "read"):
		return []
	limit = int(limit) if limit else 40
	if limit < 1:
		limit = 1
	if limit > 100:
		limit = 100
	parents = frappe.get_all(
		"Event Participants",
		filters={
			"reference_doctype": reference_doctype,
			"reference_docname": reference_name,
			"parenttype": "Event",
		},
		pluck="parent",
	)
	parents = list(dict.fromkeys(parents))
	if not parents:
		return []
	rows = frappe.get_all(
		"Event",
		filters={"name": ("in", parents)},
		fields=[
			"name",
			"subject",
			"starts_on",
			"ends_on",
			"event_type",
			"owner",
			"creation",
			"modified",
		],
	) or []
	rows.sort(
		key=lambda e: (e.get("starts_on") or e.get("creation") or ""),
		reverse=True,
	)
	return rows[:limit]


def get_deal_activities(name: str):
	if not frappe.has_permission("Opportunity", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "Opportunity", name)
	docinfo = frappe.response["docinfo"]
	deal_meta = frappe.get_meta("Opportunity")
	deal_fields = {
		field.fieldname: {"label": field.label, "options": field.options} for field in deal_meta.fields
	}
	avoid_fields = [
		"party_name",
		"opportunity_from",
		"response_by",
		"sla_creation",
		"sla",
		"first_response_time",
		"first_responded_on",
	]

	doc = frappe.db.get_values("Opportunity", name, ["creation", "owner", "opportunity_from", "party_name"])[0]
	lead = doc[3] if doc[2] == "Lead" else None

	activities = []
	calls = []
	notes = []
	tasks = []
	attachments = []
	creation_text = _("created this deal")

	lead_events: list = []
	if lead:
		activities, calls, notes, tasks, attachments, lead_events = get_lead_activities(lead)
		creation_text = _("converted the lead to this deal")

	activities.append(
		{
			"activity_type": "creation",
			"creation": doc[0],
			"owner": doc[1],
			"data": creation_text,
			"is_lead": False,
		}
	)

	docinfo.versions.reverse()

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		if change := data.get("changed")[0]:
			field = deal_fields.get(change[0], None)

			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue

			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None

			activity_type = "changed"
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}

			if not change[1] and change[2]:
				activity_type = "added"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[2],
				}
			elif change[1] and not change[2]:
				activity_type = "removed"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[1],
				}

			if data.get("value") and field_option and is_translatable(field_option):
				data["value"] = _(data["value"])

				if data.get("old_value"):
					data["old_value"] = _(data["old_value"])

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
			"is_lead": False,
			"options": field_option,
		}
		activities.append(activity)

	for comment in docinfo.comments:
		activity = {
			"name": comment.name,
			"activity_type": "comment",
			"creation": comment.creation,
			"owner": comment.owner,
			"content": comment.content,
			"attachments": get_attachments("Comment", comment.name),
			"is_lead": False,
		}
		activities.append(activity)

	for communication in docinfo.communications + docinfo.automated_messages:
		activity = {
			"activity_type": "communication",
			"communication_type": communication.communication_type,
			"communication_date": communication.communication_date or communication.creation,
			"creation": communication.creation,
			"data": {
				"subject": communication.subject,
				"content": communication.content,
				"sender_full_name": communication.sender_full_name,
				"sender": communication.sender,
				"recipients": communication.recipients,
				"cc": communication.cc,
				"bcc": communication.bcc,
				"attachments": get_attachments("Communication", communication.name),
				"read_by_recipient": communication.read_by_recipient,
				"delivery_status": communication.delivery_status,
			},
			"is_lead": False,
		}
		activities.append(activity)

	for attachment_log in docinfo.attachment_logs:
		activity = {
			"name": attachment_log.name,
			"activity_type": "attachment_log",
			"creation": attachment_log.creation,
			"owner": attachment_log.owner,
			"data": parse_attachment_log(attachment_log.content, attachment_log.comment_type),
			"is_lead": False,
		}
		activities.append(activity)

	_linked = get_linked_calls(name)
	calls = calls + _linked.get("calls", [])
	notes = notes + get_linked_notes(name, "Opportunity") + _linked.get("notes", [])
	tasks = tasks + get_linked_tasks(name, "Opportunity") + _linked.get("tasks", [])
	attachments = attachments + get_attachments("Opportunity", name)

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)

	opp_events = get_linked_events("Opportunity", name)
	by_name: dict = {}
	for ev in opp_events + lead_events:
		by_name.setdefault(ev["name"], ev)
	events = sorted(
		by_name.values(),
		key=lambda e: (e.get("starts_on") or e.get("creation") or ""),
		reverse=True,
	)

	return activities, calls, notes, tasks, attachments, events


def get_lead_activities(name: str):
	if not frappe.has_permission("Lead", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "Lead", name)
	docinfo = frappe.response["docinfo"]
	lead_meta = frappe.get_meta("Lead")
	lead_fields = {
		field.fieldname: {"label": field.label, "options": field.options} for field in lead_meta.fields
	}
	avoid_fields = [
		"converted",
		"response_by",
		"sla_creation",
		"sla",
		"first_response_time",
		"first_responded_on",
	]

	doc = frappe.db.get_values("Lead", name, ["creation", "owner"])[0]
	activities = [
		{
			"activity_type": "creation",
			"creation": doc[0],
			"owner": doc[1],
			"data": _("created this lead"),
			"is_lead": True,
		}
	]

	docinfo.versions.reverse()

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		if change := data.get("changed")[0]:
			field = lead_fields.get(change[0], None)

			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue

			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None

			activity_type = "changed"
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}

			if not change[1] and change[2]:
				activity_type = "added"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[2],
				}
			elif change[1] and not change[2]:
				activity_type = "removed"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[1],
				}

			if data.get("value") and field_option and is_translatable(field_option):
				data["value"] = _(data["value"])

				if data.get("old_value"):
					data["old_value"] = _(data["old_value"])

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
			"is_lead": True,
			"options": field_option,
		}
		activities.append(activity)

	for comment in docinfo.comments:
		activity = {
			"name": comment.name,
			"activity_type": "comment",
			"creation": comment.creation,
			"owner": comment.owner,
			"content": comment.content,
			"attachments": get_attachments("Comment", comment.name),
			"is_lead": True,
		}
		activities.append(activity)

	for communication in docinfo.communications + docinfo.automated_messages:
		activity = {
			"activity_type": "communication",
			"communication_type": communication.communication_type,
			"communication_date": communication.communication_date or communication.creation,
			"creation": communication.creation,
			"data": {
				"subject": communication.subject,
				"content": communication.content,
				"sender_full_name": communication.sender_full_name,
				"sender": communication.sender,
				"recipients": communication.recipients,
				"cc": communication.cc,
				"bcc": communication.bcc,
				"attachments": get_attachments("Communication", communication.name),
				"read_by_recipient": communication.read_by_recipient,
				"delivery_status": communication.delivery_status,
			},
			"is_lead": True,
		}
		activities.append(activity)

	for attachment_log in docinfo.attachment_logs:
		activity = {
			"name": attachment_log.name,
			"activity_type": "attachment_log",
			"creation": attachment_log.creation,
			"owner": attachment_log.owner,
			"data": parse_attachment_log(attachment_log.content, attachment_log.comment_type),
			"is_lead": True,
		}
		activities.append(activity)

	_linked = get_linked_calls(name)
	calls = _linked.get("calls", [])
	notes = get_linked_notes(name, "Lead") + _linked.get("notes", [])
	tasks = get_linked_tasks(name, "Lead") + _linked.get("tasks", [])
	attachments = get_attachments("Lead", name)

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)

	events = get_linked_events("Lead", name)

	return activities, calls, notes, tasks, attachments, events


def get_attachments(doctype: str, name: str):
	return (
		frappe.db.get_all(
			"File",
			filters={"attached_to_doctype": doctype, "attached_to_name": name},
			fields=[
				"name",
				"file_name",
				"file_type",
				"file_url",
				"file_size",
				"is_private",
				"modified",
				"creation",
				"owner",
			],
		)
		or []
	)


def handle_multiple_versions(versions: list):
	activities = []
	grouped_versions = []
	old_version = None
	for version in versions:
		is_version = version["activity_type"] in ["changed", "added", "removed"]
		if not is_version:
			activities.append(version)
		if not old_version:
			old_version = version
			if is_version:
				grouped_versions.append(version)
			continue
		if is_version and old_version.get("owner") and version["owner"] == old_version["owner"]:
			grouped_versions.append(version)
		else:
			if grouped_versions:
				activities.append(parse_grouped_versions(grouped_versions))
			grouped_versions = []
			if is_version:
				grouped_versions.append(version)
		old_version = version
		if version == versions[-1] and grouped_versions:
			activities.append(parse_grouped_versions(grouped_versions))

	return activities


def parse_grouped_versions(versions: list):
	version = versions[0]
	if len(versions) == 1:
		return version
	other_versions = versions[1:]
	version["other_versions"] = other_versions
	return version


def get_linked_calls(name: str):
	"""Load ERPNext Call Log rows linked to ``name`` via the Call Log ``links`` child (Dynamic Link)."""
	linked_call_names = frappe.get_all(
		"Dynamic Link",
		filters={"parenttype": "Call Log", "link_name": name},
		pluck="parent",
	)
	linked_call_names = list(dict.fromkeys(linked_call_names))

	notes = []
	tasks = []
	calls = []

	if linked_call_names:
		dl_children = frappe.get_all(
			"Dynamic Link",
			filters={"parenttype": "Call Log", "parent": ("in", linked_call_names)},
			fields=["link_doctype", "link_name"],
		)
		for row in dl_children:
			if row.link_doctype == "Note":
				notes.append(row.link_name)
			elif row.link_doctype == "ToDo":
				tasks.append(row.link_name)

		notes = list(dict.fromkeys(notes))
		tasks = list(dict.fromkeys(tasks))

		calls = frappe.db.get_all(
			"Call Log",
			filters={"name": ("in", linked_call_names)},
			fields=[
				"name",
				"id",
				"from",
				"to",
				"duration",
				"start_time",
				"end_time",
				"status",
				"type",
				"recording_url",
				"creation",
				"summary",
				"employee_user_id",
				"call_received_by",
				"customer",
				"medium",
			],
		)

	if notes:
		notes = frappe.db.get_all(
			"Note",
			filters={"name": ("in", notes)},
			fields=["name", "title", "content", "owner", "modified"],
		)

	if tasks:
		tasks = frappe.db.get_all(
			"ToDo",
			filters={"name": ("in", tasks)},
			fields=[
				"name",
				"description",
				"allocated_to",
				"date",
				"priority",
				"status",
				"modified",
			],
		)

	calls = [parse_call_log(call) for call in calls] if calls else []

	return {"calls": calls, "notes": notes, "tasks": tasks}


def get_linked_notes(name: str, reference_doctype: str = "Lead"):
	meta = frappe.get_meta("Note")
	if not (meta.has_field("reference_doctype") and meta.has_field("reference_docname")):
		return []
	notes = frappe.db.get_all(
		"Note",
		filters={"reference_doctype": reference_doctype, "reference_docname": name},
		fields=["name", "title", "content", "owner", "modified", "creation"],
	)
	return notes or []


def get_linked_tasks(name: str, reference_doctype: str = "Lead"):
	tasks = frappe.db.get_all(
		"ToDo",
		filters={"reference_type": reference_doctype, "reference_name": name},
		fields=[
			"name",
			"description",
			"allocated_to",
			"date",
			"priority",
			"status",
			"modified",
			"creation",
		],
	)
	return tasks or []


@frappe.whitelist()
def get_open_todos_for_reference(reference_doctype: str, reference_name: str):
	"""Open ToDos linked to a Lead or Deal (for list modal)."""
	if not reference_doctype or not reference_name:
		return []
	if reference_doctype not in ("Lead", "Opportunity"):
		frappe.throw(_("Unsupported document type"))
	if not frappe.db.exists(reference_doctype, reference_name):
		frappe.throw(_("Document not found"), frappe.DoesNotExistError)
	frappe.has_permission(reference_doctype, "read", reference_name, throw=True)
	return frappe.get_all(
		"ToDo",
		filters={
			"reference_type": reference_doctype,
			"reference_name": reference_name,
			"status": "Open",
		},
		fields=[
			"name",
			"description",
			"allocated_to",
			"date",
			"priority",
			"status",
			"modified",
			"creation",
		],
		order_by="date asc, modified desc",
	) or []


def parse_attachment_log(html: str, type: str):
	soup = BeautifulSoup(html, "html.parser")
	a_tag = soup.find("a")
	type = "added" if type == "Attachment" else "removed"
	if not a_tag:
		return {
			"type": type,
			"file_name": html.replace("Removed ", ""),
			"file_url": "",
			"is_private": False,
		}

	is_private = False
	if "private/files" in a_tag["href"]:
		is_private = True

	return {
		"type": type,
		"file_name": a_tag.text,
		"file_url": a_tag["href"],
		"is_private": is_private,
	}


def is_translatable(doctype: str) -> bool:
	return doctype in get_translated_doctypes()
