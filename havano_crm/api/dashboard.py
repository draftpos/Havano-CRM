import json

import frappe
from frappe import _
from frappe.query_builder import Case, DocType
from frappe.query_builder.functions import Avg, Count, Date, DateFormat, IfNull, Sum

from havano_crm.compat import get_default_currency
from havano_crm.utils import sales_user_only

DASHBOARD_LAYOUT_KEY = "havano_crm_manager_dashboard_layout"

# Same widget layout as Frappe CRM Manager Dashboard (visual parity).
DEFAULT_MANAGER_DASHBOARD_LAYOUT = (
	'[{"name":"total_leads","type":"number_chart","tooltip":"Total number of leads","layout":{"x":0,"y":0,"w":4,"h":3,"i":"total_leads"}},'
	'{"name":"ongoing_deals","type":"number_chart","tooltip":"Total number of ongoing deals","layout":{"x":8,"y":0,"w":4,"h":3,"i":"ongoing_deals"}},'
	'{"name":"won_deals","type":"number_chart","tooltip":"Total number of won deals","layout":{"x":12,"y":0,"w":4,"h":3,"i":"won_deals"}},'
	'{"name":"average_won_deal_value","type":"number_chart","tooltip":"Average value of won deals","layout":{"x":16,"y":0,"w":4,"h":3,"i":"average_won_deal_value"}},'
	'{"name":"average_deal_value","type":"number_chart","tooltip":"Average deal value of ongoing and won deals","layout":{"x":0,"y":2,"w":4,"h":3,"i":"average_deal_value"}},'
	'{"name":"average_time_to_close_a_lead","type":"number_chart","tooltip":"Average time taken to close a lead","layout":{"x":4,"y":0,"w":4,"h":3,"i":"average_time_to_close_a_lead"}},'
	'{"name":"average_time_to_close_a_deal","type":"number_chart","layout":{"x":4,"y":2,"w":4,"h":3,"i":"average_time_to_close_a_deal"}},'
	'{"name":"spacer","type":"spacer","layout":{"x":8,"y":2,"w":12,"h":3,"i":"spacer"}},'
	'{"name":"sales_trend","type":"axis_chart","layout":{"x":0,"y":4,"w":10,"h":9,"i":"sales_trend"}},'
	'{"name":"forecasted_revenue","type":"axis_chart","layout":{"x":10,"y":4,"w":10,"h":9,"i":"forecasted_revenue"}},'
	'{"name":"funnel_conversion","type":"axis_chart","layout":{"x":0,"y":11,"w":10,"h":9,"i":"funnel_conversion"}},'
	'{"name":"deals_by_stage_donut","type":"donut_chart","layout":{"x":10,"y":11,"w":10,"h":9,"i":"deals_by_stage_donut"}},'
	'{"name":"lost_deal_reasons","type":"axis_chart","layout":{"x":0,"y":32,"w":20,"h":9,"i":"lost_deal_reasons"}},'
	'{"name":"leads_by_source","type":"donut_chart","layout":{"x":0,"y":18,"w":10,"h":9,"i":"leads_by_source"}},'
	'{"name":"deals_by_source","type":"donut_chart","layout":{"x":10,"y":18,"w":10,"h":9,"i":"deals_by_source"}},'
	'{"name":"deals_by_territory","type":"axis_chart","layout":{"x":0,"y":25,"w":10,"h":9,"i":"deals_by_territory"}},'
	'{"name":"deals_by_salesperson","type":"axis_chart","layout":{"x":10,"y":25,"w":10,"h":9,"i":"deals_by_salesperson"}}]'
)


def _layout_list():
	raw = frappe.db.get_default(DASHBOARD_LAYOUT_KEY)
	if raw:
		try:
			return json.loads(raw)
		except Exception:
			pass
	return json.loads(DEFAULT_MANAGER_DASHBOARD_LAYOUT)


