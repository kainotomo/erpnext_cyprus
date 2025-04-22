import frappe
from frappe import _
from frappe.utils import cstr
from erpnext_cyprus.utils.account_utils import setup_cyprus_accounts
from erpnext_cyprus.utils.tax_utils import (
    setup_cyprus_purchase_tax_templates,
    setup_cyprus_sales_tax_templates,
    setup_cyprus_item_tax_templates,
    setup_cyprus_tax_rules,
    setup_cyprus_item_groups
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
        "item_groups_added": [],
        "purchase_templates_added": [],
        "sales_templates_added": [],
        "item_tax_templates_added": [],
        "tax_rules_added": []
    }
    
    # Step 1: Setup chart of accounts
    frappe.msgprint(_("Step 1: Setting up chart of accounts"))
    accounts_created = setup_cyprus_accounts(company)
    results["accounts_added"] = accounts_created
    frappe.msgprint(_("Chart of accounts setup completed. Created: {0}").format(
        ", ".join(accounts_created) if accounts_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 2: Setup required item groups (formerly Step 3)
    frappe.msgprint(_("Step 2: Setting up required item groups"))
    item_groups_created = setup_cyprus_item_groups()
    results["item_groups_added"] = item_groups_created
    frappe.msgprint(_("Item groups setup completed. Created: {0}").format(
        ", ".join(item_groups_created) if item_groups_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 3: Setup purchase tax templates (formerly Step 4)
    frappe.msgprint(_("Step 3: Setting up purchase tax templates"))
    purchase_templates_created = setup_cyprus_purchase_tax_templates(company)
    results["purchase_templates_added"] = purchase_templates_created
    frappe.msgprint(_("Purchase tax templates setup completed. Created: {0}").format(
        ", ".join(purchase_templates_created) if purchase_templates_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 4: Setup sales tax templates (formerly Step 5)
    frappe.msgprint(_("Step 4: Setting up sales tax templates"))
    sales_templates_created = setup_cyprus_sales_tax_templates(company)
    results["sales_templates_added"] = sales_templates_created
    frappe.msgprint(_("Sales tax templates setup completed. Created: {0}").format(
        ", ".join(sales_templates_created) if sales_templates_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 5: Setup item tax templates (formerly Step 6)
    frappe.msgprint(_("Step 5: Setting up item tax templates"))
    item_templates_created = setup_cyprus_item_tax_templates(company)
    results["item_tax_templates_added"] = item_templates_created
    frappe.msgprint(_("Item tax templates setup completed. Created: {0}").format(
        ", ".join(item_templates_created) if item_templates_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 6: Setup tax rules (formerly Step 7)
    frappe.msgprint(_("Step 6: Setting up tax rules"))
    tax_rules_created = setup_cyprus_tax_rules(company)
    results["tax_rules_added"] = tax_rules_created
    frappe.msgprint(_("Tax rules setup completed. Created: {0}").format(
        ", ".join(tax_rules_created) if tax_rules_created else "None"))
    
    return results