app_name = "havano_crm"
app_title = "Havano CRM"
app_publisher = "Havano"
app_description = "CRM UI on ERPNext standard CRM doctypes (Lead, Opportunity, Customer, …)."
app_email = "admin@havano.local"
app_license = "agpl-3.0"
app_icon_url = "/assets/havano_crm/images/logo.svg"
app_icon_title = "Havano CRM"
app_icon_route = "/havano_crm"

add_to_apps_screen = [
	{
		"name": "havano_crm",
		"logo": "/assets/havano_crm/images/logo.svg",
		"title": "Havano CRM",
		"route": "/havano_crm",
		"has_permission": "havano_crm.api.check_app_permission",
	}
]

get_site_info = "havano_crm.activation.get_site_info"

export_python_type_annotations = True
require_type_annotated_api_methods = True

website_route_rules = [
	{"from_route": "/havano-crm/<path:app_path>", "to_route": "havano_crm"},
]

setup_wizard_complete = None

before_install = "havano_crm.install.before_install"
after_install = "havano_crm.install.after_install"

before_uninstall = "havano_crm.uninstall.before_uninstall"

override_doctype_class = {
	"Contact": "havano_crm.overrides.contact.CustomContact",
	"Email Template": "havano_crm.overrides.email_template.CustomEmailTemplate",
}

doc_events = {
	"Contact": {
		"validate": ["havano_crm.api.contact.validate"],
	},
	"ToDo": {
		"after_insert": ["havano_crm.api.todo.after_insert"],
		"on_update": ["havano_crm.api.todo.on_update"],
	},
	"Communication": {
		"after_insert": ["havano_crm.utils.on_communication_insert"],
		"on_update": ["havano_crm.utils.on_communication_update"],
	},
	"Comment": {
		"after_insert": ["havano_crm.utils.on_comment_insert"],
		"on_update": ["havano_crm.api.comment.on_update"],
	},
	"WhatsApp Message": {
		"validate": ["havano_crm.api.whatsapp.validate"],
		"on_update": ["havano_crm.api.whatsapp.on_update"],
	},
	"User": {
		"before_validate": ["havano_crm.api.live_demo.validate_user"],
		"validate_reset_password": ["havano_crm.api.live_demo.validate_reset_password"],
	},
}

before_tests = None

ignore_links_on_delete = []

after_migrate = [
	"havano_crm.install.after_migrate",
	"havano_crm.api.whatsapp.add_roles",
]

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["dt", "=", "Lead"]],
	},
]

standard_dropdown_items = [
	{
		"name1": "app_selector",
		"label": "Apps",
		"type": "Route",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "settings",
		"label": "Settings",
		"type": "Route",
		"icon": "settings",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "about",
		"label": "About",
		"type": "Route",
		"icon": "info",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "separator",
		"label": "",
		"type": "Separator",
		"is_standard": 1,
	},
	{
		"name1": "logout",
		"label": "Log out",
		"type": "Route",
		"icon": "log-out",
		"route": "#",
		"is_standard": 1,
	},
]
