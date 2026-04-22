# Nivesh.ai (FD-backed Loan Readiness Engine)

This project is for **instant FD-backed loan pre-qualification**.  
User gives profile + FD details, and API returns:

- readiness score
- decision (`pre_qualified` / `conditionally_ready` / `improve_then_apply`)
- eligible loan range
- LTV applied, EMI estimate, explanation, and suggested route

It also has a simulation endpoint to answer:  
**"If I add one more FD, how much more loan eligibility can I unlock?"**

---

## What this backend does

At a high level, this backend converts raw borrower + FD data into an underwriter-style decision in milliseconds.

1. Validates request data with strong Pydantic schemas.
2. Resolves FD interest rate (user input or Blostem live rate).
3. Applies haircut + lock-factor logic to compute usable collateral.
4. Scores collateral, cashflow, tenure quality, and KYC readiness.
5. Converts score to LTV, loan range, rate band, and recommendation.
6. Returns transparent reasoning (breakdown + route options).

---

## Architecture (current)

```text
┌───────────────┐
│     User      │
└───────┬───────┘
        │
        ▼
┌──────────────────────────────────────────────┐
│ Frontend  │
│ - Collects profile + FD details             │
│ - Triggers pre-check and what-if simulation │
└───────────────────┬──────────────────────────┘
                    │ HTTPS JSON Request/Response
                    ▼
┌──────────────────────────────────────────────┐
│ Backend Loan Engine                │
│ - Input validation                           │
│ - Scoring + eligibility computation          │
│ - Recommendation and explanation generation  │
└───────────────┬───────────────────┬──────────┘
                │                   │
                │ Live rate lookup  │ Fallback rate logic
                ▼                   ▼
      ┌───────────────────┐   ┌─────────────────────────┐
      │ Blostem Rate API  │   │ Internal default rates  │
      └─────────┬─────────┘   └─────────────┬───────────┘
                └───────────────┬───────────┘
                                ▼
                  ┌──────────────────────────┐
                  │ Final decision payload   │
                  │ score + range + route    │
                  └──────────────┬───────────┘
                                 │
                                 ▼
                  ┌──────────────────────────┐
                  │ Frontend Result Panel    │
                  │ breakdown + simulation   │
                  └──────────────────────────┘
```

---

## How Blostem powers this

Blostem is the **rate intelligence layer** of this backend.

When a request includes `bank_slug` and `BLOSTEM_API_KEY` is configured:

1. Backend calls `POST {BLOSTEM_API_BASE}/fd-rates/calculate`
2. Sends FD context (principal, tenure, bank slug, depositor type)
3. Uses Blostem's `rateUsed` in collateral + eligibility calculations
4. Marks response mode as `blostem_live`

If Blostem call is not possible (missing key/slug, timeout, or HTTP error), backend gracefully falls back to internal institution-wise defaults and marks mode as `mock_or_fallback`.

So, Blostem gives this product **live-market realism**, while fallback ensures **high availability**.

---

```
