import asyncio
import os
from datetime import datetime, timedelta
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def upsert_offer(conn, card_name: str, merchant_name: str, deal: dict):
    card = await conn.fetchrow("SELECT id FROM cards WHERE card_name ILIKE $1", f"%{card_name}%")
    merchant = await conn.fetchrow("SELECT id FROM merchants WHERE name ILIKE $1", f"%{merchant_name}%")

    if not card or not merchant:
        print(f"[-] Skipped: {card_name} or {merchant_name} not found.")
        return

    valid_until = deal.get("valid_until") or (datetime.now() + timedelta(days=60)).date()

    await conn.execute("""
        INSERT INTO offers (card_id, merchant_id, discount_type, discount_value, min_spend, max_cap, promo_code, valid_until)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, card["id"], merchant["id"], deal["discount_type"], deal["discount_value"], deal.get("min_spend", 0.0), deal.get("max_cap"), deal.get("promo_code"), valid_until)

    print(f"[+] Added offer: {card_name} on {merchant_name}")

async def run():
    ssl_mode = "require" if "localhost" not in (DATABASE_URL or "") else None
    conn = await asyncpg.connect(DATABASE_URL, ssl=ssl_mode)

    sample_deals = [
        {"card": "Axis Airtel", "merchant": "Zomato", "discount_type": "PERCENTAGE", "discount_value": 10.0, "min_spend": 300.0, "max_cap": 100.0, "promo_code": "AXISZOM"},
        {"card": "ICICI Amazon Pay", "merchant": "Amazon", "discount_type": "PERCENTAGE", "discount_value": 5.0, "min_spend": 0.0, "max_cap": None, "promo_code": None},
        {"card": "HDFC Millennia", "merchant": "Blinkit", "discount_type": "PERCENTAGE", "discount_value": 5.0, "min_spend": 500.0, "max_cap": 75.0, "promo_code": "HDFCBK"}
    ]

    for deal in sample_deals:
        await upsert_offer(conn, deal["card"], deal["merchant"], deal)

    await conn.close()

if __name__ == "__main__":
    asyncio.run(run())