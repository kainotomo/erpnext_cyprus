import frappe
from frappe.utils import cstr
from erpnext_cyprus.utils.tax_utils import get_eu_vat_rates

def get_customer_billing_country(doc):
    """
    Get the customer's billing country from the address
    """
    if not doc.customer:
        return None
        
    # First try to get the billing address if set
    billing_address = None
    if hasattr(doc, "customer_address") and doc.customer_address:
        billing_address = doc.customer_address
    else:
        # Fall back to the default billing address
        addresses = frappe.get_all(
            "Dynamic Link",
            filters={
                "link_doctype": "Customer",
                "link_name": doc.customer,
                "parenttype": "Address"
            },
            fields=["parent"]
        )
        
        for address in addresses:
            address_doc = frappe.get_doc("Address", address.parent)
            if address_doc.address_type == "Billing" or (not billing_address and address_doc.is_primary_address):
                billing_address = address.parent
                break
    
    if billing_address:
        country = frappe.db.get_value("Address", billing_address, "country")
        return country
    
    return None

def set_oss_vat_rate(doc, method=None):
    """
    Set the VAT OSS rate based on the customer's billing country
    Only applies to sales documents with the Digital Services tax category
    """
    if not (hasattr(doc, "tax_category") and doc.tax_category == "Digital Services" and hasattr(doc, "taxes")):
        return
        
    # Get customer billing country
    country = get_customer_billing_country(doc)
    if not country:
        return
    
    # Skip for Cyprus customers (they use local VAT)
    if country == "Cyprus":
        return
    
    # Get the country's VAT rate
    eu_vat_rates = get_eu_vat_rates()
    rate = eu_vat_rates.get(country, 19)  # Default to 19% if country not found
    
    # Find and update the VAT OSS line
    for tax_row in doc.taxes:
        if hasattr(tax_row, "description") and "VAT OSS" in tax_row.description:
            if tax_row.rate != rate:
                tax_row.rate = rate
                tax_row.description = f"VAT OSS {country} ({rate}%)"
                
                # Log the change for audit purposes
                frappe.msgprint(f"Applied {country} VAT OSS rate: {rate}%")