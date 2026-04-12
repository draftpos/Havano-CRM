"""List and kanban defaults for standard DocTypes when the controller has no default_list_data."""


def get_standard_list_data(doctype: str) -> dict | None:
	return STANDARD_LIST_DATA.get(doctype)


def get_standard_kanban_settings(doctype: str) -> dict | None:
	return STANDARD_KANBAN.get(doctype)


STANDARD_LIST_DATA = {
	"Lead": {
		"columns": [
			{"label": "Name", "type": "Data", "key": "lead_name", "width": "12rem"},
			{"label": "Organization", "type": "Data", "key": "company_name", "width": "10rem"},
			{
				"label": "Deal size",
				"type": "Float",
				"key": "custom_deal_size_",
				"align": "right",
				"width": "9rem",
			},
			{"label": "Status", "type": "Select", "key": "status", "width": "8rem"},
			{"label": "Mobile No.", "type": "Data", "key": "mobile_no", "width": "11rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		],
		"rows": [
			"name",
			"lead_name",
			"company_name",
			"custom_deal_size_",
			"status",
			"mobile_no",
			"lead_owner",
			"first_name",
			"modified",
			"image",
		],
	},
	"Opportunity": {
		"columns": [
			{"label": "Customer", "type": "Data", "key": "customer_name", "width": "11rem"},
			{
				"label": "Amount",
				"type": "Currency",
				"key": "opportunity_amount",
				"align": "right",
				"width": "9rem",
			},
			{"label": "Status", "type": "Select", "key": "status", "width": "10rem"},
			{"label": "Email", "type": "Data", "key": "contact_email", "width": "12rem"},
			{"label": "Mobile No.", "type": "Data", "key": "contact_mobile", "width": "11rem"},
			{"label": "Assigned To", "type": "Text", "key": "_assign", "width": "10rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		],
		"rows": [
			"name",
			"title",
			"customer_name",
			"opportunity_amount",
			"status",
			"currency",
			"contact_email",
			"contact_mobile",
			"opportunity_owner",
			"modified",
			"_assign",
		],
	},
	"Customer": {
		"columns": [
			{"label": "Customer", "type": "Data", "key": "customer_name", "width": "16rem"},
			{"label": "Website", "type": "Data", "key": "website", "width": "14rem"},
			{
				"label": "Industry",
				"type": "Link",
				"key": "industry",
				"options": "Industry Type",
				"width": "14rem",
			},
			{
				"label": "Territory",
				"type": "Link",
				"key": "territory",
				"options": "Territory",
				"width": "12rem",
			},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		],
		"rows": [
			"name",
			"customer_name",
			"image",
			"website",
			"industry",
			"territory",
			"default_currency",
			"modified",
		],
	},
	"Contact": {
		"columns": [
			{"label": "Name", "type": "Data", "key": "full_name", "width": "17rem"},
			{"label": "Email", "type": "Data", "key": "email_id", "width": "12rem"},
			{"label": "Phone", "type": "Data", "key": "mobile_no", "width": "12rem"},
			{"label": "Organization", "type": "Data", "key": "company_name", "width": "12rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		],
		"rows": ["name", "full_name", "company_name", "email_id", "mobile_no", "modified", "image"],
	},
	"ToDo": {
		"columns": [
			{"label": "Description", "type": "Text", "key": "description", "width": "16rem"},
			{"label": "Status", "type": "Select", "key": "status", "width": "8rem"},
			{"label": "Priority", "type": "Select", "key": "priority", "width": "8rem"},
			{"label": "Due Date", "type": "Date", "key": "date", "width": "8rem"},
			{
				"label": "Allocated To",
				"type": "Link",
				"key": "allocated_to",
				"options": "User",
				"width": "10rem",
			},
			{"label": "Lead / Deal", "type": "Data", "key": "reference_name", "width": "10rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		],
		"rows": [
			"name",
			"description",
			"allocated_to",
			"date",
			"status",
			"priority",
			"reference_type",
			"reference_name",
			"modified",
		],
	},
	"Note": {
		"columns": [
			{"label": "Title", "type": "Data", "key": "title", "width": "18rem"},
			{"label": "Owner", "type": "Link", "key": "owner", "options": "User", "width": "12rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		],
		"rows": ["name", "title", "content", "owner", "modified"],
	},
	"Call Log": {
		"columns": [
			{"label": "Type", "type": "Select", "key": "type", "width": "9rem"},
			{"label": "Status", "type": "Select", "key": "status", "width": "9rem"},
			{"label": "Duration", "type": "Duration", "key": "duration", "width": "6rem"},
			{"label": "From", "type": "Data", "key": "from", "width": "9rem"},
			{"label": "To", "type": "Data", "key": "to", "width": "9rem"},
			{"label": "Customer", "type": "Link", "key": "customer", "options": "Customer", "width": "12rem"},
			{"label": "Start Time", "type": "Datetime", "key": "start_time", "width": "8rem"},
		],
		"rows": [
			"name",
			"id",
			"type",
			"status",
			"duration",
			"from",
			"to",
			"customer",
			"medium",
			"summary",
			"start_time",
			"recording_url",
		],
	},
}

STANDARD_KANBAN = {
	"Lead": {
		"column_field": "status",
		"title_field": "lead_name",
		"kanban_fields": '["company_name", "email_id", "mobile_no", "_assign", "modified"]',
	},
	"Opportunity": {
		"column_field": "status",
		"title_field": "title",
		"kanban_fields": '["customer_name", "contact_email", "contact_mobile", "_assign", "modified"]',
	},
	"ToDo": {
		"column_field": "status",
		"title_field": "description",
		"kanban_fields": '["priority", "date", "allocated_to"]',
	},
}
