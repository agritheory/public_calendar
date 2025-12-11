# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document


class PublicCalendar(Document):
	def validate(self):
		self.validate_working_hours()

	def validate_working_hours(self):
		if not self.working_hours:
			return

		try:
			hours = json.loads(self.working_hours)
		except json.JSONDecodeError:
			frappe.throw(frappe._("Invalid working hours format"))

		for day, blocks in hours.items():
			if not blocks:
				continue

			sorted_blocks = sorted(blocks, key=lambda b: b.get("start", ""))

			for i in range(len(sorted_blocks) - 1):
				current = sorted_blocks[i]
				next_block = sorted_blocks[i + 1]

				current_end = current.get("end", "")
				next_start = next_block.get("start", "")

				if current_end > next_start:
					frappe.throw(
						frappe._("{0}: Time blocks overlap ({1}-{2} and {3}-{4})").format(
							day.title(),
							current.get("start"),
							current_end,
							next_start,
							next_block.get("end"),
						)
					)
