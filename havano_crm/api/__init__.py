import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.core.api.file import get_max_file_size
from frappe.translate import get_all_translations
from frappe.utils import cstr, split_emails, validate_email_address

from havano_crm.utils import is_frappe_version


@frappe.whitelist(allow_guest=True)
def get_translations():
	if frappe.session.user != "Guest":
		language = frappe.db.get_value("User", frappe.session.user, "language")
	else:
		language = frappe.db.get_single_value("System Settings", "language")

	return get_all_translations(language)


@frappe.whitelist()
def get_user_signature():
	user = frappe.session.user
	user_email_signature = (
		frappe.db.get_value(
			"User",
			user,
			"email_signature",
		)
		if user
		else None
	)

	signature = user_email_signature or frappe.db.get_value(
		"Email Account",
		{"default_outgoing": 1, "add_signature": 1},
		"signature",
	)

	if not signature:
		return

	soup = BeautifulSoup(signature, "html.parser")
	html_signature = soup.find("div", {"class": "ql-editor read-mode"})
	_signature = None
	if html_signature:
		_signature = html_signature.renderContents()
	content = ""
	if cstr(_signature) or signature:
		content = f'<br><p class="signature">{signature}</p>'
	return content


def check_app_permission():
	if frappe.session.user == "Administrator":
		return True

	allowed_modules = []

	if is_frappe_version("15"):
		allowed_modules = frappe.config.get_modules_from_all_apps_for_user()
	elif is_frappe_version("16", above=True):
		from frappe.utils.modules import get_modules_from_all_apps_for_user

		allowed_modules = get_modules_from_all_apps_for_user()

	allowed_modules = [x["module_name"] for x in allowed_modules]
	if not set(allowed_modules).intersection({"CRM", "Havano CRM", "Havano", "Selling"}):
		return False

	roles = frappe.get_roles()
	if any(role in ["System Manager", "Sales User", "Sales Manager"] for role in roles):
		return True

	return False


@frappe.whitelist(allow_guest=True)
def accept_invitation(key: str | None = None):
	frappe.throw(_("User invitations are managed from Desk (User / User Invitation)."))


@frappe.whitelist()
def invite_by_email(emails: str, role: str):
	frappe.only_for(["Sales Manager", "System Manager"], True)

	user_roles = frappe.get_roles(frappe.session.user)

	if role == "System Manager" and "System Manager" not in user_roles:
		frappe.throw(_("You are not allowed to invite System Managers"), frappe.PermissionError)

	if role == "Sales Manager" and "System Manager" not in user_roles:
		frappe.throw(_("You are not allowed to invite Sales Managers"), frappe.PermissionError)

	if role not in ["System Manager", "Sales Manager", "Sales User"]:
		frappe.throw(_("Cannot invite for this role"), frappe.PermissionError)

	frappe.throw(_("Invite users from Desk → User (Havano CRM does not use CRM Invitation)."))


@frappe.whitelist()
def get_file_uploader_defaults(doctype: str):
	max_number_of_files = None
	make_attachments_public = False
	if doctype:
		meta = frappe.get_meta(doctype)
		max_number_of_files = meta.get("max_attachments")
		make_attachments_public = meta.get("make_attachments_public")

	return {
		"allowed_file_types": frappe.get_system_settings("allowed_file_extensions"),
		"max_file_size": get_max_file_size(),
		"max_number_of_files": max_number_of_files,
		"make_attachments_public": bool(make_attachments_public),
	}
