The Hellenic Bank integration in ERPNext Cyprus allows businesses to connect directly with their Hellenic Bank accounts to automate banking operations such as retrieving transactions and making payments. This guide explains how to set up and use the Hellenic Bank integration features.

## Table of Contents
1. Overview
2. Prerequisites
3. Initial Setup
4. Authentication
5. Bank Account Configuration
6. Retrieving Bank Transactions
7. Making Wire Transfers
8. Troubleshooting

## Overview

The Hellenic Bank integration provides these key features:
- Secure OAuth2 authentication with Hellenic Bank APIs
- Automatic retrieval of bank accounts
- Downloading bank transactions
- Executing wire transfers to other bank accounts
- Checking funds availability before payment

## Prerequisites

Before setting up the integration, you need:
- A Hellenic Bank business account with online banking access
- API credentials from Hellenic Bank (client ID and client secret)
- Proper authorization to access the Hellenic Bank API services
- ERPNext Cyprus module installed on your ERPNext instance

## Initial Setup

1. Navigate to **Hellenic Bank** list and create a new record:
   - Enter a meaningful **Title** for this connection
   - Set the **Bank** field to your Hellenic Bank entity 
   - Enter the **Parent Account** where bank accounts will be created in your Chart of Accounts
   - Toggle **Allow Payments** if you need to make outgoing payments
   - Enable **Is Sandbox** if you're testing with Hellenic Bank's sandbox environment

2. Enter your API credentials:
   - **Client ID**: The client ID provided by Hellenic Bank
   - **Client Secret**: The client secret provided by Hellenic Bank

3. Save the configuration

## Authentication

Once you've saved the initial configuration, you need to authenticate with Hellenic Bank:

1. Click the **Connect to [Bank Name]** button on the Hellenic Bank doctype
2. A new browser window will open with the Hellenic Bank authentication page
3. Log in with your Hellenic Bank credentials
4. Authorize the application to access your account data
5. After successful authorization, you'll be redirected back to ERPNext
6. The system will display a success message when the authorization is complete
7. The **Token Status** field will show a green success message when properly connected

## Bank Account Configuration

After successful authorization, you can automatically create bank accounts:

1. Click the **Create Accounts** button on the Hellenic Bank doctype
2. Confirm the action when prompted
3. The system will:
   - Retrieve all available accounts from Hellenic Bank
   - Create corresponding accounts in your Chart of Accounts
   - Set up Bank Account records with proper IBAN and account details
4. A success message will appear when accounts are created

## Retrieving Bank Transactions

You can retrieve bank transactions in two ways:

### Via Bank Reconciliation Tool

1. Navigate to **Accounting > Banking and Payments > Bank Reconciliation Tool**
2. Select the Hellenic Bank account you want to work with
3. Enter the date range for transactions
4. Click **Retrieve Bank Transactions** under the "Hellenic Bank" menu
5. Transactions will be downloaded and added to the reconciliation tool
6. You can then match and reconcile transactions as usual

### Via Bank Account

1. Open the Bank Account that's linked to your Hellenic Bank account
2. Navigate to the "Get Statements" section
3. Specify the date range
4. Click "Get Statement"
5. The system will retrieve the transactions from Hellenic Bank

## Making Wire Transfers

To make wire transfers (payments) to other bank accounts:

1. Create a new Payment Entry
2. Set the **Payment Type** to "Pay"
3. Select your Hellenic Bank account as the **Bank Account**
4. Select the recipient's bank account as the **Party Bank Account**
5. Enter the payment amount, reference number, and reference date
6. Save the Payment Entry
7. Click **Wire Transfer** in the Hellenic Bank section
8. The system will:
   - Check if sufficient funds are available 
   - Execute the payment through the Hellenic Bank API
   - Display a success message when the payment is processed

## Troubleshooting

Common issues and solutions:

1. **Authorization Failed**:
   - Check if your client ID and client secret are correct
   - Ensure your Hellenic Bank account has API access enabled
   - Try reconnecting by clicking the "Connect" button again

2. **Token Expired**:
   - The system should automatically refresh tokens, but if issues persist
   - Disconnect and reconnect to get a new authorization token

3. **Transaction Retrieval Errors**:
   - Verify the date range is valid (not in the future)
   - Check if your authorization is still valid
   - Ensure the IBAN is correctly configured in the Bank Account

4. **Payment Errors**:
   - Verify sufficient funds are available in the account
   - Check that all required payment details are provided
   - Ensure the beneficiary IBAN is valid and correctly formatted

For persistent issues, check the Hellenic Bank API documentation or contact your bank representative.