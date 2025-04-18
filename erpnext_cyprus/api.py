import frappe
from frappe import _
from frappe.utils import cstr
from erpnext_cyprus.utils.account_utils import setup_cyprus_accounts
from erpnext_cyprus.utils.tax_utils import (
    setup_cyprus_tax_categories,
    setup_cyprus_purchase_tax_templates
)

@frappe.whitelist()
def setup_cyprus_company(company):
    """
    Set up Cyprus-specific configuration for a company
    """
    frappe.msgprint(_("Starting Cyprus company setup for: {0}").format(company))
    
    if not frappe.has_permission("Company", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    company_doc = frappe.get_doc("Company", company)
    if company_doc.country != "Cyprus":
        frappe.throw(_("This function is only available for Cyprus-based companies"))
    
    results = {
        "message": _("Cyprus company setup completed"),
        "accounts_added": [],
        "tax_categories_added": [],
        "purchase_templates_added": []
    }
    
    # Step 1: Setup chart of accounts
    frappe.msgprint(_("Step 1: Setting up chart of accounts"))
    accounts_created = setup_cyprus_accounts(company)
    results["accounts_added"] = accounts_created
    frappe.msgprint(_("Chart of accounts setup completed. Created: {0}").format(
        ", ".join(accounts_created) if accounts_created else "None"))
    
    # Commit changes before proceeding to ensure accounts are saved
    frappe.db.commit()
    
    # Step 2: Setup tax categories
    frappe.msgprint(_("Step 2: Setting up tax categories"))
    tax_categories_created = setup_cyprus_tax_categories()
    results["tax_categories_added"] = tax_categories_created
    frappe.msgprint(_("Tax categories setup completed. Created: {0}").format(
        ", ".join(tax_categories_created) if tax_categories_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 3: Setup purchase tax templates
    frappe.msgprint(_("Step 3: Setting up purchase tax templates"))
    purchase_templates_created = setup_cyprus_purchase_tax_templates(company)
    results["purchase_templates_added"] = purchase_templates_created
    frappe.msgprint(_("Purchase tax templates setup completed. Created: {0}").format(
        ", ".join(purchase_templates_created) if purchase_templates_created else "None"))
    
    return results