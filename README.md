# ShopFlow — Demo Target App for SENTINEL

ShopFlow is a fake e-commerce app intentionally broken to demonstrate SENTINEL's
Persistent Context Engine at Anvil 2026.

---

## The Bug Story

| Version | What Happened | Incident |
|---------|---------------|----------|
| v1.0 | `process()` endpoint: DB connection created per-request, never closed | INC-001 |
| v1.1 | Engineer added `try/finally` close — incident "resolved" — but root cause remains | — |
| v1.2 | New engineer copied same bad pattern into `refund()` endpoint | INC-002 |

**SENTINEL detects**: DNA(INC-001) ≈ DNA(INC-002) with **0.94 cosine similarity**.
Root cause: identical — no database connection pooling.

---

## Quick Start

```bash
# Option 1: Start everything at once
start.bat

# Option 2: Manual
cd payment-service && pip install -r requirements.txt && python main.py
cd storefront && npm install && npm run dev
```

**URLs**:
- Storefront: http://localhost:3001
- Payment API: http://localhost:8001
- Payment Docs: http://localhost:8001/docs

---

## Trigger the Bug (Live Demo)

```bash
cd payment-service

# Trigger payment bug (INC-001 pattern)
python simulate_load.py --users 10

# Trigger refund bug (INC-002 — same DNA as INC-001)
python simulate_load.py --users 10 --refund

# Fastest pool exhaustion (mix both)
python simulate_load.py --users 15 --mixed

# Reset between demo runs
python simulate_load.py --reset
```

---

## Demo Flow for Judges

1. Open storefront at http://localhost:3001
2. Browse products → Add to Cart → Checkout
3. Run `simulate_load.py --users 10 --mixed` in a terminal
4. Watch checkout button show **red error toast** (visible to judges)
5. Switch to SENTINEL dashboard (port 3000) — incident card appears automatically
6. SENTINEL shows **INC-002 matches INC-001 via DNA fingerprinting (94% similarity)**
7. Click "Mark Resolved" — SENTINEL learns from the fix

---

## File Structure

```
dummy-app/
├── payment-service/
│   ├── main.py              # FastAPI v1.2 (buggy refund endpoint)
│   ├── simulate_load.py     # Concurrent load trigger
│   ├── event_emitter.py     # Bridge to SENTINEL /api/v1/ingest
│   ├── requirements.txt
│   ├── .env
│   └── versions/
│       ├── v1_0_buggy.py    # Original bug (reference)
│       ├── v1_1_bad_fix.py  # Band-aid fix (reference)
│       └── v1_2_new_bug.py  # New refund bug (reference)
│
├── storefront/
│   ├── app/
│   │   ├── page.tsx         # Product listing (3 plans)
│   │   ├── cart/page.tsx    # Cart + Checkout + Error toast
│   │   └── orders/page.tsx  # Order history + Refund button
│   └── components/
│       └── Navbar.tsx
│
├── start.bat                # Launch everything
└── README.md
```

---

## Environment Variables

**payment-service/.env**
```
ENGINE_INGEST_URL=http://localhost:8000/api/v1/ingest
SERVICE_NAME=payment-service
SERVICE_VERSION=v1.2
PORT=8001
```

**storefront/.env.local**
```
NEXT_PUBLIC_PAYMENT_API=http://localhost:8001
NEXT_PUBLIC_SENTINEL_API=http://localhost:8000
```

---

*Built for Anvil 2026 · RootedMinds · Problem Statement 02*
