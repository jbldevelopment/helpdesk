import frappe
from frappe.utils.caching import redis_cache
from pypika import Criterion
from frappe.model import no_value_fields
from frappe.model.document import get_controller

from helpdesk.utils import check_permissions


@frappe.whitelist()
@redis_cache()
def get_filterable_fields(doctype):
	check_permissions(doctype, None)
	QBDocField = frappe.qb.DocType("DocField")
	QBCustomField = frappe.qb.DocType("Custom Field")
	allowed_fieldtypes = [
		"Check",
		"Data",
		"Float",
		"Int",
		"Link",
		"Long Text",
		"Select",
		"Small Text",
		"Text Editor",
		"Text",
	]

	from_doc_fields = (
		frappe.qb.from_(QBDocField)
		.select(
			QBDocField.fieldname,
			QBDocField.fieldtype,
			QBDocField.label,
			QBDocField.name,
			QBDocField.options,
		)
		.where(QBDocField.parent == doctype)
		.where(QBDocField.hidden == False)
		.where(Criterion.any([QBDocField.fieldtype == i for i in allowed_fieldtypes]))
		.run(as_dict=True)
	)

	from_custom_fields = (
		frappe.qb.from_(QBCustomField)
		.select(
			QBCustomField.fieldname,
			QBCustomField.fieldtype,
			QBCustomField.label,
			QBCustomField.name,
			QBCustomField.options,
		)
		.where(QBCustomField.dt == doctype)
		.where(QBCustomField.hidden == False)
		.where(
			Criterion.any([QBCustomField.fieldtype == i for i in allowed_fieldtypes])
		)
		.run(as_dict=True)
	)

	res = []
	res.extend(from_doc_fields)
	res.extend(from_custom_fields)
	res.extend(
		[{
			"fieldname": "_assign",
			"fieldtype": "Link",
			"label": "Assigned to",
			"name": "_assign",
			"options": "HD Agent",
		},
		{
			"fieldname": "name",
			"fieldtype": "Data",
			"label": "ID",
			"name": "name",
		}]
	)
	return res

@frappe.whitelist()
def get_list_data(
	doctype: str, 
	filters: dict={}, 
	order_by: str="modified desc", 
	page_length=20,
	columns=None,
	rows=None,
):
	is_default = True

	if columns or rows:
		is_default = False
		columns = frappe.parse_json(columns)
		rows = frappe.parse_json(rows)

	if not columns:
		columns = [
			{"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		]

	if not rows:
		rows = ["name"]

	# if frappe.db.exists("HD List View Settings", doctype):
	# 	list_view_settings = frappe.get_doc("CRM List View Settings", doctype)
	# 	columns = frappe.parse_json(list_view_settings.columns)
	# 	rows = frappe.parse_json(list_view_settings.rows)
	# 	is_default = False
	# else:
	list = get_controller(doctype)

	if is_default:
		if hasattr(list, "default_list_data"):
			columns = list.default_list_data().get("columns")
			rows = list.default_list_data().get("rows")

	# check if rows has all keys from columns if not add them
	for column in columns:
		if column.get("key") not in rows:
			rows.append(column.get("key"))

	rows.append("name") if "name" not in rows else rows
	data = frappe.get_list(
		doctype,
		fields=rows,
		filters=filters,
		order_by=order_by,
		page_length=page_length,
	) or []

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": field.label,
			"type": field.fieldtype,
			"value": field.fieldname,
			"options": field.options,
		}
		for field in fields
		if field.label and field.fieldname
	]

	std_fields = [
		{"label": "Name", "type": "Data", "value": "name"},
		{"label": "Created On", "type": "Datetime", "value": "creation"},
		{"label": "Last Modified", "type": "Datetime", "value": "modified"},
		{
			"label": "Modified By",
			"type": "Link",
			"value": "modified_by",
			"options": "User",
		},
		{"label": "Assigned To", "type": "Text", "value": "_assign"},
		{"label": "Owner", "type": "Link", "value": "owner", "options": "User"},
	]

	for field in std_fields:
		if field.get('value') not in rows:
			rows.append(field.get('value'))
		if field not in fields:
			fields.append(field)

	return {
		"data": data,
		"columns": columns,
		"rows": rows,
		"fields": fields,
		"total_count": len(frappe.get_list(doctype, filters=filters)),
		"row_count": len(data),
	}


