import frappe
from frappe import _
from erpnext_cyprus.overrides.company import get_eu_countries

def before_print(doc, method, print_settings=None):
    """Calculate if reverse charge applies before printing"""
    eu_countries = get_eu_countries()
    country = None
    
    if doc.customer_address:
        country = frappe.db.get_value("Address", doc.customer_address, "country")
    
    customer_tax_id = frappe.db.get_value("Customer", doc.customer, "tax_id")
    
    is_reverse_charge = (
        country in eu_countries and 
        country != "Cyprus" and
        customer_tax_id and 
        (doc.total_taxes_and_charges == 0 or not doc.taxes)
    )
    
    # Find and modify the field's metadata to control print behavior
    for field in doc.meta.fields:
        if field.fieldname == "custom_is_reverse_charge":
            # Set print_hide to False if it's a reverse charge, True otherwise
            field.print_hide = not is_reverse_charge
            break