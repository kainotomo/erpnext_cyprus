# VAT Statement Guide for Cyprus

The VAT Statement report in ERPNext Cyprus helps businesses prepare accurate VAT returns according to Cyprus tax regulations. This guide explains how to properly mark transactions to ensure your VAT statement is correct.

## Table of Contents
1. [Setting Up Your Company](#setting-up-your-company)
2. [Customer and Supplier Setup](#customer-and-supplier-setup)
3. [Item Configuration](#item-configuration)
4. [Sales Transactions](#sales-transactions)
5. [Purchase Transactions](#purchase-transactions)
6. [Special Scenarios](#special-scenarios)
7. [VAT Return Boxes Explained](#vat-return-boxes-explained)

## Setting Up Your Company

Before recording transactions, ensure your company is correctly set up:

1. Configure your company's Tax ID with the proper Cyprus format (CY followed by numbers)
2. Set up VAT accounts:
   - Cyprus VAT Output Account (for collecting VAT on sales)
   - Cyprus VAT Input Account (for reclaiming VAT on purchases)

## Customer and Supplier Setup

### Domestic Customers
- Set Tax ID for Cyprus customers with "CY" prefix
- Apply standard Cyprus VAT rates in sales transactions

### EU Customers
- Enter Tax ID with correct country code (e.g., "DE" for Germany)
- For B2B transactions to EU businesses, zero-rate VAT (reverse charge)

### Non-EU Customers
- Enter Tax ID if available
- Zero-rate VAT for exports outside the EU

### Suppliers
- For Cyprus suppliers: Enter Tax ID with "CY" prefix
- For EU suppliers: Enter Tax ID with correct country code
- For non-EU suppliers: Enter Tax ID if available

## Item Configuration

Correctly classify your items as goods or services:

1. Navigate to Item master
2. Enable the "Is Service" custom field:
   - Set to "Yes" for services
   - Set to "No" for physical goods

This distinction is crucial for EU sales and purchases reporting (Boxes 8A/8B and 11A/11B).

## Sales Transactions

### Domestic Sales
- Apply standard Cyprus VAT rates
- System will automatically calculate Box 1 (VAT due on sales)

### EU Sales
- For B2B transactions to VAT-registered EU businesses:
  - Verify the customer has a valid EU Tax ID
  - Zero-rate the invoice (no VAT)
  - These will appear in Box 8A (goods) or 8B (services)

### Exports Outside EU
- Zero-rate the invoice
- These will be reported in Box 9

### Out-of-Scope Sales
- For transactions outside the scope of VAT but eligible for input tax deduction
- Zero-rate the invoice
- These will be reported in Box 10

## Purchase Transactions

### Domestic Purchases
- Include VAT as charged by supplier
- System will automatically include in Box 4 (VAT reclaimed)

### EU Purchases (Reverse Charge)
- Record the purchase without VAT
- Create a reverse charge entry to account for both output VAT (Box 2) and input VAT (Box 4)
- These will appear in Box 11A (goods) or 11B (services)

### Imports from Outside EU
- Record import VAT paid
- These will be included in Box 4 (VAT reclaimed)

## Special Scenarios

### Reverse Charge Mechanism
For EU purchases subject to reverse charge:
1. Create a purchase invoice with zero VAT
2. Create a journal entry to:
   - Debit the VAT Input Account
   - Credit the VAT Output Account
   - Use the same amount for both

### Partial Exemption
If your business has exempt activities:
- Consult with your accountant about partial exemption calculations
- Adjust Box 4 (VAT reclaimed) accordingly

## VAT Return Boxes Explained

The system automatically calculates these values based on your transactions:

- **Box 1**: VAT due on sales and other outputs
- **Box 2**: VAT due on acquisitions from other EU Member States
- **Box 3**: Total VAT due (Box 1 + Box 2)
- **Box 4**: VAT reclaimed on purchases and inputs
- **Box 5**: Net VAT payable or reclaimable (Box 3 - Box 4)
- **Box 6**: Total value of sales excluding VAT
- **Box 7**: Total value of purchases excluding VAT
- **Box 8A**: Value of goods supplied to EU Member States
- **Box 8B**: Value of services supplied to EU Member States
- **Box 9**: Value of zero-rated supplies (exports outside EU)
- **Box 10**: Value of out-of-scope sales with right to deduct input tax
- **Box 11A**: Value of goods acquired from EU Member States
- **Box 11B**: Value of services received from anywhere

By following these guidelines, your VAT statement report will accurately reflect your business transactions according to Cyprus tax regulations.
