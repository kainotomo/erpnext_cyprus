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
    """
    if doc.tax_id and is_valid_vies_vat(doc.tax_id):
        doc.customer_group = "Commercial"
        doc.customer_type = "Company"
    else:
        doc.customer_group = "Individual"
        doc.customer_type = "Individual"
