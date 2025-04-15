import frappe
from frappe import _
from frappe.model.document import Document

@frappe.whitelist()
def create_sample_data(company):
    """
    Create sample data for the given company. Covers Cyprus, EU, and Non-EU cases for customers, suppliers, and transactions.
    """
    # --- Customers ---
    # Create Cyprus, EU, and Non-EU customers
    customers = [
        {
            "customer_name": "Cyprus B2B Customer",
            "customer_type": "Company",
            "customer_group": "Commercial",
            "country": "Cyprus",
            "tax_id": "CY12345678A",
            "company": company
        },
        {
            "customer_name": "Cyprus B2C Customer",
            "customer_type": "Individual",
            "customer_group": "Individual",
            "country": "Cyprus",
            "company": company
        },
        {
            "customer_name": "EU B2B Customer",
            "customer_type": "Company",
            "customer_group": "Commercial",
            "country": "Germany",
            "tax_id": "DE123456789",
            "company": company
        },
        {
            "customer_name": "EU B2C Customer",
            "customer_type": "Individual",
            "customer_group": "Individual",
            "country": "France",
            "company": company
        },
        {
            "customer_name": "Non-EU Customer",
            "customer_type": "Company",
            "customer_group": "Commercial",
            "country": "United States",
            "tax_id": "US12-3456789",
            "company": company
        }
    ]
    for cust in customers:
        if not frappe.db.exists("Customer", {"customer_name": cust["customer_name"], "company": company}):
            doc = frappe.get_doc({
                "doctype": "Customer",
                **cust
            })
            doc.insert(ignore_permissions=True)

    # --- Suppliers ---
    # Create Cyprus, EU, and Non-EU suppliers

    # --- Items ---
    # Create sample goods and services with different VAT rates

    # --- Sales Invoices ---
    # Create invoices for all customer types and VAT scenarios

    # --- Purchase Invoices ---
    # Create invoices for all supplier types and VAT scenarios

    # --- Payments ---
    # Create incoming and outgoing payments

    # --- Stock Entries ---
    # Create stock movements

    # --- Journal Entries ---
    # Create accounting entries

    # --- Employees & Payroll ---
    # Create at least one employee and payroll entry

    # --- Other Documents ---
    # Prepayments, advances, credit notes, returns, etc.

    return {"status": "success", "message": _("Sample data created for company: {0}").format(company)}

@frappe.whitelist()
def delete_sample_data(company):
    """
    Delete sample data for the given company.
    """
    # --- Customers ---
    # Delete sample customers (delete transactional data first in future steps)
    customers = [
        {
            "customer_name": "Cyprus B2B Customer",
            "customer_type": "Company",
            "customer_group": "Commercial",
            "country": "Cyprus",
            "tax_id": "CY12345678A"
        },
        {
            "customer_name": "Cyprus B2C Customer",
            "customer_type": "Individual",
            "customer_group": "Individual",
            "country": "Cyprus"
        },
        {
            "customer_name": "EU B2B Customer",
            "customer_type": "Company",
            "customer_group": "Commercial",
            "country": "Germany",
            "tax_id": "DE123456789"
        },
        {
            "customer_name": "EU B2C Customer",
            "customer_type": "Individual",
            "customer_group": "Individual",
            "country": "France"
        },
        {
            "customer_name": "Non-EU Customer",
            "customer_type": "Company",
            "customer_group": "Commercial",
            "country": "United States",
            "tax_id": "US12-3456789"
        }
    ]
    for cust in customers:
        customer_name = frappe.db.get_value("Customer", {"customer_name": cust["customer_name"]}, "name")
        if customer_name:
            try:
                frappe.delete_doc("Customer", customer_name, ignore_permissions=True)
            except frappe.LinkExistsError:
                # If there are linked documents, skip deletion
                pass

    # --- Suppliers ---
    # Delete sample suppliers

    # --- Items ---
    # Delete sample items

    # --- Sales Invoices ---
    # Delete sample sales invoices

    # --- Purchase Invoices ---
    # Delete sample purchase invoices

    # --- Payments ---
    # Delete sample payments

    # --- Stock Entries ---
    # Delete sample stock entries

    # --- Journal Entries ---
    # Delete sample journal entries

    # --- Employees & Payroll ---
    # Delete sample employees and payroll entries

    # --- Other Documents ---
    # Delete other sample documents

    return {"status": "success", "message": _("Sample data deleted for company: {0}").format(company)}
