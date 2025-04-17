import frappe
from frappe import _
from frappe.utils import cstr
from erpnext_cyprus.utils.account_utils import setup_cyprus_accounts

@frappe.whitelist()
def setup_cyprus_chart_of_accounts(company):
    """
    Set up Cyprus-specific accounts in the company's chart of accounts
    """
    if not frappe.has_permission("Company", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    company_doc = frappe.get_doc("Company", company)
    if company_doc.country != "Cyprus":
        frappe.throw(_("This function is only available for Cyprus-based companies"))
    
    results = setup_cyprus_accounts(company)
    
    return {
        "message": _("Chart of Accounts extended with Cyprus-specific accounts"),
        "accounts_added": results
    }