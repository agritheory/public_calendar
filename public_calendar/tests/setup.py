# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

import datetime

import frappe
from erpnext.setup.utils import enable_all_roles_and_domains, set_defaults_for_tests
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

from public_calendar.tests.fixtures import employees


def before_test():
	frappe.clear_cache()
	today = frappe.utils.getdate()
	setup_complete(
		{
			"currency": "USD",
			"full_name": "Administrator",
			"company_name": "Winthrop Barn Builders, LLC",
			"timezone": "America/New_York",
			"company_abbr": "WBB",
			"domains": ["Distribution"],
			"country": "United States",
			"fy_start_date": today.replace(month=1, day=1).isoformat(),
			"fy_end_date": today.replace(month=12, day=31).isoformat(),
			"language": "en-US",
			"company_tagline": "Winthrop Barn Builders, LLC",
			"email": "support@agritheory.dev",
			"password": "admin",
			"chart_of_accounts": "Standard with Numbers",
			"bank_account": "Primary Checking",
		}
	)
	enable_all_roles_and_domains()
	set_defaults_for_tests()
	frappe.db.commit()
	create_test_data()


def create_test_data():
	settings = frappe._dict(
		{
			"day": datetime.date(
				int(frappe.defaults.get_defaults().get("fiscal_year", datetime.datetime.now().year)), 1, 1
			),
			"company": frappe.defaults.get_defaults().get("company"),
		}
	)
	create_employees(settings)
	dismiss_onboarding(settings)


def dismiss_onboarding(settings=None):
	for m in frappe.get_all("Module Onboarding"):
		frappe.db.set_value("Module Onboarding", m, "is_complete", 1)


def create_employees(settings, only_create=None):

	for employee in employees:
		if only_create and employee.get("employee_name") not in only_create:
			continue

		if frappe.db.exists("Employee", {"employee_name": employee.get("employee_name")}):
			continue

		if not frappe.db.exists("Designation", employee.get("designation")):
			desg = frappe.new_doc("Designation")
			desg.designation_name = employee.get("designation")
			desg.save()

		empl = frappe.new_doc("Employee")
		empl.update(employee)
		empl.reports_to = None
		if settings.company:
			empl.company = settings.company
		empl.save()

		user = frappe.new_doc("User")
		user.email = f"{empl.first_name[0].lower()}{empl.last_name.lower()}@cfc.co"
		user.first_name = empl.first_name
		user.last_name = empl.last_name
		user.send_welcome_email = 0
		user.enabled = 1
		user.language = settings.language
		user.time_zone = settings.time_zone
		for r in employee.get("roles", []):
			user.append("roles", {"role": r})

		user.save()
		empl.user_id = user.email
		if employee.get("reports_to"):
			empl.reports_to = frappe.get_value("Employee", {"employee_name": employee.get("reports_to")})
		empl.save()