@frappe.whitelist()
def save_dashboard_layout(layout: str):
	frappe.only_for(["System Manager", "Sales Manager"], True)
	frappe.db.set_default(DASHBOARD_LAYOUT_KEY, layout)
	return {"ok": 1}


@frappe.whitelist()
def reset_to_default():
	frappe.only_for("System Manager", True)
	frappe.db.set_default(DASHBOARD_LAYOUT_KEY, None)
	return {"ok": 1}


@frappe.whitelist()
@sales_user_only
def get_dashboard(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	roles = frappe.get_roles(frappe.session.user)
	is_sales_manager = "Sales Manager" in roles or "System Manager" in roles
	is_sales_user = "Sales User" in roles and not is_sales_manager
	if is_sales_user:
		user = frappe.session.user

	layout = _layout_list()
	mod = frappe.get_module("havano_crm.api.dashboard")
	for item in layout:
		method_name = f"get_{item['name']}"
		if hasattr(mod, method_name):
			item["data"] = getattr(mod, method_name)(from_date, to_date, user)
		else:
			item["data"] = None
	return layout


@frappe.whitelist()
@sales_user_only
def get_chart(
	name: str, type: str, from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())
	roles = frappe.get_roles(frappe.session.user)
	is_sales_manager = "Sales Manager" in roles or "System Manager" in roles
	is_sales_user = "Sales User" in roles and not is_sales_manager
	if is_sales_user:
		user = frappe.session.user
	mod = frappe.get_module("havano_crm.api.dashboard")
	method_name = f"get_{name}"
	if hasattr(mod, method_name):
		return getattr(mod, method_name)(from_date, to_date, user)
	return {"error": _("Invalid chart name")}


def get_total_leads(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	diff = frappe.utils.date_diff(to_date, from_date) or 1
	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)
	Lead = DocType("Lead")
	cur = (Lead.creation >= from_date) & (Lead.creation < to_date_plus_one)
	prv = (Lead.creation >= prev_from_date) & (Lead.creation < from_date)
	if user:
		cur = cur & (Lead.lead_owner == user)
		prv = prv & (Lead.lead_owner == user)
	q = frappe.qb.from_(Lead).select(
		Count(Case().when(cur, Lead.name).else_(None)).as_("current_month_leads"),
		Count(Case().when(prv, Lead.name).else_(None)).as_("prev_month_leads"),
	)
	row = q.run(as_dict=True)[0]
	c, p = row.current_month_leads or 0, row.prev_month_leads or 0
	delta = ((c - p) / p * 100) if p else 0
	return {
		"title": _("Total leads"),
		"tooltip": _("Total number of leads"),
		"value": c,
		"delta": delta,
		"deltaSuffix": "%",
	}


def _ongoing_opp_cond(Opp, from_date, to_date_plus_one):
	return (
		(Opp.creation >= from_date)
		& (Opp.creation < to_date_plus_one)
		& Opp.status.notin(["Converted", "Lost", "Closed"])
	)


def get_ongoing_deals(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	diff = frappe.utils.date_diff(to_date, from_date) or 1
	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)
	Opp = DocType("Opportunity")
	cur = _ongoing_opp_cond(Opp, from_date, to_date_plus_one)
	prv = _ongoing_opp_cond(Opp, prev_from_date, from_date)
	if user:
		cur = cur & (Opp.opportunity_owner == user)
		prv = prv & (Opp.opportunity_owner == user)
	q = frappe.qb.from_(Opp).select(
		Count(Case().when(cur, Opp.name).else_(None)).as_("c"),
		Count(Case().when(prv, Opp.name).else_(None)).as_("p"),
	)
	row = q.run(as_dict=True)[0]
	c, p = row.c or 0, row.p or 0
	delta = ((c - p) / p * 100) if p else 0
	return {
		"title": _("Ongoing deals"),
		"tooltip": _("Opportunities not closed or lost"),
		"value": c,
		"delta": delta,
		"deltaSuffix": "%",
	}


def get_won_deals(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	diff = frappe.utils.date_diff(to_date, from_date) or 1
	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)
	Opp = DocType("Opportunity")
	cur = (Opp.creation >= from_date) & (Opp.creation < to_date_plus_one) & (Opp.status == "Converted")
	prv = (Opp.creation >= prev_from_date) & (Opp.creation < from_date) & (Opp.status == "Converted")
	if user:
		cur = cur & (Opp.opportunity_owner == user)
		prv = prv & (Opp.opportunity_owner == user)
	q = frappe.qb.from_(Opp).select(
		Count(Case().when(cur, Opp.name).else_(None)).as_("c"),
		Count(Case().when(prv, Opp.name).else_(None)).as_("p"),
	)
	row = q.run(as_dict=True)[0]
	c, p = row.c or 0, row.p or 0
	delta = ((c - p) / p * 100) if p else 0
	return {
		"title": _("Won deals"),
		"tooltip": _("Opportunities marked Converted"),
		"value": c,
		"delta": delta,
		"deltaSuffix": "%",
	}


def get_average_won_deal_value(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	to_date_plus_one = frappe.utils.add_days(to_date, 1)
	Opp = DocType("Opportunity")
	cond = (Opp.creation >= from_date) & (Opp.creation < to_date_plus_one) & (Opp.status == "Converted")
	if user:
		cond = cond & (Opp.opportunity_owner == user)
	row = (
		frappe.qb.from_(Opp)
		.select(Avg(IfNull(Opp.opportunity_amount, 0)).as_("avg"))
		.where(cond)
		.run(as_dict=True)
	)[0]
	val = float(row.avg or 0)
	return {
		"title": _("Average won deal value"),
		"tooltip": _("Mean opportunity amount for converted deals"),
		"value": round(val, 2),
		"delta": 0,
		"deltaSuffix": "%",
	}


def get_average_deal_value(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	to_date_plus_one = frappe.utils.add_days(to_date, 1)
	Opp = DocType("Opportunity")
	cond = (
		(Opp.creation >= from_date)
		& (Opp.creation < to_date_plus_one)
		& Opp.status.notin(["Lost", "Closed"])
	)
	if user:
		cond = cond & (Opp.opportunity_owner == user)
	row = (
		frappe.qb.from_(Opp)
		.select(Avg(IfNull(Opp.opportunity_amount, 0)).as_("avg"))
		.where(cond)
		.run(as_dict=True)
	)[0]
	val = float(row.avg or 0)
	return {
		"title": _("Average deal value"),
		"tooltip": _("Mean opportunity amount (open + won)"),
		"value": round(val, 2),
		"delta": 0,
		"deltaSuffix": "%",
	}


def get_average_time_to_close_a_lead(
	from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	return {
		"title": _("Avg. time to close lead"),
		"tooltip": _("Not available without CRM status history"),
		"value": 0,
		"delta": 0,
		"deltaSuffix": "%",
	}


def get_average_time_to_close_a_deal(
	from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	return {
		"title": _("Avg. time to close deal"),
		"tooltip": _("Not available without CRM status history"),
		"value": 0,
		"delta": 0,
		"deltaSuffix": "%",
	}


def get_sales_trend(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	Lead = DocType("Lead")
	Opp = DocType("Opportunity")
	leads_q = frappe.qb.from_(Lead).select(
		Date(Lead.creation).as_("date"),
		Count("*").as_("leads"),
		frappe.qb.terms.ValueWrapper(0).as_("deals"),
		frappe.qb.terms.ValueWrapper(0).as_("won_deals"),
	).where(Date(Lead.creation).between(from_date, to_date))
	if user:
		leads_q = leads_q.where(Lead.lead_owner == user)
	leads_q = leads_q.groupby(Date(Lead.creation))

	deals_q = frappe.qb.from_(Opp).select(
		Date(Opp.creation).as_("date"),
		frappe.qb.terms.ValueWrapper(0).as_("leads"),
		Count("*").as_("deals"),
		Sum(Case().when(Opp.status == "Converted", 1).else_(0)).as_("won_deals"),
	).where(Date(Opp.creation).between(from_date, to_date))
	if user:
		deals_q = deals_q.where(Opp.opportunity_owner == user)
	deals_q = deals_q.groupby(Date(Opp.creation))

	union_query = leads_q.union_all(deals_q)
	daily = (
		frappe.qb.from_(union_query)
		.select(
			DateFormat(union_query.date, "%Y-%m-%d").as_("date"),
			Sum(union_query.leads).as_("leads"),
			Sum(union_query.deals).as_("deals"),
			Sum(union_query.won_deals).as_("won_deals"),
		)
		.groupby(union_query.date)
		.orderby(union_query.date)
	)
	result = daily.run(as_dict=True)
	sales_trend = [
		{
			"date": frappe.utils.get_datetime(row.date).strftime("%Y-%m-%d"),
			"leads": row.leads or 0,
			"deals": row.deals or 0,
			"won_deals": row.won_deals or 0,
		}
		for row in result
	]
	return {
		"data": sales_trend,
		"title": _("Sales trend"),
		"subtitle": _("Daily performance of leads, opportunities, and wins"),
		"xAxis": {"title": _("Date"), "key": "date", "type": "time", "timeGrain": "day"},
		"yAxis": {"title": _("Count")},
		"series": [
			{"name": "leads", "type": "line", "showDataPoints": True},
			{"name": "deals", "type": "line", "showDataPoints": True},
			{"name": "won_deals", "type": "line", "showDataPoints": True},
		],
	}


def get_forecasted_revenue(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	twelve_months_ago = frappe.utils.add_months(frappe.utils.nowdate(), -12)
	Opp = DocType("Opportunity")
	forecasted = IfNull(Opp.opportunity_amount, 0) * IfNull(Opp.probability, 0) / 100
	actual = Case().when(Opp.status == "Converted", IfNull(Opp.opportunity_amount, 0)).else_(0)
	q = (
		frappe.qb.from_(Opp)
		.select(
			DateFormat(Opp.expected_closing, "%Y-%m").as_("month"),
			Sum(forecasted).as_("forecasted"),
			Sum(actual).as_("actual"),
		)
		.where(Opp.expected_closing >= twelve_months_ago)
		.groupby(DateFormat(Opp.expected_closing, "%Y-%m"))
		.orderby(DateFormat(Opp.expected_closing, "%Y-%m"))
	)
	if user:
		q = q.where(Opp.opportunity_owner == user)
	result = q.run(as_dict=True)
	for row in result:
		row["month"] = frappe.utils.get_datetime(row["month"] + "-01").strftime("%Y-%m-01")
		row["forecasted"] = row["forecasted"] or ""
		row["actual"] = row["actual"] or ""
	return {
		"data": result or [],
		"title": _("Forecasted revenue"),
		"subtitle": _("From Opportunity amount × probability"),
		"xAxis": {"title": _("Month"), "key": "month", "type": "time", "timeGrain": "month"},
		"yAxis": {"title": _("Revenue") + f" ({get_base_currency_symbol()})"},
		"series": [
			{"name": "forecasted", "type": "line", "showDataPoints": True},
			{"name": "actual", "type": "line", "showDataPoints": True},
		],
	}


def get_funnel_conversion(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	return {
		"data": [],
		"title": _("Funnel conversion"),
		"subtitle": _("Configure custom stages in ERPNext to extend this chart"),
		"xAxis": {"title": _("Stage"), "key": "stage", "type": "category"},
		"yAxis": {"title": _("Count")},
		"series": [{"name": "count", "type": "bar"}],
	}


def get_deals_by_stage_donut(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	Opp = DocType("Opportunity")
	q = (
		frappe.qb.from_(Opp)
		.select(Opp.sales_stage.as_("stage"), Count("*").as_("count"))
		.where(Date(Opp.creation).between(from_date, to_date))
		.groupby(Opp.sales_stage)
		.orderby(Count("*"), order=frappe.qb.desc)
	)
	if user:
		q = q.where(Opp.opportunity_owner == user)
	result = q.run(as_dict=True)
	return {
		"data": result or [],
		"title": _("Deals by stage"),
		"subtitle": _("Opportunity sales_stage distribution"),
		"categoryColumn": "stage",
		"valueColumn": "count",
	}


def get_lost_deal_reasons(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	return {
		"data": [],
		"title": _("Lost deal reasons"),
		"subtitle": _("Use Opportunity lost reason fields in ERPNext for detail"),
		"xAxis": {"title": _("Reason"), "key": "reason", "type": "category"},
		"yAxis": {"title": _("Count")},
		"series": [{"name": "count", "type": "bar"}],
	}


def get_leads_by_source(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	Lead = DocType("Lead")
	q = (
		frappe.qb.from_(Lead)
		.select(Lead.source.as_("source"), Count("*").as_("count"))
		.where(Date(Lead.creation).between(from_date, to_date))
		.groupby(Lead.source)
		.orderby(Count("*"), order=frappe.qb.desc)
	)
	if user:
		q = q.where(Lead.lead_owner == user)
	result = q.run(as_dict=True)
	return {
		"data": result or [],
		"title": _("Leads by source"),
		"subtitle": _("Lead source field"),
		"categoryColumn": "source",
		"valueColumn": "count",
	}


def get_deals_by_source(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	Opp = DocType("Opportunity")
	q = (
		frappe.qb.from_(Opp)
		.select(Opp.source.as_("source"), Count("*").as_("count"))
		.where(Date(Opp.creation).between(from_date, to_date))
		.groupby(Opp.source)
		.orderby(Count("*"), order=frappe.qb.desc)
	)
	if user:
		q = q.where(Opp.opportunity_owner == user)
	result = q.run(as_dict=True)
	return {
		"data": result or [],
		"title": _("Deals by source"),
		"subtitle": _("Opportunity source"),
		"categoryColumn": "source",
		"valueColumn": "count",
	}


def get_deals_by_territory(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	Opp = DocType("Opportunity")
	q = (
		frappe.qb.from_(Opp)
		.select(Opp.territory.as_("territory"), Count("*").as_("count"))
		.where(Date(Opp.creation).between(from_date, to_date))
		.groupby(Opp.territory)
		.orderby(Count("*"), order=frappe.qb.desc)
	)
	if user:
		q = q.where(Opp.opportunity_owner == user)
	result = q.run(as_dict=True)
	return {
		"data": result or [],
		"title": _("Deals by territory"),
		"subtitle": _("Opportunity territory"),
		"xAxis": {"title": _("Territory"), "key": "territory", "type": "category"},
		"yAxis": {"title": _("Count")},
		"series": [{"name": "count", "type": "bar"}],
	}


def get_deals_by_salesperson(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	Opp = DocType("Opportunity")
	q = (
		frappe.qb.from_(Opp)
		.select(Opp.opportunity_owner.as_("owner"), Count("*").as_("deals"), Sum(IfNull(Opp.opportunity_amount, 0)).as_("value"))
		.where(Date(Opp.creation).between(from_date, to_date))
		.groupby(Opp.opportunity_owner)
		.orderby(Count("*"), order=frappe.qb.desc)
	)
	if user:
		q = q.where(Opp.opportunity_owner == user)
	result = q.run(as_dict=True)
	return {
		"data": result or [],
		"title": _("Deals by salesperson"),
		"subtitle": _("Opportunity owner"),
		"xAxis": {"title": _("Owner"), "key": "owner", "type": "category"},
		"yAxis": {"title": _("Count")},
		"y2Axis": {"title": _("Deal value") + f" ({get_base_currency_symbol()})"},
		"series": [
			{"name": "deals", "type": "bar"},
			{"name": "value", "type": "line", "showDataPoints": True, "axis": "y2"},
		],
	}


def get_base_currency_symbol():
	base_currency = get_default_currency()
	return frappe.db.get_value("Currency", base_currency, "symbol") or base_currency
