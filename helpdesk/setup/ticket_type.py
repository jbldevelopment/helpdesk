import frappe
from helpdesk.consts import DEFAULT_TICKET_TYPE

DT = "HD Ticket Type"
TICKET_TYPES = ["Question", "Bug", "Incident"]
ENABLED_TICKET_TYPES = {
	"Funds": [
		"Add Funds", "Withdrawal Funds", 
	],
	"Email Issue" : [
		"Contract Mail" , "Mail password reset", "Margin Statement Mail"
	],
	"Employee" : ["Employee creation" , "CTCL related" , "Other Modifications" , "Salary/Incentive related" , "Location related"],
	"Investment Products" : [ "Mutual Fund" , "Wealth Basket / PMS" , "IPO" , "Unlisted Shares" , "SLBM" , "Insurance" , "Corporate Bonds, NCD, SGB"],
	"Monitoring" : ["Server" , "Services" , "Websites"],
	"My Account" : [
"Account Opening",
"Account Modification",
"Account Closure",
"Brokerage related",
"Reactivation",
"Transfer of Securities (DIS)",
"Transfer of Securities (DRF)",
"Branch related issue",
"Ledger related",
"Deposite related",
"Payout related",
"Service Related issue",
],
"Partner Related" : [
"Brokerage sharing related",
"My registration related",
"Brokerage payout related",
"Tech Excel Support",
"Space related",
"Service Related issue",
],
"Platform and Tools" : ["Jainam Web Trading",
"Jainam App Trading",
"Trading Software EXE based",
"Back Office App",
"Jainam Portal Reports & back office",
"API",
"Backoffice related",
"Trading Software related",
"API",
"Smart Greek",
"Smart RMS",
"Smart Delta",
"Server related issue",
],
"Technical Support" : ["CPU NOT WORKING",
"KEYBOARD & MOUSE NOT WORKING",
"MONITOR NOT WORKING",
"New System",
"Other Query",
"PRINTER NOT WORKING",
"Provide System",
"Software Installation",
"System Issue",
"System Shifting",
"TechExcel - Backoffice",
"TechExcel API",
"Virtual Server",
"Development/Devops",
],
"Trading related" : ["Auction",
"Corporate Action",
"Pledge",
"Unpledge",
"Limit",
"Penalty & Charges",
"Auction",
"Corporate Action",
"Limit",
"Penalty & Charges",
]
}

def create_fallback_ticket_type():
	if frappe.db.exists(DT, DEFAULT_TICKET_TYPE):
		return

	d = frappe.new_doc(DT)
	d.name = DEFAULT_TICKET_TYPE
	d.is_system = True
	d.save()


def create_ootb_ticket_types():
	for ticket_type in TICKET_TYPES:
		if frappe.db.exists(DT, ticket_type):
			return

		d = frappe.new_doc(DT)
		d.name = ticket_type
		d.is_system = False
		d.save()

def disable_ticket_types():

	hd_parent_ticket_type = frappe.qb.DocType("HD Parent Ticket Type")
	hd_ticket_type = frappe.qb.DocType("HD Ticket Type")
	parent_ticket_types = list(ENABLED_TICKET_TYPES.keys())
	ticket_types = []
	for key,value in ENABLED_TICKET_TYPES.items():
		ticket_types.extend(value)

	query = (
		frappe.qb.from_(hd_parent_ticket_type)
		.select(hd_parent_ticket_type.name)
		.where(hd_parent_ticket_type.name.isin(parent_ticket_types) == False)
	)

	records_to_disable = query.run(as_dict=True)

	if records_to_disable:
		for record in records_to_disable:
			frappe.db.set_value('HD Parent Ticket Type', record['name'], 'disabled', 1)

		# Commit the changes
		frappe.db.commit()
	

	sub_query = (frappe.qb.from_(hd_ticket_type)
		.select(hd_ticket_type.name)
		.where(hd_ticket_type.name.isin(ticket_types) == False))
	
	sub_records_to_disable = sub_query.run(as_dict=True)
	if sub_records_to_disable:
		for record in records_to_disable:
			frappe.db.set_value('HD Ticket Type', record['name'], 'disabled', 1)

		# Commit the changes
		frappe.db.commit()