@frappe.whitelist()
def get_tickets_list(
doctype: str, 
	filters: dict={}, 
	order_by: str="modified desc", 
	page_length=20,
	columns=None,
	rows=None,
):
	is_default = True
	manager_id = filters["owner"]

	if columns or rows:
		is_default = False
		columns = frappe.parse_json(columns)
		rows = frappe.parse_json(rows)

	if not columns:
		columns = [
			{"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		]

	if not rows:
		rows = ["name"]

	# if frappe.db.exists("HD List View Settings", doctype):
	# 	list_view_settings = frappe.get_doc("CRM List View Settings", doctype)
	# 	columns = frappe.parse_json(list_view_settings.columns)
	# 	rows = frappe.parse_json(list_view_settings.rows)
	# 	is_default = False
	# else:
	list = get_controller(doctype)

	if is_default:
		if hasattr(list, "default_list_data"):
			columns = list.default_list_data().get("columns")
			rows = list.default_list_data().get("rows")

	# check if rows has all keys from columns if not add them
	for column in columns:
		if column.get("key") not in rows:
			rows.append(column.get("key"))

	rows.append("name") if "name" not in rows else rows

	# employees_reporting_to_me = frappe.qb.from_('Employee').select('name').where((frappe.qb.Field('reports_to_email') == manager_id)).run(as_dict = True)

	# employee_ids = [emp['name'] for emp in employees_reporting_to_me]

	# tickets_query = frappe.qb.from_('HD Ticket') \
    # .select('*') \
    # .where(
    #     (frappe.qb.Field('raised_by').isin(employee_ids)) |  # Tickets created by employees reporting to you
    #     (frappe.qb.Field('name').isin(
    #         frappe.qb.from_('ToDo')
    #         .select('reference_name')
    #         .where(frappe.qb.Field('allocated_to') == manager_id)  # Tickets assigned to you in ToDo
    #     )) |
	# 	(frappe.qb.Field('raised_by') == manager_id)
    # )

	# ticket_count_query = frappe.qb.from_('HD Ticket') \
    # .where(
    #     (frappe.qb.Field('raised_by').isin(employee_ids)) |  # Tickets created by employees reporting to you
    #     (frappe.qb.Field('name').isin(
    #         frappe.qb.from_('ToDo')
    #         .select('reference_name')
    #         .where(frappe.qb.Field('allocated_to') == manager_id)  # Tickets assigned to you in ToDo
    #     )) |
	# 	(frappe.qb.Field('raised_by') == manager_id)
    # )

	employees_reporting_to_me_query = """
    SELECT name 
    FROM `tabEmployee` 
    WHERE reports_to_email = %s
	"""
	employees_reporting_to_me = frappe.db.sql(employees_reporting_to_me_query, manager_id, as_dict=True)

	# Extract the employee IDs from the result
	employee_ids = [emp['name'] for emp in employees_reporting_to_me]

	# Step 2: Prepare the main query to fetch tickets
	tickets_query = """
		SELECT * 
		FROM `tabHD Ticket`
		WHERE 
			raised_by IN ({}) 
			OR name IN (
				SELECT reference_name 
				FROM `tabToDo` 
				WHERE allocated_to = %s
			)
			OR raised_by = %s
	"""
	# Convert employee_ids to a comma-separated string
	employee_ids_str = ",".join([f"'{emp_id}'" for emp_id in employee_ids])

	# Execute the final query
	result = frappe.db.sql(tickets_query.format(employee_ids_str), (manager_id, manager_id), as_dict=True)

	data = result

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": field.label,
			"type": field.fieldtype,
			"value": field.fieldname,
			"options": field.options,
		}
		for field in fields
		if field.label and field.fieldname
	]

	std_fields = [
		{"label": "Name", "type": "Data", "value": "name"},
		{"label": "Created On", "type": "Datetime", "value": "creation"},
		{"label": "Last Modified", "type": "Datetime", "value": "modified"},
		{
			"label": "Modified By",
			"type": "Link",
			"value": "modified_by",
			"options": "User",
		},
		{"label": "Assigned To", "type": "Text", "value": "_assign"},
		{"label": "Owner", "type": "Link", "value": "owner", "options": "User"},
	]

	for field in std_fields:
		if field.get('value') not in rows:
			rows.append(field.get('value'))
		if field not in fields:
			fields.append(field)

	return {
		"data": data,
		"columns": columns,
		"rows": rows,
		"fields": fields,
		"total_count": 0,
		"row_count": len(data),
	}

@frappe.whitelist()
def sort_options(doctype: str):
	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": field.label,
			"value": field.fieldname,
		}
		for field in fields
		if field.label and field.fieldname
	]

	standard_fields = [
		{"label": "Name", "value": "name"},
		{"label": "Created On", "value": "creation"},
		{"label": "Last Modified", "value": "modified"},
		{"label": "Modified By", "value": "modified_by"},
		{"label": "Owner", "value": "owner"},
	]

	for field in standard_fields:
		fields.append(field)

	return fields