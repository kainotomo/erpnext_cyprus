import frappe
import re
import requests
from xml.etree import ElementTree as ET

def is_valid_vies_vat(vat_number: str) -> bool:
	"""Check if a VAT number is valid using the VIES web service."""
	if not vat_number or len(vat_number) < 3:
		return False
	country_code = vat_number[:2]
	number = vat_number[2:]
	envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
	<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
		<soapenv:Header/>
		<soapenv:Body>
			<urn:checkVat>
				<urn:countryCode>{country_code}</urn:countryCode>
				<urn:vatNumber>{number}</urn:vatNumber>
			</urn:checkVat>
		</soapenv:Body>
	</soapenv:Envelope>"""
	headers = {'Content-Type': 'text/xml'}
	url = 'https://ec.europa.eu/taxation_customs/vies/services/checkVatService'
	try:
		response = requests.post(url, headers=headers, data=envelope, timeout=10)
		if response.status_code == 200:
			root = ET.fromstring(response.content)
			valid = root.find(".//{urn:ec.europa.eu:taxud:vies:services:checkVat:types}valid")
			return valid is not None and valid.text == "true"
	except Exception:
		pass
	return False

def assign_customer_group_based_on_vat(doc, method=None):
	"""
	Assigns 'Commercial' group if tax_id is a valid VIES VAT number, else 'Individual'.
	Only proceeds if tax_id field is modified (dirty) and not empty.
	"""
	# For new documents, simply check if tax_id exists
	# For existing documents, check if tax_id has changed
	tax_id_changed = True
	if not doc.is_new():
		previous_doc = doc.get_doc_before_save()
		if previous_doc and previous_doc.tax_id == doc.tax_id:
			tax_id_changed = False
	
	# Only proceed if tax_id changed and is not empty
	if not tax_id_changed or not doc.tax_id:
		return
		
	if is_valid_vies_vat(doc.tax_id):
		doc.customer_group = "Commercial"
		doc.customer_type = "Company"
		if frappe.session.user != 'Administrator' and frappe.session.user != 'Guest' and frappe.db.get_value("User", frappe.session.user, "user_type") == "Website User":
			frappe.msgprint("You have entered a valid VAT number!!!")
	else:
		doc.customer_group = "Individual"
		doc.customer_type = "Individual"
		if frappe.session.user != 'Administrator' and frappe.session.user != 'Guest' and frappe.db.get_value("User", frappe.session.user, "user_type") == "Website User":
			frappe.msgprint("Invalid VAT number format. Please check the VAT number and try again.")

def assign_customer_territory_based_on_country(doc, method=None):
	"""
	Assigns territory based on the billing country of the customer.
	"""

	# Get the customer lined to the address
	customer_name = None
	for link in doc.links:
		if link.link_doctype == "Customer":
			customer_name = link.link_name
			break
	if not customer_name:
		return
	
	# Get the customer document
	customer_doc = frappe.get_doc("Customer", customer_name)
	if not customer_doc:
		return

	country = doc.country

	if country:
		if country == "Cyprus":
			customer_doc.territory = "Cyprus"
		elif country in ["Austria", "Belgium", "Bulgaria", "Croatia", "Czech Republic",
			"Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
			"Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
			"Malta", "Netherlands", "Poland", "Portugal", "Romania",
			"Slovakia", "Slovenia", "Spain", "Sweden"]:
			customer_doc.territory = "EU"
		else:
			customer_doc.territory = "Rest Of The World"
	else:
		customer_doc.territory = "Rest Of The World"
	customer_doc.save(ignore_permissions=True)
	frappe.db.commit()
