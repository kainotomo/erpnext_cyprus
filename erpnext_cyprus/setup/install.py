import frappe
from frappe import _
import os
import json
import shutil

def after_install():
    """Add Cyprus Chart of Accounts"""
    
    # Add chart of accounts files to the expected location
    charts_path = frappe.get_app_path("erpnext", "accounts", "doctype", "account", "chart_of_accounts", "verified")
    
    # Copy the chart template to ERPNext's verified folder
    source_path = frappe.get_app_path("erpnext_cyprus", "setup", "chart_of_accounts", "cyprus_chart_template.json")
    target_path = os.path.join(charts_path, "cy_cyprus_chart_template.json")
    
    if os.path.exists(source_path):
        try:
            # Create a backup if the file already exists
            if os.path.exists(target_path):
                backup_path = target_path + ".bak"
                shutil.copy2(target_path, backup_path)
            
            # Copy the template
            with open(source_path, 'r') as source_file:
                chart_data = json.load(source_file)
            
            with open(target_path, 'w') as target_file:
                json.dump(chart_data, target_file, indent=4)
                
            frappe.log_error("Chart template installed successfully", "ERPNext Cyprus Install")
            frappe.msgprint(_("Cyprus Chart of Accounts template has been installed."))
            
        except Exception as e:
            frappe.log_error(f"Error installing chart template: {str(e)}", "ERPNext Cyprus Install Error")
    else:
        frappe.log_error("Source template file not found", "ERPNext Cyprus Install Error")