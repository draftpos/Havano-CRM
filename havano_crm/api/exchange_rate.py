import frappe
import requests
from frappe import _

from havano_crm.compat import get_default_currency


@frappe.whitelist()
def get_exchange_rate(from_currency: str, to_currency: str, date: str | None = None):
	if not date:
		date = "latest"

	cache_date = frappe.utils.today() if date == "latest" else date
	cache_key = f"exchange_rate_{from_currency}_{to_currency}_{cache_date}"

	cached_rate = frappe.cache().get_value(cache_key)
	if cached_rate is not None:
		return cached_rate

	rate, api_used = _fetch_exchange_rate(from_currency, to_currency, date)

	if rate is not None:
		frappe.cache().set_value(cache_key, rate)
		return rate

	_raise_exchange_rate_error(from_currency, to_currency, date, api_used)


def _fetch_exchange_rate(from_currency: str, to_currency: str, date: str):
	rate = _fetch_from_frankfurter(from_currency, to_currency, date)
	if rate is not None:
		return rate, "frankfurter"
	rate = _fetch_from_fawaz_api(from_currency, to_currency, date)
	return rate, "fawazahmed-exchange-api"


def _fetch_from_frankfurter(from_currency: str, to_currency: str, date: str):
	try:
		res = requests.get(
			f"https://api.frankfurter.app/{date}?from={from_currency}&to={to_currency}", timeout=5
		)
		if res.ok:
			return res.json().get("rates", {}).get(to_currency)
	except Exception:
		pass
	return None


def _fetch_from_fawaz_api(from_currency: str, to_currency: str, date: str):
	from_lower = from_currency.lower()
	to_lower = to_currency.lower()
	date_str = "latest" if date == "latest" else date
	urls = [
		f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date_str}/v1/currencies/{from_lower}.json",
		f"https://{date_str}.currency-api.pages.dev/v1/currencies/{from_lower}.json",
	]
	for url in urls:
		try:
			res = requests.get(url, timeout=5)
			if res.ok:
				return res.json()[from_lower][to_lower]
		except Exception:
			continue
	return None


def _raise_exchange_rate_error(from_currency: str, to_currency: str, date: str, api_used: str):
	frappe.log_error(
		title="Exchange Rate Fetch Error",
		message=f"Failed to fetch exchange rate from {from_currency} to {to_currency} using {api_used} API.",
	)

	frappe.throw(
		_(
			"Failed to fetch exchange rate from {0} to {1} on {2}. Please check your internet connection or try again later."
		).format(from_currency, to_currency, date)
	)


@frappe.whitelist()
def get_default_currency_for_ui():
	return get_default_currency()
