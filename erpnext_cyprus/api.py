import frappe
from frappe import _
from frappe.utils import cstr
from erpnext_cyprus.utils.account_utils import setup_cyprus_accounts
from erpnext_cyprus.utils.tax_utils import setup_cyprus_tax_categories

@frappe.whitelist()
def setup_cyprus_company(company):
    """
    Set up Cyprus-specific configuration for a company
    """
    if not frappe.has_permission("Company", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    company_doc = frappe.get_doc("Company", company)
    if company_doc.country != "Cyprus":
        frappe.throw(_("This function is only available for Cyprus-based companies"))
    
    # Setup chart of accounts - this already has checks for existing accounts
    accounts_created = setup_cyprus_accounts(company)
    
    # Setup tax categories - this already has checks for existing categories
    tax_categories_created = setup_cyprus_tax_categories()
    
    return {
        "message": _("Cyprus company setup completed successfully"),
        "accounts_added": accounts_created,
        "tax_categories_added": tax_categories_created
    }