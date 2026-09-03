import os
from dotenv import load_dotenv

load_dotenv()  # Reads from your local .env file
from contextlib import asynccontextmanager
from typing import List, Optional
import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://devuser:devpassword@localhost:5432/discount_engine"
)

pool: Optional[asyncpg.Pool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    yield
    if pool:
        await pool.close()

app = FastAPI(title="Slashh Discount Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CalculateRequest(BaseModel):
    merchant_id: int
    spend_amount: float
    held_card_ids: List[int]

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Slashh Discount API is live", "docs": "/docs"}

@app.get("/api/v1/meta")
async def get_metadata():
    if not pool:
        raise HTTPException(status_code=500, detail="Database uninitialized")
    async with pool.acquire() as conn:
        merchants = await conn.fetch("SELECT id, name, category FROM merchants ORDER BY name ASC")
        cards = await conn.fetch("SELECT id, card_name, bank_id FROM cards ORDER BY card_name ASC")
        return {
            "merchants": [dict(m) for m in merchants],
            "cards": [dict(c) for c in cards]
        }

@app.post("/api/v1/discounts/calculate")
async def calculate_discount(req: CalculateRequest):
    if not pool:
        raise HTTPException(status_code=500, detail="Database uninitialized")

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT o.id, o.card_id, c.card_name, c.affiliate_apply_url,
                   o.discount_type, o.discount_value, o.min_spend, o.max_cap, o.promo_code
            FROM offers o
            JOIN cards c ON o.card_id = c.id
            WHERE o.merchant_id = $1 
              AND o.min_spend <= $2
              AND (o.valid_until IS NULL OR o.valid_until >= CURRENT_DATE)
            """,
            req.merchant_id, req.spend_amount
        )

    if not rows:
        return {"best_held_card": None, "missed_opportunity": None}

    evaluated = []
    for r in rows:
        if r["discount_type"] == "PERCENTAGE":
            calc = (req.spend_amount * float(r["discount_value"])) / 100.0
            savings = min(calc, float(r["max_cap"])) if r["max_cap"] is not None else calc
        else:
            savings = float(r["discount_value"])

        evaluated.append({
            "card_id": r["card_id"],
            "card_name": r["card_name"],
            "promo_code": r["promo_code"],
            "savings": round(savings, 2),
            "affiliate_url": r["affiliate_apply_url"],
            "is_held": r["card_id"] in req.held_card_ids
        })

    held_offers = [o for o in evaluated if o["is_held"]]
    best_held = max(held_offers, key=lambda x: x["savings"]) if held_offers else None
    best_overall = max(evaluated, key=lambda x: x["savings"]) if evaluated else None

    missed_opp = None
    held_savings = best_held["savings"] if best_held else 0.0
    if best_overall and (not best_overall["is_held"]) and (best_overall["savings"] > held_savings):
        missed_opp = {
            "card_name": best_overall["card_name"],
            "potential_savings": best_overall["savings"],
            "difference": round(best_overall["savings"] - held_savings, 2),
            "apply_url": best_overall["affiliate_url"]
        }

    return {
        "best_held_card": best_held,
        "missed_opportunity": missed_opp
    }