import frappe
import os
import shutil

def before_uninstall():
    """Remove Cyprus Chart of Accounts template file on app uninstallation"""
    try:
        # Path to the chart template in ERPNext
        charts_path = frappe.get_app_path("erpnext", "accounts", "doctype", "account", "chart_of_accounts", "verified")
        target_path = os.path.join(charts_path, "cy_cyprus_chart_template.json")
        
        # Check if file exists and remove it
        if os.path.exists(target_path):
            os.remove(target_path)
            frappe.log_error("Chart template removed during uninstallation", "ERPNext Cyprus Uninstall")
    except Exception as e:
        frappe.log_error(f"Error removing chart template: {str(e)}", "ERPNext Cyprus Uninstall Error")