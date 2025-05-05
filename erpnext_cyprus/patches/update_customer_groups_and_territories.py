import frappe
from erpnext_cyprus.utils.customer_group_assignment import assign_customer_territory_based_on_country

def execute():
    """
    Run assignment methods for all customers and their addresses
    """
    print("\n=== Starting Customer Group and Territory Assignment ===\n")
    
    # Process all customers for VAT group assignment
    customers = frappe.get_all("Customer", filters={"customer_name": ["!=", ""]}, fields=["name"])
    count = 0
    total = len(customers)
    
    print(f"Processing {total} customers for group assignment...")
    frappe.log_error(f"Starting customer group assignment for {total} customers")
    
    for customer in customers:
        try:
            customer_doc = frappe.get_doc("Customer", customer.name)
            assign_customer_group_based_on_vat(customer_doc)
            customer_doc.save(ignore_permissions=True)
            
            count += 1                
            if count % 100 == 0:
                frappe.db.commit()
                print(f"Processed {count}/{total} customers ({int(count*100/total)}%)")
                frappe.log_error(f"Processed {count}/{total} customers")
        except Exception as e:
            print(f"Error processing customer {customer.name}: {str(e)}")
            frappe.log_error(f"Error processing customer {customer.name}: {str(e)}")
    
    frappe.db.commit()
    print(f"\n✓ Completed customer group assignment for {total} customers\n")
    frappe.log_error(f"Completed customer group assignment for {total} customers")
    
    # Process all customer addresses for territory assignment
    addresses = frappe.get_all(
        "Address", 
        filters=[["Dynamic Link", "link_doctype", "=", "Customer"]],
        fields=["name"]
    )
    
    count = 0
    total = len(addresses)
    
    print(f"Processing {total} addresses for territory assignment...")
    frappe.log_error(f"Starting territory assignment for {total} addresses")
    
    for address in addresses:
        try:
            address_doc = frappe.get_doc("Address", address.name)
            assign_customer_territory_based_on_country(address_doc)
            
            count += 1
            if count % 100 == 0:
                frappe.db.commit()
                print(f"Processed {count}/{total} addresses ({int(count*100/total)}%)")
                frappe.log_error(f"Processed {count}/{total} addresses")
        except Exception as e:
            print(f"Error processing address {address.name}: {str(e)}")
            frappe.log_error(f"Error processing address {address.name}: {str(e)}")
    
    frappe.db.commit()
    print(f"\n✓ Completed territory assignment for {total} addresses")
    print("\n=== Finished Customer Group and Territory Assignment ===\n")
    frappe.log_error(f"Completed territory assignment for {total} addresses")

def assign_customer_group_based_on_vat(doc, method=None):
    """
    Assigns 'Commercial' group if tax_id is a valid VIES VAT number, else 'Individual'.
    Only proceeds if tax_id field is modified (dirty) and not empty.
    """
        
    if doc.tax_id and doc.tax_id != "":
        doc.customer_group = "Commercial"
        doc.customer_type = "Company"
    else:
        doc.customer_group = "Individual"
        doc.customer_type = "Individual"