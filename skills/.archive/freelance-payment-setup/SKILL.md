---
name: freelance-payment-setup
description: Procedures for configuring international payment gateways and banking for freelancers (Upwork, Wise, Payoneer, Digital Banks). Focuses on minimizing conversion spreads and maximizing net take-home pay.
---

# Freelance Payment Setup

This skill governs the configuration of payment pipelines from international platforms (like Upwork) to local currency (BRL/USD). The primary goal is to avoid "hidden" fees from platform-native conversion and high bank spreads.

## Core Strategy: The "USD-First" Pipeline
Avoid converting currency inside the freelancing platform. Most platforms apply a spread of 2-5% above the mid-market rate.
**Optimal Path:** `Freelance Platform` $\rightarrow$ `Digital USD Account (Wise/Payoneer)` $\rightarrow$ `Câmbio Real` $\rightarrow$ `Local Bank (via PIX/TED)`.

## Upwork $\rightarrow$ Wise Configuration (The Gold Standard)

This is the most cost-effective method for freelancers in Brazil.

### 1. Wise Side: USD Account Details
You must have an active USD Balance with account details.
- **Path:** Home $\rightarrow$ Balances $\rightarrow$ USD $\rightarrow$ "Get account details".
- **Required Data:**
    - **ACH Routing Number:** (Usually ends in 3150, 9519, or 9628).
    - **Account Number:** Unique to your balance.
    - **Account Type:** Checking.

### 2. Upwork Side: Payment Method
**Settings $\rightarrow$ Get Paid $\rightarrow$ Add Payment Method $\rightarrow$ Direct to US Bank (USD)**.
- **Routing Number:** Enter the Wise ACH Routing.
- **Account Number:** Enter the Wise Account Number.
- **Account Holder Name:** Must exactly match the name on the Wise account.

### 3. Verification: Micro-deposits
Upwork verifies ownership via small deposits.
- **Wait:** 1–3 business days for 2 micro-deposits (cents) to appear in the Wise USD balance.
- **Confirm:** Go to **Settings $\rightarrow$ Get Paid** and enter the exact amounts received.

## Common Pitfalls & Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| **Bank not found** | Upwork cannot resolve the bank branch via routing. | Select "Enter branch address manually" and provide the Wise USD bank address. |
| **High Fees** | Using "Direct to Local Bank (BRL)". | Switch to "Direct to US Bank (USD)" to move the conversion to Wise. |
| **Funds Frozen** | Name mismatch between Upwork and Wise. | Ensure both accounts use the same legal name (no nicknames). |
| **Micro-deposits not appearing** | Wrong routing number (Wire vs ACH). | Ensure you are using the **ACH** routing number, not the Wire routing number. |

## Comparison Matrix: Withdrawal Methods

| Method | Conversion Rate | Speed | Cost | Notes |
|---|---|---|---|---|
| **Wise (USD Account)** | Mid-market (Best) | Fast | Low (Wise fee only) | **Gold Standard** for Brazil. $0 Upwork fee. |
| **Revolut (Brazil)** | Commercial | Slow | High ($30/saque) | No ACH routing. Only SWIFT/Wire. |
| **Direct to Local Bank (BRL)** | Platform Spread (Poor) | Medium | $0.99 fixed fee | High loss on exchange rate. |
| **PayPal** | Poor | Fast | High (Fee + Spread) | Avoid for large sums. |
| **Payoneer** | Medium | Medium | Medium | Alternative for business accounts. |

## Decision Logic: Which to use?
- **Low Volume (< $100):** Direct to Local Bank (BRL) may be simpler, but still more expensive.
- **High Volume / Long Term:** **Wise (USD)** is mandatory to avoid losing hundreds of dollars in spread over a year.
- **Revolut (Brazil):** Use only for travel spending/card usage. Avoid as a primary Upwork withdrawal method due to lack of ACH routing and high Wire fees.
- **Corporate/Legal Entity (PJ):** Use Wise Business for easier accounting and tax compliance.
