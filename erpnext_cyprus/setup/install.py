import frappe
from frappe import _
import os
import json
import shutil

def after_install():
    """Add Cyprus Chart of Accounts"""
    
    # Add chart of accounts files to the expected location
    charts_path = frappe.get_app_path("erpnext", "accounts", "doctype", "account", "chart_of_accounts", "verified")
    
    # Define source and target paths for both chart templates
    templates = [
        {
            "source": frappe.get_app_path("erpnext_cyprus", "setup", "chart_of_accounts", "cyprus_chart_template.json"),
            "target": os.path.join(charts_path, "cy_cyprus_chart_template.json"),
            "name": "Cyprus Standard"
        },
        {
            "source": frappe.get_app_path("erpnext_cyprus", "setup", "chart_of_accounts", "cyprus_chart_template_numbered.json"),
            "target": os.path.join(charts_path, "cy_cyprus_chart_template_numbered.json"),
            "name": "Cyprus Standard Numbered"
        }
    ]
    
    # Copy each template to ERPNext's verified folder
    for template in templates:
        if os.path.exists(template["source"]):
            try:
                # Create a backup if the file already exists
                if os.path.exists(template["target"]):
                    backup_path = template["target"] + ".bak"
                    shutil.copy2(template["target"], backup_path)
                
                # Copy the template
                with open(template["source"], 'r') as source_file:
                    chart_data = json.load(source_file)
                
                with open(template["target"], 'w') as target_file:
                    json.dump(chart_data, target_file, indent=4)
                    
                frappe.log_error(f"{template['name']} chart template installed successfully", "ERPNext Cyprus Install")
                
            except Exception as e:
                frappe.log_error(f"Error installing {template['name']} chart template: {str(e)}", "ERPNext Cyprus Install Error")
        else:
            frappe.log_error(f"Source template file not found: {template['source']}", "ERPNext Cyprus Install Error")
    
    frappe.msgprint(_("Cyprus Chart of Accounts templates have been installed."))