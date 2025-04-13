import frappe
import os
import shutil

def before_uninstall():
    """Remove Cyprus Chart of Accounts template files on app uninstallation"""
    try:
        # Path to the chart templates in ERPNext
        charts_path = frappe.get_app_path("erpnext", "accounts", "doctype", "account", "chart_of_accounts", "verified")
        
        # Templates to remove
        templates = [
            {
                "path": os.path.join(charts_path, "cy_cyprus_chart_template.json"),
                "name": "Cyprus Standard"
            },
            {
                "path": os.path.join(charts_path, "cy_cyprus_chart_template_numbered.json"),
                "name": "Cyprus Standard Numbered"
            }
        ]
        
        # Check if files exist and remove them
        for template in templates:
            if os.path.exists(template["path"]):
                os.remove(template["path"])
                frappe.log_error(f"{template['name']} chart template removed during uninstallation", "ERPNext Cyprus Uninstall")
                
                # Also remove any backup files
                backup_path = template["path"] + ".bak"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
    except Exception as e:
        frappe.log_error(f"Error removing chart templates: {str(e)}", "ERPNext Cyprus Uninstall Error")